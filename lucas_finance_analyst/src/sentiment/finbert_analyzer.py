"""
FinBERT sentiment analyzer for English financial text
Uses pre-trained FinBERT model from Hugging Face
"""
from typing import Dict, Optional


class FinBERTAnalyzer:
    """Financial sentiment analysis using FinBERT"""

    def __init__(self):
        """Initialize FinBERT model"""
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        self._init_model()

    def _init_model(self):
        """Load FinBERT model from Hugging Face"""
        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

            print("Loading FinBERT model (this may take a moment on first run)...")

            model_name = "ProsusAI/finbert"

            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)

            self.pipeline = pipeline(
                "sentiment-analysis",
                model=self.model,
                tokenizer=self.tokenizer
            )

            print("✓ FinBERT model loaded successfully")

        except ImportError:
            print("⚠ transformers library not available. Install with:")
            print("  pip install transformers torch")
        except Exception as e:
            print(f"⚠ Error loading FinBERT: {e}")

    def analyze(self, text: str) -> Optional[Dict]:
        """
        Analyze sentiment of financial text

        Args:
            text: Text to analyze (English)

        Returns:
            Dictionary with sentiment label, score, and confidence
            Example: {'label': 'positive', 'score': 0.85, 'confidence': 0.85}
        """
        if not text or not text.strip():
            return None

        if self.pipeline is None:
            return self._fallback_sentiment(text)

        try:
            # Truncate long text (BERT max is 512 tokens)
            max_length = 500
            if len(text) > max_length:
                text = text[:max_length]

            # Run sentiment analysis
            result = self.pipeline(text)[0]

            # FinBERT returns: positive, negative, neutral
            label = result['label'].lower()
            confidence = result['score']

            # Convert to numeric score: positive=1, neutral=0, negative=-1
            score_map = {
                'positive': 1.0,
                'neutral': 0.0,
                'negative': -1.0
            }

            score = score_map.get(label, 0.0) * confidence

            return {
                'label': label,
                'score': score,
                'confidence': confidence
            }

        except Exception as e:
            print(f"  FinBERT analysis error: {e}")
            return self._fallback_sentiment(text)

    def _fallback_sentiment(self, text: str) -> Dict:
        """
        Simple keyword-based sentiment as fallback

        Returns:
            Dictionary with sentiment data
        """
        positive_words = [
            'profit', 'gain', 'growth', 'surge', 'beat', 'exceed',
            'strong', 'robust', 'upgrade', 'bullish', 'outperform',
            'success', 'record', 'high', 'breakthrough'
        ]

        negative_words = [
            'loss', 'decline', 'fall', 'drop', 'miss', 'weak',
            'downgrade', 'bearish', 'underperform', 'concern',
            'warning', 'risk', 'investigation', 'lawsuit', 'fraud'
        ]

        text_lower = text.lower()

        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)

        if pos_count > neg_count:
            label = 'positive'
            confidence = min(pos_count * 0.25, 0.8)
            score = confidence
        elif neg_count > pos_count:
            label = 'negative'
            confidence = min(neg_count * 0.25, 0.8)
            score = -confidence
        else:
            label = 'neutral'
            confidence = 0.5
            score = 0.0

        return {
            'label': label,
            'score': score,
            'confidence': confidence
        }

    def batch_analyze(self, texts: list) -> list:
        """
        Analyze sentiment for multiple texts

        Args:
            texts: List of texts to analyze

        Returns:
            List of sentiment dictionaries
        """
        results = []
        for text in texts:
            result = self.analyze(text)
            results.append(result)

        return results


def test_analyzer():
    """Test FinBERT analyzer"""
    analyzer = FinBERTAnalyzer()

    test_texts = [
        "Company reports strong Q3 earnings, beating analyst expectations",
        "Stock plunges on profit warning and weak guidance",
        "The company announced a new product launch",
    ]

    print("\nTesting FinBERT analyzer:")
    for text in test_texts:
        result = analyzer.analyze(text)
        print(f"\nText: {text}")
        print(f"Sentiment: {result['label']} (score: {result['score']:.2f}, confidence: {result['confidence']:.2f})")


if __name__ == "__main__":
    test_analyzer()
