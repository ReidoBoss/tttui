use std::time::{Duration, Instant};

use super::result::TestResult;
use super::test_mode::TestMode;

#[derive(Debug, Clone)]
pub struct TestSession {
    pub mode: TestMode,
    pub language: String,
    pub target: Vec<char>,
    pub input: Vec<char>,
    pub started_at: Option<Instant>,
    pub elapsed: Duration,
    pub sample_history: Vec<(Duration, f64)>,
    pub last_sample_at: Option<Instant>,
}

impl TestSession {
    pub fn new(mode: TestMode, language: String, target: String) -> Self {
        Self {
            mode,
            language,
            target: target.chars().collect(),
            input: Vec::new(),
            started_at: None,
            elapsed: Duration::ZERO,
            sample_history: Vec::new(),
            last_sample_at: None,
        }
    }

    pub fn start_if_needed(&mut self, now: Instant) {
        if self.started_at.is_none() {
            self.started_at = Some(now);
            self.last_sample_at = Some(now);
        }
    }

    pub fn tick(&mut self, now: Instant) {
        if let Some(started_at) = self.started_at {
            self.elapsed = now.saturating_duration_since(started_at);
        }
    }

    pub fn push_char(&mut self, value: char) {
        if self.input.len() < self.target.len() {
            self.input.push(value);
        }
    }

    pub fn backspace(&mut self) {
        self.input.pop();
    }

    pub fn delete_word(&mut self) {
        let mut new_len = self.input.len();
        while new_len > 0 && self.target.get(new_len - 1) == Some(&' ') {
            new_len -= 1;
        }
        while new_len > 0 && self.target.get(new_len - 1).is_some_and(|c| *c != ' ') {
            new_len -= 1;
        }
        self.input.truncate(new_len);
    }

    pub fn typed_chars(&self) -> usize {
        self.input.len()
    }

    pub fn correct_chars(&self) -> usize {
        self.input
            .iter()
            .zip(self.target.iter())
            .filter(|(typed, expected)| typed == expected)
            .count()
    }

    pub fn incorrect_chars(&self) -> usize {
        self.typed_chars().saturating_sub(self.correct_chars())
    }

    pub fn current_raw_wpm(&self) -> f64 {
        wpm(self.typed_chars(), self.elapsed)
    }

    pub fn current_net_wpm(&self) -> f64 {
        wpm(self.correct_chars(), self.elapsed)
    }

    pub fn record_sample_if_due(&mut self, now: Instant, sample_rate: Duration) {
        if self.started_at.is_none() {
            return;
        }

        let due = self
            .last_sample_at
            .map(|last_sample| now.saturating_duration_since(last_sample) >= sample_rate)
            .unwrap_or(true);

        if due {
            self.tick(now);
            self.sample_history
                .push((self.elapsed, self.current_raw_wpm()));
            self.last_sample_at = Some(now);
        }
    }

    pub fn is_complete(&self) -> bool {
        match self.mode {
            TestMode::Time(duration) => self.elapsed >= Duration::from_secs(duration as u64),
            TestMode::Words(_)
            | TestMode::Punctuation(_)
            | TestMode::Numbers(_)
            | TestMode::Quote => self.input.len() == self.target.len(),
        }
    }

    pub fn result(&self) -> TestResult {
        let correct_chars = self.correct_chars();
        let incorrect_chars = self.incorrect_chars();
        let typed_chars = self.typed_chars();
        let history = self.sample_history.clone();
        let accuracy = if typed_chars == 0 {
            0.0
        } else {
            correct_chars as f64 / typed_chars as f64 * 100.0
        };
        let net_wpm = wpm(correct_chars, self.elapsed);
        let raw_wpm = wpm(typed_chars, self.elapsed);
        let consistency = consistency(&history, net_wpm);

        TestResult {
            net_wpm,
            raw_wpm,
            accuracy,
            consistency,
            duration: self.elapsed,
            correct_chars,
            incorrect_chars,
            remaining_chars: self.target.len().saturating_sub(self.input.len()),
            history,
        }
    }
}

fn wpm(chars: usize, duration: Duration) -> f64 {
    if duration.is_zero() {
        return 0.0;
    }

    (chars as f64 / 5.0) / (duration.as_secs_f64() / 60.0)
}

fn consistency(history: &[(Duration, f64)], net_wpm: f64) -> f64 {
    if history.len() < 2 || net_wpm <= 0.0 {
        return 100.0;
    }

    let mean = history.iter().map(|(_, value)| value).sum::<f64>() / history.len() as f64;
    let variance = history
        .iter()
        .map(|(_, value)| {
            let delta = value - mean;
            delta * delta
        })
        .sum::<f64>()
        / (history.len() - 1) as f64;
    let stddev = variance.sqrt();

    (100.0 - stddev / net_wpm * 100.0).max(0.0)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn delete_word_is_noop_on_empty_input() {
        let mut session = TestSession::new(TestMode::Words(2), "english".into(), "cat dog".into());
        session.delete_word();
        assert!(session.input.is_empty());
    }

    #[test]
    fn delete_word_removes_partial_word() {
        let mut session = TestSession::new(TestMode::Words(2), "english".into(), "cat dog".into());
        session.input = vec!['c', 'a', 't', ' ', 'd', 'o'];
        session.delete_word();
        assert_eq!(session.input, vec!['c', 'a', 't', ' ']);
    }

    #[test]
    fn delete_word_at_word_start_removes_previous_word() {
        let mut session = TestSession::new(TestMode::Words(2), "english".into(), "cat dog".into());
        session.input = vec!['c', 'a', 't', ' '];
        session.delete_word();
        assert!(session.input.is_empty());
    }

    #[test]
    fn delete_word_uses_target_boundaries_for_mistyped_space() {
        let mut session = TestSession::new(TestMode::Words(2), "english".into(), "cat dog".into());
        session.input = vec!['c', 'a', 't', 'x', 'd', 'o'];
        session.delete_word();
        assert_eq!(session.input, vec!['c', 'a', 't', 'x']);
    }

    #[test]
    fn delete_word_clears_single_word() {
        let mut session = TestSession::new(TestMode::Words(1), "english".into(), "cat".into());
        session.input = vec!['c', 'a'];
        session.delete_word();
        assert!(session.input.is_empty());
    }

    #[test]
    fn computes_accuracy_from_input() {
        let mut session = TestSession::new(TestMode::Words(1), "english".into(), "cat".into());
        session.input = vec!['c', 'o', 't'];
        session.elapsed = Duration::from_secs(60);
        let result = session.result();

        assert_eq!(result.correct_chars, 2);
        assert_eq!(result.incorrect_chars, 1);
        assert!((result.accuracy - 66.666).abs() < 0.01);
    }
}
