"""Internationalization utilities for Health Addon."""
import json
import logging
from pathlib import Path
from typing import Optional

_LOGGER = logging.getLogger(__name__)

_translations: dict = {}
_current_lang: str = "en"


def load_translations(translations_path: Path, language: str = "en") -> None:
    """Load translation files."""
    global _translations, _current_lang
    _current_lang = language
    
    # Load English as fallback
    en_path = translations_path / "en.json"
    if en_path.exists():
        with open(en_path, "r", encoding="utf-8") as f:
            _translations["en"] = json.load(f)
        _LOGGER.info("Loaded English translations")
    
    # Load requested language
    if language != "en":
        lang_path = translations_path / f"{language}.json"
        if lang_path.exists():
            with open(lang_path, "r", encoding="utf-8") as f:
                _translations[language] = json.load(f)
            _LOGGER.info("Loaded %s translations", language)
        else:
            _LOGGER.warning("Translation file not found: %s, using English", lang_path)


def t(key: str, default: str = None, **kwargs) -> str:
    """Translate a key."""
    # Navigate nested keys like "services.add_medication.name"
    keys = key.split(".")
    
    # Try current language first, then fallback to English
    for lang in [_current_lang, "en"]:
        if lang in _translations:
            value = _translations[lang]
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    break
            else:
                # Found value
                if isinstance(value, str):
                    return value.format(**kwargs) if kwargs else value
    
    # Return default or key
    return default or key


def set_language(language: str) -> None:
    """Set current language."""
    global _current_lang
    _current_lang = language


def get_language() -> str:
    """Get current language."""
    return _current_lang