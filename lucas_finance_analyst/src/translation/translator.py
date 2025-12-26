"""
Free translation module using multiple fallback options
1. deep-translator (free, no API key)
2. googletrans (free, unofficial)
"""
from typing import Optional
import re


class Translator:
    """Multi-backend translator with fallback options"""

    def __init__(self, cache_manager=None):
        """
        Initialize translator

        Args:
            cache_manager: Database manager for caching translations
        """
        self.cache_manager = cache_manager
        self.translator = None
        self._init_translator()

    def _init_translator(self):
        """Initialize translation backend with fallbacks"""
        # Try deep-translator first (more reliable)
        try:
            from deep_translator import GoogleTranslator
            self.translator = GoogleTranslator(source='auto', target='en')
            self.backend = 'deep-translator'
            print("✓ Translation: Using deep-translator")
            return
        except ImportError:
            print("  deep-translator not available")

        # Fallback to googletrans
        try:
            from googletrans import Translator as GoogleTrans
            self.translator = GoogleTrans()
            self.backend = 'googletrans'
            print("✓ Translation: Using googletrans")
            return
        except ImportError:
            print("  googletrans not available")

        # No translator available
        self.backend = None
        print("⚠ Warning: No translation library available. Install with:")
        print("  pip install deep-translator")

    def translate(self, text: str, source_lang: str = 'auto', target_lang: str = 'en') -> Optional[str]:
        """
        Translate text from source language to target language

        Args:
            text: Text to translate
            source_lang: Source language code (default: auto-detect)
            target_lang: Target language code (default: en)

        Returns:
            Translated text or None if translation fails
        """
        if not text or not text.strip():
            return text

        # Check if translation needed
        if not self._needs_translation(text, target_lang):
            return text

        # Check cache first
        if self.cache_manager:
            cached = self.cache_manager.get_cached_translation(text)
            if cached:
                return cached

        # Translate
        translated = self._do_translation(text, source_lang, target_lang)

        # Cache result
        if translated and self.cache_manager:
            self.cache_manager.cache_translation(text, translated, source_lang, target_lang)

        return translated

    def _needs_translation(self, text: str, target_lang: str) -> bool:
        """Check if text needs translation"""
        if target_lang != 'en':
            return True

        # Check if text contains Chinese characters
        has_chinese = bool(re.search(r'[\u4e00-\u9fff]', text))

        return has_chinese

    def _do_translation(self, text: str, source_lang: str, target_lang: str) -> Optional[str]:
        """Perform actual translation"""
        if self.translator is None:
            return None

        try:
            if self.backend == 'deep-translator':
                # deep-translator
                from deep_translator import GoogleTranslator
                translator = GoogleTranslator(source=source_lang, target=target_lang)
                return translator.translate(text)

            elif self.backend == 'googletrans':
                # googletrans
                result = self.translator.translate(text, src=source_lang, dest=target_lang)
                return result.text

        except Exception as e:
            print(f"  Translation error: {e}")
            return None

    def detect_language(self, text: str) -> str:
        """
        Detect language of text

        Returns:
            Language code (e.g., 'zh-cn', 'en')
        """
        # Simple detection based on character ranges
        if re.search(r'[\u4e00-\u9fff]', text):
            return 'zh'
        return 'en'

    def batch_translate(self, texts: list, source_lang: str = 'auto',
                       target_lang: str = 'en') -> list:
        """
        Translate multiple texts

        Args:
            texts: List of texts to translate
            source_lang: Source language
            target_lang: Target language

        Returns:
            List of translated texts
        """
        translated = []

        for text in texts:
            result = self.translate(text, source_lang, target_lang)
            translated.append(result if result else text)

        return translated


def test_translator():
    """Test the translator"""
    translator = Translator()

    # Test Chinese to English
    chinese_text = "腾讯控股发布第三季度财报"
    print(f"Original (Chinese): {chinese_text}")

    translated = translator.translate(chinese_text)
    print(f"Translated (English): {translated}")

    # Test English (should not translate)
    english_text = "Tencent reports Q3 earnings"
    print(f"\nOriginal (English): {english_text}")

    result = translator.translate(english_text)
    print(f"Result: {result}")

    # Test language detection
    print(f"\nLanguage detection:")
    print(f"  '{chinese_text}' -> {translator.detect_language(chinese_text)}")
    print(f"  '{english_text}' -> {translator.detect_language(english_text)}")


if __name__ == "__main__":
    test_translator()
