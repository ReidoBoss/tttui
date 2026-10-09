use std::collections::BTreeSet;
use std::fs;
use std::path::{Path, PathBuf};

use tttui_core::{AppError, AppResult};

use crate::features::typing_test::application::ports::ContentRepository;

const LANGUAGES: &str = "languages";
const QUOTES: &str = "quotes";

/// Bundled content is embedded at compile time so that distributed binaries
/// (release archives, `cargo install`, `cargo binstall`) work without the
/// source tree that produced them.
const BUNDLED_LANGUAGES: &[(&str, &str)] = &[
    (
        "english",
        include_str!("../../../../assets/languages/english.txt"),
    ),
    (
        "italian",
        include_str!("../../../../assets/languages/italian.txt"),
    ),
    (
        "japanese",
        include_str!("../../../../assets/languages/japanese.txt"),
    ),
    (
        "russian",
        include_str!("../../../../assets/languages/russian.txt"),
    ),
    (
        "spanish",
        include_str!("../../../../assets/languages/spanish.txt"),
    ),
];

const BUNDLED_QUOTES: &[(&str, &str)] = &[
    (
        "english",
        include_str!("../../../../assets/quotes/english.txt"),
    ),
    (
        "italian",
        include_str!("../../../../assets/quotes/italian.txt"),
    ),
    (
        "japanese",
        include_str!("../../../../assets/quotes/japanese.txt"),
    ),
    (
        "russian",
        include_str!("../../../../assets/quotes/russian.txt"),
    ),
    (
        "spanish",
        include_str!("../../../../assets/quotes/spanish.txt"),
    ),
];

pub struct FileContentRepository {
    config_dir: PathBuf,
}

impl FileContentRepository {
    pub fn new(config_dir: PathBuf) -> AppResult<Self> {
        fs::create_dir_all(config_dir.join(LANGUAGES))?;
        fs::create_dir_all(config_dir.join(QUOTES))?;
        Ok(Self { config_dir })
    }

    fn user_dir(&self, item_type: &str) -> PathBuf {
        self.config_dir.join(item_type)
    }

    fn bundled_items(item_type: &str) -> &'static [(&'static str, &'static str)] {
        match item_type {
            LANGUAGES => BUNDLED_LANGUAGES,
            QUOTES => BUNDLED_QUOTES,
            _ => &[],
        }
    }

    fn bundled_content(item_type: &str, language: &str) -> Option<&'static str> {
        Self::bundled_items(item_type)
            .iter()
            .find(|(name, _)| *name == language)
            .map(|(_, content)| *content)
    }

    fn parse_items(raw: &str) -> Vec<String> {
        raw.lines()
            .map(str::trim)
            .filter(|line| !line.is_empty())
            .map(ToOwned::to_owned)
            .collect()
    }

    fn available_from_dir(path: &Path) -> AppResult<Vec<String>> {
        if !path.exists() {
            return Ok(Vec::new());
        }

        let mut values = Vec::new();
        for entry in fs::read_dir(path)? {
            let entry = entry?;
            let path = entry.path();
            if path.extension().and_then(|value| value.to_str()) == Some("txt") {
                if let Some(stem) = path.file_stem().and_then(|value| value.to_str()) {
                    values.push(stem.to_string());
                }
            }
        }
        Ok(values)
    }

    fn load_items(&self, item_type: &str, language: &str) -> AppResult<Vec<String>> {
        let user_path = self.user_dir(item_type).join(format!("{language}.txt"));

        let raw = if user_path.exists() {
            fs::read_to_string(user_path)?
        } else {
            Self::bundled_content(item_type, language)
                .ok_or_else(|| {
                    AppError::InvalidConfig(format!(
                        "no bundled or user-provided {item_type} content for language '{language}'"
                    ))
                })?
                .to_string()
        };

        Ok(Self::parse_items(&raw))
    }
}

impl ContentRepository for FileContentRepository {
    fn available_languages(&self) -> AppResult<Vec<String>> {
        let mut values = BTreeSet::new();
        values.extend(
            Self::bundled_items(LANGUAGES)
                .iter()
                .map(|(name, _)| (*name).to_string()),
        );
        values.extend(Self::available_from_dir(&self.user_dir(LANGUAGES))?);
        Ok(values.into_iter().collect())
    }

    fn words(&self, language: &str) -> AppResult<Vec<String>> {
        self.load_items(LANGUAGES, language)
    }

    fn quotes(&self, language: &str) -> AppResult<Vec<String>> {
        self.load_items(QUOTES, language)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const SUPPORTED_LANGUAGES: [&str; 5] = ["english", "italian", "japanese", "russian", "spanish"];

    fn temp_config_dir(label: &str) -> PathBuf {
        let dir =
            std::env::temp_dir().join(format!("tttui-content-{}-{label}", std::process::id()));
        let _ = fs::remove_dir_all(&dir);
        fs::create_dir_all(&dir).expect("temp config dir");
        dir
    }

    fn repository(label: &str) -> FileContentRepository {
        FileContentRepository::new(temp_config_dir(label)).expect("repository")
    }

    #[test]
    fn lists_every_bundled_language_with_an_empty_config_dir() {
        let repo = repository("lists");
        let languages = repo.available_languages().expect("available languages");

        for language in SUPPORTED_LANGUAGES {
            assert!(
                languages.contains(&language.to_string()),
                "missing bundled language {language}"
            );
        }
    }

    #[test]
    fn loads_bundled_words_and_quotes_for_every_language() {
        let repo = repository("loads");

        for language in SUPPORTED_LANGUAGES {
            let words = repo.words(language).expect("bundled words");
            assert!(words.len() > 1, "{language} exposes {} words", words.len());

            let quotes = repo.quotes(language).expect("bundled quotes");
            assert!(!quotes.is_empty(), "{language} exposes no quotes");
        }
    }

    #[test]
    fn user_files_override_bundled_content() {
        let dir = temp_config_dir("override");
        let repo = FileContentRepository::new(dir.clone()).expect("repository");
        fs::write(dir.join("languages").join("english.txt"), "userword\n").expect("write");

        assert_eq!(repo.words("english").expect("words"), vec!["userword"]);
    }

    #[test]
    fn user_languages_are_merged_with_bundled_ones() {
        let dir = temp_config_dir("merged");
        let repo = FileContentRepository::new(dir.clone()).expect("repository");
        fs::write(dir.join("languages").join("klingon.txt"), "tlhIngan\n").expect("write");

        let languages = repo.available_languages().expect("available languages");
        assert!(languages.contains(&"klingon".to_string()));
        assert!(languages.contains(&"english".to_string()));
    }

    #[test]
    fn unknown_language_reports_a_config_error() {
        let repo = repository("unknown");

        let error = repo
            .words("klingon")
            .expect_err("unknown language must fail");
        assert!(matches!(error, AppError::InvalidConfig(_)), "got {error:?}");
    }

    #[test]
    fn every_bundled_entry_is_non_empty() {
        for (item_type, items) in [(LANGUAGES, BUNDLED_LANGUAGES), (QUOTES, BUNDLED_QUOTES)] {
            assert!(!items.is_empty(), "{item_type} has no bundled entries");

            for (name, content) in items {
                assert!(
                    !content.trim().is_empty(),
                    "bundled {item_type}/{name} is empty"
                );
            }
        }
    }
}
