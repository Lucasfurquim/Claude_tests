"""
SnowNLP sentiment analyzer for Chinese text
"""
from typing import Dict, Optional


class SnowNLPAnalyzer:
    """Chinese sentiment analysis using SnowNLP"""

    def __init__(self):
        """Initialize SnowNLP"""
        self.available = False
        self._init_snownlp()

    def _init_snownlp(self):
        """Check if SnowNLP is available"""
        try:
            import snownlp
            self.available = True
            print("✓ SnowNLP available for Chinese sentiment analysis")
        except ImportError:
            print("⚠ SnowNLP not available. Install with:")
            print("  pip install snownlp")

    def analyze(self, text: str) -> Optional[Dict]:
        """
        Analyze sentiment of Chinese text

        Args:
            text: Chinese text to analyze

        Returns:
            Dictionary with sentiment label, score, and confidence
        """
        if not text or not text.strip():
            return None

        if not self.available:
            return self._fallback_sentiment(text)

        try:
            from snownlp import SnowNLP

            s = SnowNLP(text)

            # SnowNLP returns sentiment score from 0 (negative) to 1 (positive)
            sentiment_score = s.sentiments

            # Convert to label and our scoring system
            if sentiment_score > 0.6:
                label = 'positive'
                score = sentiment_score
                confidence = sentiment_score
            elif sentiment_score < 0.4:
                label = 'negative'
                score = -(1 - sentiment_score)  # Negative score
                confidence = 1 - sentiment_score
            else:
                label = 'neutral'
                score = 0.0
                confidence = 0.5

            return {
                'label': label,
                'score': score,
                'confidence': confidence
            }

        except Exception as e:
            print(f"  SnowNLP analysis error: {e}")
            return self._fallback_sentiment(text)

    def _fallback_sentiment(self, text: str) -> Dict:
        """
        Simple keyword-based sentiment for Chinese text

        Returns:
            Dictionary with sentiment data
        """
        # Chinese positive keywords
        positive_words = [
            '增长', '上涨', '盈利', '收益', '成功', '强劲',
            '超预期', '利好', '看涨', '突破', '创新高'
        ]

        # Chinese negative keywords
        negative_words = [
            '下跌', '亏损', '损失', '暴跌', '风险', '警告',
            '调查', '诉讼', '违规', '弱', '看跌', '利空'
        ]

        pos_count = sum(1 for word in positive_words if word in text)
        neg_count = sum(1 for word in negative_words if word in text)

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
        """Analyze sentiment for multiple Chinese texts"""
        results = []
        for text in texts:
            result = self.analyze(text)
            results.append(result)

        return results


def test_analyzer():
    """Test SnowNLP analyzer"""
    analyzer = SnowNLPAnalyzer()

    test_texts = [
        "腾讯第三季度盈利大幅增长，超出市场预期",
        "公司股价暴跌，发布盈利警告",
        "公司宣布推出新产品",
    ]

    print("\nTesting SnowNLP analyzer:")
    for text in test_texts:
        result = analyzer.analyze(text)
        print(f"\nText: {text}")
        print(f"Sentiment: {result['label']} (score: {result['score']:.2f}, confidence: {result['confidence']:.2f})")


if __name__ == "__main__":
    test_analyzer()
