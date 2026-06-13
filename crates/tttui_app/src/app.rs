use std::collections::BTreeMap;
use std::io;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};

use crossterm::event::{
    self, Event, KeyCode, KeyEvent, KeyEventKind, KeyModifiers, KeyboardEnhancementFlags,
    PopKeyboardEnhancementFlags, PushKeyboardEnhancementFlags,
};
use crossterm::execute;
use crossterm::terminal::{
    disable_raw_mode, enable_raw_mode, supports_keyboard_enhancement, EnterAlternateScreen,
    LeaveAlternateScreen,
};
use ratatui::backend::CrosstermBackend;
use ratatui::layout::{Alignment, Constraint, Direction, Layout, Rect};
use ratatui::style::{Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Borders, Clear, Paragraph};
use ratatui::{Frame, Terminal};
use tttui_core::{AppError, AppResult};

use crate::config::app_config::{AppConfig, PersonalBest, SessionHistoryEntry};
use crate::config::app_paths::config_dir;
use crate::features::preferences::application::ports::PreferencesRepository;
use crate::features::preferences::domain::keybinding::{KeyMap, KeySequenceMatcher};
use crate::features::preferences::domain::theme::{ResolvedTheme, ThemeDefinition};
use crate::features::preferences::infrastructure::file_preferences_repository::FilePreferencesRepository;
use crate::features::session_history::presentation::render::render_history;
use crate::features::typing_test::application::ports::ContentRepository;
use crate::features::typing_test::application::use_cases::StartTypingTest;
use crate::features::typing_test::domain::result::TestResult;
use crate::features::typing_test::domain::session::TestSession;
use crate::features::typing_test::domain::test_mode::TestMode;
use crate::features::typing_test::infrastructure::file_content_repository::FileContentRepository;
use crate::features::typing_test::presentation::render::{render_result, render_test};

const SAMPLE_RATE: Duration = Duration::from_millis(250);

pub fn run() -> AppResult<()> {
    let preferences = FilePreferencesRepository::new()?;
    let config = preferences.load_config()?;
    let themes = preferences.load_themes()?;
    let content = FileContentRepository::new(config_dir()?)?;
    let mut app = App::new(config, themes, content)?;

    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen)?;
    let keyboard_enhanced = supports_keyboard_enhancement().unwrap_or(false);
    if keyboard_enhanced {
        execute!(
            stdout,
            PushKeyboardEnhancementFlags(KeyboardEnhancementFlags::DISAMBIGUATE_ESCAPE_CODES)
        )?;
    }
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;
    let result = app.run(&mut terminal, &preferences);
    if keyboard_enhanced {
        execute!(terminal.backend_mut(), PopKeyboardEnhancementFlags)?;
    }
    disable_raw_mode()?;
    execute!(terminal.backend_mut(), LeaveAlternateScreen)?;
    terminal.show_cursor()?;
    result
}

struct App<R>
where
    R: ContentRepository,
{
    config: AppConfig,
    themes: BTreeMap<String, ThemeDefinition>,
    theme: ResolvedTheme,
    keymap: KeyMap,
    matcher: KeySequenceMatcher,
    content: R,
    screen: Screen,
    home: HomeState,
}

impl<R> App<R>
where
    R: ContentRepository,
{
    fn new(
        config: AppConfig,
        themes: BTreeMap<String, ThemeDefinition>,
        content: R,
    ) -> AppResult<Self> {
        let theme = themes
            .get(&config.defaults.theme)
            .or_else(|| themes.get("default"))
            .or_else(|| themes.values().next())
            .ok_or_else(|| AppError::InvalidConfig("no themes are available".into()))?
            .resolve()?;
        let keymap = KeyMap::from_config(&config.keybindings)?;
        let languages = content.available_languages()?;
        let theme_names = themes.keys().cloned().collect::<Vec<_>>();
        let home = HomeState::new(&config, languages, theme_names);

        Ok(Self {
            config,
            themes,
            theme,
            keymap,
            matcher: KeySequenceMatcher::default(),
            content,
            screen: Screen::Home,
            home,
        })
    }

    fn run(
        &mut self,
        terminal: &mut Terminal<CrosstermBackend<io::Stdout>>,
        preferences: &impl PreferencesRepository,
    ) -> AppResult<()> {
        loop {
            if let Screen::Test(session) = &mut self.screen {
                let now = Instant::now();
                session.tick(now);
                session.record_sample_if_due(now, SAMPLE_RATE);
                if session.is_complete() {
                    let result = session.result();
                    let key = format!("{}_{}", session.mode.key(), session.language);
                    let is_personal_best = self
                        .config
                        .personal_bests
                        .get(&key)
                        .map(|best| result.net_wpm > best.net_wpm)
                        .unwrap_or(true);
                    self.config.record_session(SessionHistoryEntry {
                        completed_at_unix: completed_at_unix(),
                        mode: session.mode.label(),
                        language: session.language.clone(),
                        net_wpm: result.net_wpm,
                        raw_wpm: result.raw_wpm,
                        accuracy: result.accuracy,
                        duration_secs: result.duration.as_secs_f64(),
                    });
                    if is_personal_best {
                        self.config.personal_bests.insert(
                            key,
                            PersonalBest {
                                net_wpm: result.net_wpm,
                                raw_wpm: result.raw_wpm,
                                accuracy: result.accuracy,
                            },
                        );
                    }
                    preferences.save_config(&self.config)?;
                    self.screen = Screen::Result {
                        result,
                        is_personal_best,
                    };
                }
            }

            terminal.draw(|frame| self.render(frame))?;

            if !event::poll(Duration::from_millis(16))? {
                continue;
            }

            let Event::Key(key) = event::read()? else {
                continue;
            };
            if key.kind != KeyEventKind::Press {
                continue;
            }

            if !self.handle_key(key, preferences)? {
                return Ok(());
            }
        }
    }

    fn handle_key(
        &mut self,
        key: KeyEvent,
        preferences: &impl PreferencesRepository,
    ) -> AppResult<bool> {
        match self.screen {
            Screen::Home => self.handle_home_key(key, preferences),
            Screen::Test(_) => self.handle_test_key(key),
            Screen::Result { .. } => self.handle_result_key(key, preferences),
            Screen::History => self.handle_history_key(key),
        }
    }

    fn handle_home_key(
        &mut self,
        key: KeyEvent,
        preferences: &impl PreferencesRepository,
    ) -> AppResult<bool> {
        let allowed_actions = if self.home.picker().is_some() {
            vec!["picker_next", "picker_previous", "start", "cancel", "quit"]
        } else {
            vec![
                "focus_next",
                "focus_previous",
                "cycle_next",
                "cycle_previous",
                "focus_mode",
                "focus_length",
                "focus_language",
                "focus_theme",
                "focus_start",
                "start",
                "cancel",
                "history",
                "quit",
            ]
        };

        if let Some(action) = self
            .matcher
            .push_for_actions(&key, &self.keymap, &allowed_actions)
        {
            match action.as_str() {
                "focus_next" => self.home.focus_next(),
                "focus_previous" => self.home.focus_previous(),
                "cycle_next" => self.home.cycle_next(),
                "cycle_previous" => self.home.cycle_previous(),
                "picker_next" => {
                    self.home.picker_next();
                    self.preview_picker_theme()?;
                }
                "picker_previous" => {
                    self.home.picker_previous();
                    self.preview_picker_theme()?;
                }
                "focus_mode" => self.home.focus(Field::Mode),
                "focus_length" => self.home.focus(Field::Length),
                "focus_language" => self.home.focus(Field::Language),
                "focus_theme" => self.home.focus(Field::Theme),
                "focus_start" => self.home.focus(Field::Start),
                "start" if self.home.picker().is_some() => self.home.confirm_picker(),
                "start" if self.home.focus == Field::Start => self.start_test(preferences)?,
                "start" => {
                    if self.home.can_open_picker() {
                        self.home.open_picker();
                    }
                }
                "cancel" => {
                    self.home.close_picker();
                    self.restore_selected_theme()?;
                }
                "history" => self.screen = Screen::History,
                "quit" => return Ok(false),
                _ => {}
            }
        }
        Ok(true)
    }

    fn handle_test_key(&mut self, key: KeyEvent) -> AppResult<bool> {
        if let Some(action) =
            self.matcher
                .push_for_actions(&key, &self.keymap, &["restart", "menu", "delete_word"])
        {
            match action.as_str() {
                "restart" => {
                    self.start_test_with_current_config()?;
                    return Ok(true);
                }
                "menu" => {
                    self.screen = Screen::Home;
                    return Ok(true);
                }
                "delete_word" => {
                    if let Screen::Test(session) = &mut self.screen {
                        session.delete_word();
                    }
                    return Ok(true);
                }
                _ => {}
            }
        }

        if let Screen::Test(session) = &mut self.screen {
            match key.code {
                KeyCode::Backspace => session.backspace(),
                KeyCode::Char(value)
                    if !key
                        .modifiers
                        .intersects(KeyModifiers::CONTROL | KeyModifiers::ALT) =>
                {
                    session.start_if_needed(Instant::now());
                    session.push_char(value);
                }
                _ => {}
            }
        }

        Ok(true)
    }

    fn handle_result_key(
        &mut self,
        key: KeyEvent,
        preferences: &impl PreferencesRepository,
    ) -> AppResult<bool> {
        if let Some(action) =
            self.matcher
                .push_for_actions(&key, &self.keymap, &["start", "focus_next", "quit"])
        {
            match action.as_str() {
                "start" => self.start_test(preferences)?,
                "focus_next" => self.screen = Screen::Home,
                "quit" => return Ok(false),
                _ => {}
            }
        }
        Ok(true)
    }

    fn handle_history_key(&mut self, key: KeyEvent) -> AppResult<bool> {
        if let Some(action) =
            self.matcher
                .push_for_actions(&key, &self.keymap, &["focus_next", "quit"])
        {
            match action.as_str() {
                "focus_next" => self.screen = Screen::Home,
                "quit" => return Ok(false),
                _ => {}
            }
        }
        Ok(true)
    }

    fn start_test(&mut self, preferences: &impl PreferencesRepository) -> AppResult<()> {
        self.config.defaults.mode = self.home.mode_name().into();
        self.config.defaults.duration = self.home.current_duration();
        self.config.defaults.word_count = self.home.current_word_count();
        self.config.defaults.language = self.home.current_language().into();
        self.config.defaults.theme = self.home.current_theme().into();
        preferences.save_config(&self.config)?;
        self.start_test_with_current_config()
    }

    fn start_test_with_current_config(&mut self) -> AppResult<()> {
        self.config.defaults.mode = self.home.mode_name().into();
        self.config.defaults.duration = self.home.current_duration();
        self.config.defaults.word_count = self.home.current_word_count();
        self.config.defaults.language = self.home.current_language().into();
        self.config.defaults.theme = self.home.current_theme().into();

        let theme = self
            .themes
            .get(self.home.current_theme())
            .ok_or_else(|| AppError::InvalidConfig("selected theme does not exist".into()))?
            .resolve()?;
        self.theme = theme;
        let mode = self.home.current_mode();
        let use_case = StartTypingTest::new(&self.content);
        self.screen = Screen::Test(use_case.execute(mode, self.home.current_language())?);
        self.matcher.clear();
        Ok(())
    }

    fn preview_picker_theme(&mut self) -> AppResult<()> {
        if let Some(picker) = self.home.picker() {
            if matches!(picker.kind, PickerKind::Theme) {
                let theme_name = &self.home.themes[picker.index];
                self.theme = self
                    .themes
                    .get(theme_name)
                    .ok_or_else(|| AppError::InvalidConfig("selected theme does not exist".into()))?
                    .resolve()?;
            }
        }
        Ok(())
    }

    fn restore_selected_theme(&mut self) -> AppResult<()> {
        self.theme = self
            .themes
            .get(self.home.current_theme())
            .ok_or_else(|| AppError::InvalidConfig("selected theme does not exist".into()))?
            .resolve()?;
        Ok(())
    }

    fn render(&self, frame: &mut Frame) {
        let area = frame.area();
        frame.render_widget(
            Block::default().style(Style::default().bg(self.theme.background)),
            area,
        );
        match &self.screen {
            Screen::Home => render_home(frame, area, &self.home, &self.theme),
            Screen::Test(session) => render_test(frame, area, session, &self.theme),
            Screen::Result {
                result,
                is_personal_best,
            } => render_result(frame, area, result, *is_personal_best, &self.theme),
            Screen::History => {
                render_history(frame, area, &self.config.session_history, &self.theme)
            }
        }
    }
}

enum Screen {
    Home,
    Test(TestSession),
    Result {
        result: TestResult,
        is_personal_best: bool,
    },
    History,
}

#[derive(Debug)]
struct HomeState {
    focus: Field,
    mode_index: usize,
    picker: Option<PickerState>,
    duration_index: usize,
    word_count_index: usize,
    language_index: usize,
    theme_index: usize,
    durations: Vec<u16>,
    word_counts: Vec<u16>,
    languages: Vec<String>,
    themes: Vec<String>,
}

impl HomeState {
    fn new(config: &AppConfig, languages: Vec<String>, themes: Vec<String>) -> Self {
        let mode_index = match config.defaults.mode.as_str() {
            "words" => 1,
            "punctuation" => 2,
            "numbers" => 3,
            "quote" => 4,
            _ => 0,
        };
        let duration_index = index_or_zero(&config.options.durations, config.defaults.duration);
        let word_count_index =
            index_or_zero(&config.options.word_counts, config.defaults.word_count);
        let language_index = index_or_zero(&languages, config.defaults.language.clone());
        let theme_index = index_or_zero(&themes, config.defaults.theme.clone());

        Self {
            focus: Field::Mode,
            mode_index,
            picker: None,
            duration_index,
            word_count_index,
            language_index,
            theme_index,
            durations: config.options.durations.clone(),
            word_counts: config.options.word_counts.clone(),
            languages,
            themes,
        }
    }

    fn focus_next(&mut self) {
        self.focus = self.focus.next();
    }

    fn focus_previous(&mut self) {
        self.focus = self.focus.previous();
    }

    fn focus(&mut self, field: Field) {
        self.focus = field;
    }

    fn cycle_next(&mut self) {
        self.cycle(1);
    }

    fn cycle_previous(&mut self) {
        self.cycle(-1);
    }

    fn cycle(&mut self, delta: isize) {
        match self.focus {
            Field::Mode => {}
            Field::Length => match self.mode_index {
                0 => {
                    self.duration_index =
                        cycle_index(self.duration_index, self.durations.len(), delta)
                }
                1 | 2 | 3 => {
                    self.word_count_index =
                        cycle_index(self.word_count_index, self.word_counts.len(), delta)
                }
                _ => {}
            },
            Field::Language => {
                self.language_index = cycle_index(self.language_index, self.languages.len(), delta)
            }
            Field::Theme => {
                self.theme_index = cycle_index(self.theme_index, self.themes.len(), delta)
            }
            Field::Start => {}
        }
    }

    fn can_open_picker(&self) -> bool {
        self.focus != Field::Start && (self.focus != Field::Length || self.mode_index != 4)
    }

    fn open_picker(&mut self) {
        self.picker = Some(match self.focus {
            Field::Mode => PickerState::new(PickerKind::Mode, self.mode_index),
            Field::Length if self.mode_index == 0 => {
                PickerState::new(PickerKind::Duration, self.duration_index)
            }
            Field::Length => PickerState::new(PickerKind::WordCount, self.word_count_index),
            Field::Language => PickerState::new(PickerKind::Language, self.language_index),
            Field::Theme => PickerState::new(PickerKind::Theme, self.theme_index),
            Field::Start => return,
        });
    }

    fn confirm_picker(&mut self) {
        if let Some(picker) = self.picker.take() {
            match picker.kind {
                PickerKind::Mode => self.mode_index = picker.index,
                PickerKind::Duration => self.duration_index = picker.index,
                PickerKind::WordCount => self.word_count_index = picker.index,
                PickerKind::Language => self.language_index = picker.index,
                PickerKind::Theme => self.theme_index = picker.index,
            }
        }
    }

    fn close_picker(&mut self) {
        self.picker = None;
    }

    fn picker(&self) -> Option<PickerState> {
        self.picker
    }

    fn picker_next(&mut self) {
        self.move_picker(1);
    }

    fn picker_previous(&mut self) {
        self.move_picker(-1);
    }

    fn move_picker(&mut self, delta: isize) {
        if let Some(picker) = self.picker {
            let len = picker.kind.len(self);
            if let Some(active_picker) = &mut self.picker {
                active_picker.index = cycle_index(active_picker.index, len, delta);
            }
        }
    }

    fn mode_name(&self) -> &'static str {
        match self.mode_index {
            1 => "words",
            2 => "punctuation",
            3 => "numbers",
            4 => "quote",
            _ => "time",
        }
    }

    fn current_mode(&self) -> TestMode {
        match self.mode_index {
            1 => TestMode::Words(self.current_word_count()),
            2 => TestMode::Punctuation(self.current_word_count()),
            3 => TestMode::Numbers(self.current_word_count()),
            4 => TestMode::Quote,
            _ => TestMode::Time(self.current_duration()),
        }
    }

    fn current_duration(&self) -> u16 {
        self.durations[self.duration_index]
    }

    fn current_word_count(&self) -> u16 {
        self.word_counts[self.word_count_index]
    }

    fn current_language(&self) -> &str {
        &self.languages[self.language_index]
    }

    fn current_theme(&self) -> &str {
        &self.themes[self.theme_index]
    }

    fn length_label(&self) -> String {
        match self.mode_index {
            1 | 2 | 3 => self.current_word_count().to_string(),
            4 => "quote".into(),
            _ => self.current_duration().to_string(),
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum Field {
    Mode,
    Length,
    Language,
    Theme,
    Start,
}

#[derive(Debug, Clone, Copy)]
struct PickerState {
    kind: PickerKind,
    index: usize,
}

impl PickerState {
    fn new(kind: PickerKind, index: usize) -> Self {
        Self { kind, index }
    }
}

#[derive(Debug, Clone, Copy)]
enum PickerKind {
    Mode,
    Duration,
    WordCount,
    Language,
    Theme,
}

impl PickerKind {
    fn len(self, home: &HomeState) -> usize {
        match self {
            Self::Mode => 5,
            Self::Duration => home.durations.len(),
            Self::WordCount => home.word_counts.len(),
            Self::Language => home.languages.len(),
            Self::Theme => home.themes.len(),
        }
    }

    fn title(self) -> &'static str {
        match self {
            Self::Mode => "select mode",
            Self::Duration | Self::WordCount => "select length",
            Self::Language => "select language",
            Self::Theme => "select theme",
        }
    }
}

impl Field {
    fn next(self) -> Self {
        match self {
            Self::Mode => Self::Length,
            Self::Length => Self::Language,
            Self::Language => Self::Theme,
            Self::Theme => Self::Start,
            Self::Start => Self::Mode,
        }
    }

    fn previous(self) -> Self {
        match self {
            Self::Mode => Self::Start,
            Self::Length => Self::Mode,
            Self::Language => Self::Length,
            Self::Theme => Self::Language,
            Self::Start => Self::Theme,
        }
    }
}

fn render_home(frame: &mut Frame, area: Rect, home: &HomeState, theme: &ResolvedTheme) {
    let sections = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(5),
            Constraint::Length(9),
            Constraint::Min(6),
            Constraint::Length(2),
        ])
        .horizontal_margin(2)
        .split(area);

    frame.render_widget(
        Paragraph::new(vec![
            Line::from("████████╗████████╗████████╗██╗   ██╗██╗"),
            Line::from("╚══██╔══╝╚══██╔══╝╚══██╔══╝██║   ██║██║"),
            Line::from("   ██║      ██║      ██║   ╚██████╔╝██║"),
        ])
        .alignment(Alignment::Center)
        .style(
            Style::default()
                .fg(theme.accent)
                .add_modifier(Modifier::BOLD),
        ),
        centered_block(sections[0], 3),
    );

    let length_label = home.length_label();
    let lines = vec![
        field_line(
            "1",
            "mode",
            home.mode_name(),
            home.focus == Field::Mode,
            theme,
        ),
        Line::from(""),
        field_line(
            "2",
            "length",
            &length_label,
            home.focus == Field::Length,
            theme,
        ),
        Line::from(""),
        field_line(
            "3",
            "language",
            home.current_language(),
            home.focus == Field::Language,
            theme,
        ),
        Line::from(""),
        field_line(
            "4",
            "theme",
            home.current_theme(),
            home.focus == Field::Theme,
            theme,
        ),
        Line::from(""),
        action_line("5", "start", home.focus == Field::Start, theme),
    ];
    frame.render_widget(Paragraph::new(lines), centered_column(sections[1], 32));

    if let Some(picker) = home.picker() {
        let modal = centered_rect(area, 38, modal_height(home, picker));
        frame.render_widget(Clear, modal);
        frame.render_widget(
            Paragraph::new(picker_lines(home, picker, theme))
                .alignment(Alignment::Left)
                .block(
                    Block::default()
                        .borders(Borders::ALL)
                        .title(picker.kind.title())
                        .style(Style::default().fg(theme.text)),
                ),
            modal,
        );
    }

    frame.render_widget(
        Paragraph::new("1-5 focus   tab/up/down move   enter open/select   q quit")
            .alignment(Alignment::Center)
            .style(Style::default().fg(theme.muted)),
        sections[3],
    );
}

fn centered_block(area: Rect, height: u16) -> Rect {
    Rect {
        x: area.x,
        y: area.y + area.height.saturating_sub(height) / 2,
        width: area.width,
        height: area.height.min(height),
    }
}

fn centered_rect(area: Rect, width: u16, height: u16) -> Rect {
    let width = area.width.min(width);
    let height = area.height.min(height);
    Rect {
        x: area.x + area.width.saturating_sub(width) / 2,
        y: area.y + area.height.saturating_sub(height) / 2,
        width,
        height,
    }
}

fn centered_column(area: Rect, width: u16) -> Rect {
    let width = area.width.min(width);
    Rect {
        x: area.x + area.width.saturating_sub(width) / 2,
        y: area.y,
        width,
        height: area.height,
    }
}

fn field_line<'a>(
    shortcut: &'a str,
    label: &'a str,
    value: &'a str,
    focused: bool,
    theme: &ResolvedTheme,
) -> Line<'a> {
    let value_style = if focused {
        Style::default()
            .fg(theme.selection)
            .add_modifier(Modifier::BOLD | Modifier::UNDERLINED)
    } else {
        Style::default().fg(theme.text)
    };
    Line::from(vec![
        Span::styled(shortcut, Style::default().fg(theme.muted)),
        Span::raw("    "),
        Span::styled(format!("{label:<10}"), Style::default().fg(theme.muted)),
        Span::styled(value, value_style),
    ])
}

fn action_line<'a>(
    shortcut: &'a str,
    label: &'a str,
    focused: bool,
    theme: &ResolvedTheme,
) -> Line<'a> {
    let label_style = if focused {
        Style::default()
            .fg(theme.selection)
            .add_modifier(Modifier::BOLD | Modifier::UNDERLINED)
    } else {
        Style::default().fg(theme.text)
    };

    Line::from(vec![
        Span::styled(shortcut, Style::default().fg(theme.muted)),
        Span::raw("    "),
        Span::styled(label, label_style),
    ])
}

fn picker_lines(
    home: &HomeState,
    picker: PickerState,
    theme: &ResolvedTheme,
) -> Vec<Line<'static>> {
    picker_values(home, picker.kind)
        .into_iter()
        .enumerate()
        .map(|(current, value)| {
            let prefix = if current == picker.index { "> " } else { "  " };
            let style = if current == picker.index {
                Style::default()
                    .fg(theme.selection)
                    .add_modifier(Modifier::BOLD)
            } else {
                Style::default().fg(theme.text)
            };
            Line::from(Span::styled(format!("{prefix}{value}"), style))
        })
        .collect()
}

fn picker_values(home: &HomeState, kind: PickerKind) -> Vec<String> {
    match kind {
        PickerKind::Mode => ["time", "words", "punctuation", "numbers", "quote"]
            .into_iter()
            .map(str::to_string)
            .collect(),
        PickerKind::Duration => home.durations.iter().map(ToString::to_string).collect(),
        PickerKind::WordCount => home.word_counts.iter().map(ToString::to_string).collect(),
        PickerKind::Language => home.languages.clone(),
        PickerKind::Theme => home.themes.clone(),
    }
}

fn modal_height(home: &HomeState, picker: PickerState) -> u16 {
    picker_values(home, picker.kind).len() as u16 + 2
}

fn cycle_index(index: usize, len: usize, delta: isize) -> usize {
    if len == 0 {
        return 0;
    }

    (index as isize + delta).rem_euclid(len as isize) as usize
}

fn index_or_zero<T: PartialEq>(values: &[T], expected: T) -> usize {
    values
        .iter()
        .position(|value| *value == expected)
        .unwrap_or(0)
}

fn completed_at_unix() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs()
}
