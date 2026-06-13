use std::collections::BTreeMap;

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppConfig {
    #[serde(default)]
    pub defaults: Defaults,
    #[serde(default)]
    pub options: Options,
    #[serde(default)]
    pub keybindings: BTreeMap<String, Vec<String>>,
    #[serde(default)]
    pub personal_bests: BTreeMap<String, PersonalBest>,
    #[serde(default)]
    pub session_history: Vec<SessionHistoryEntry>,
}

impl Default for AppConfig {
    fn default() -> Self {
        let mut keybindings = BTreeMap::new();
        keybindings.insert("quit".into(), vec!["q".into()]);
        keybindings.insert("start".into(), vec!["enter".into()]);
        keybindings.insert("focus_next".into(), vec!["tab".into(), "down".into()]);
        keybindings.insert(
            "focus_previous".into(),
            vec!["shift+tab".into(), "up".into()],
        );
        keybindings.insert("cycle_next".into(), vec!["right".into(), "l".into()]);
        keybindings.insert("cycle_previous".into(), vec!["left".into(), "h".into()]);
        keybindings.insert("picker_next".into(), vec!["down".into(), "j".into()]);
        keybindings.insert("picker_previous".into(), vec!["up".into(), "k".into()]);
        keybindings.insert("focus_mode".into(), vec!["1".into()]);
        keybindings.insert("focus_length".into(), vec!["2".into()]);
        keybindings.insert("focus_language".into(), vec!["3".into()]);
        keybindings.insert("focus_theme".into(), vec!["4".into()]);
        keybindings.insert("focus_start".into(), vec!["5".into()]);
        keybindings.insert("restart".into(), vec!["tab enter".into()]);
        keybindings.insert("menu".into(), vec!["tab m".into()]);
        keybindings.insert("history".into(), vec!["g".into()]);
        keybindings.insert("cancel".into(), vec!["esc".into()]);
        keybindings.insert("backspace".into(), vec!["backspace".into()]);
        keybindings.insert(
            "delete_word".into(),
            vec![
                "ctrl+backspace".into(),
                "ctrl+h".into(),
                "ctrl+w".into(),
                "alt+backspace".into(),
            ],
        );

        Self {
            defaults: Defaults::default(),
            options: Options::default(),
            keybindings,
            personal_bests: BTreeMap::new(),
            session_history: Vec::new(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Defaults {
    #[serde(default = "default_mode")]
    pub mode: String,
    #[serde(default = "default_duration")]
    pub duration: u16,
    #[serde(default = "default_word_count")]
    pub word_count: u16,
    #[serde(default = "default_language")]
    pub language: String,
    #[serde(default = "default_theme")]
    pub theme: String,
}

impl Default for Defaults {
    fn default() -> Self {
        Self {
            mode: default_mode(),
            duration: default_duration(),
            word_count: default_word_count(),
            language: default_language(),
            theme: default_theme(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Options {
    #[serde(default = "default_durations")]
    pub durations: Vec<u16>,
    #[serde(default = "default_word_counts")]
    pub word_counts: Vec<u16>,
    #[serde(default = "default_history_limit")]
    pub history_limit: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PersonalBest {
    pub net_wpm: f64,
    pub raw_wpm: f64,
    pub accuracy: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SessionHistoryEntry {
    pub completed_at_unix: u64,
    pub mode: String,
    pub language: String,
    pub net_wpm: f64,
    pub raw_wpm: f64,
    pub accuracy: f64,
    pub duration_secs: f64,
}

impl Default for Options {
    fn default() -> Self {
        Self {
            durations: default_durations(),
            word_counts: default_word_counts(),
            history_limit: default_history_limit(),
        }
    }
}

impl AppConfig {
    pub fn record_session(&mut self, entry: SessionHistoryEntry) {
        self.session_history.insert(0, entry);
        self.session_history.truncate(self.options.history_limit);
    }

    pub fn merge_missing_keybindings(&mut self) {
        for (action, bindings) in Self::default().keybindings {
            self.keybindings.entry(action).or_insert(bindings);
        }
    }

    pub fn upgrade_legacy_default_keybindings(&mut self) {
        if self
            .keybindings
            .get("focus_next")
            .is_some_and(|bindings| bindings == &["tab"])
        {
            self.keybindings
                .insert("focus_next".into(), vec!["tab".into(), "down".into()]);
        }

        if self
            .keybindings
            .get("focus_previous")
            .is_some_and(|bindings| bindings == &["shift+tab"])
        {
            self.keybindings.insert(
                "focus_previous".into(),
                vec!["shift+tab".into(), "up".into()],
            );
        }
    }
}

fn default_mode() -> String {
    "time".into()
}

fn default_duration() -> u16 {
    30
}

fn default_word_count() -> u16 {
    25
}

fn default_language() -> String {
    "english".into()
}

fn default_theme() -> String {
    "default".into()
}

fn default_durations() -> Vec<u16> {
    vec![15, 30, 60, 120]
}

fn default_word_counts() -> Vec<u16> {
    vec![10, 25, 50, 100]
}

fn default_history_limit() -> usize {
    20
}

#[cfg(test)]
mod tests {
    use super::*;

    fn session(index: u64) -> SessionHistoryEntry {
        SessionHistoryEntry {
            completed_at_unix: index,
            mode: "words 25".into(),
            language: "english".into(),
            net_wpm: 80.0,
            raw_wpm: 82.0,
            accuracy: 98.0,
            duration_secs: 30.0,
        }
    }

    #[test]
    fn session_history_is_newest_first_and_bounded() {
        let mut config = AppConfig::default();
        config.options.history_limit = 2;

        config.record_session(session(1));
        config.record_session(session(2));
        config.record_session(session(3));

        assert_eq!(config.session_history.len(), 2);
        assert_eq!(config.session_history[0].completed_at_unix, 3);
        assert_eq!(config.session_history[1].completed_at_unix, 2);
    }

    #[test]
    fn missing_keybindings_are_added_without_overwriting_custom_values() {
        let mut config = AppConfig::default();
        config.keybindings.remove("history");
        config.keybindings.insert("quit".into(), vec!["x".into()]);

        config.merge_missing_keybindings();

        assert_eq!(config.keybindings["history"], vec!["g"]);
        assert_eq!(config.keybindings["quit"], vec!["x"]);
    }

    #[test]
    fn legacy_default_focus_bindings_gain_arrow_keys() {
        let mut config = AppConfig::default();
        config
            .keybindings
            .insert("focus_next".into(), vec!["tab".into()]);
        config
            .keybindings
            .insert("focus_previous".into(), vec!["shift+tab".into()]);

        config.upgrade_legacy_default_keybindings();

        assert_eq!(config.keybindings["focus_next"], vec!["tab", "down"]);
        assert_eq!(
            config.keybindings["focus_previous"],
            vec!["shift+tab", "up"]
        );
    }

    #[test]
    fn custom_focus_bindings_are_not_upgraded() {
        let mut config = AppConfig::default();
        config
            .keybindings
            .insert("focus_next".into(), vec!["n".into()]);
        config
            .keybindings
            .insert("focus_previous".into(), vec!["p".into()]);

        config.upgrade_legacy_default_keybindings();

        assert_eq!(config.keybindings["focus_next"], vec!["n"]);
        assert_eq!(config.keybindings["focus_previous"], vec!["p"]);
    }
}
