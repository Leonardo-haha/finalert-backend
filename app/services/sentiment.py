"""
Sentiment Analysis Service

Provides NLP-based sentiment scoring for news articles.
Uses TextBlob for sentiment analysis with custom enhancements.
"""

from textblob import TextBlob
from typing import List, Dict, Tuple
import re


class SentimentAnalyzer:
    """
    Sentiment analysis engine using TextBlob with enhancements.
    Provides scores from -1.0 (very negative) to 1.0 (very positive).
    """

    # Keywords that indicate strong sentiment for each instrument
    INSTRUMENT_KEYWORDS = {
        "gold": [
            "gold", "xau", "precious metals", "safe haven", "bullion",
            "fed", "inflation", "dollar weakness", "central bank",
            "rate cut", "rate hike", "monetary policy"
        ],
        "dxy": [
            "dollar", "dxy", "usd", "federal reserve", "fed",
            "treasury", "bond yields", "exchange rate", "currency",
            "us economy", "usd strength", "usd weakness"
        ],
        "oil": [
            "oil", "crude", "wti", "brent", "opec", "energy",
            "petroleum", "natural gas", "supply", "demand",
            "inventories", "production", "sanctions"
        ]
    }

    # Strong sentiment keywords
    STRONG_BULLISH_KEYWORDS = [
        "surge", "rally", "soar", "jump", "gain", "rise", "increase",
        "growth", "bullish", "optimistic", "strong", "record high",
        "breakthrough", "boom", "rallying"
    ]

    STRONG_BEARISH_KEYWORDS = [
        "plunge", "crash", "drop", "fall", "decline", "decrease",
        "loss", "bearish", "pessimistic", "weak", "record low",
        "breakdown", "bust", "slump", "concern", "worried"
    ]

    # Economic event keywords
    ECONOMIC_KEYWORDS = [
        "gdp", "unemployment", "inflation", "cpi", "jobs report",
        "manufacturing", "pmi", "trade war", "tariffs", "sanctions",
        "election", "fed meeting", "central bank", "geopolitical"
    ]

    def __init__(self):
        """Initialize the sentiment analyzer."""
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile regex patterns for efficiency."""
        self.bullish_pattern = re.compile(
            r'\b(' + '|'.join(self.STRONG_BULLISH_KEYWORDS) + r')\b',
            re.IGNORECASE
        )
        self.bearish_pattern = re.compile(
            r'\b(' + '|'.join(self.STRONG_BEARISH_KEYWORDS) + r')\b',
            re.IGNORECASE
        )

    def analyze(self, text: str) -> Dict:
        """
        Analyze sentiment of given text.

        Args:
            text: Text to analyze (headline + summary)

        Returns:
            Dictionary with sentiment_score, sentiment_level, and detected_instruments
        """
        if not text:
            return {
                "sentiment_score": 0.0,
                "sentiment_level": "neutral",
                "confidence": 0.0,
                "detected_instruments": []
            }

        # Get base sentiment from TextBlob
        blob = TextBlob(text)
        base_polarity = blob.sentiment.polarity  # -1 to 1
        subjectivity = blob.sentiment.subjectivity  # 0 to 1

        # Adjust sentiment based on strong keywords
        adjusted_score = base_polarity
        confidence = 1.0 - subjectivity

        # Check for strong bullish keywords
        bullish_matches = len(self.bullish_pattern.findall(text))
        if bullish_matches > 0:
            # Boost positive sentiment
            boost = min(bullish_matches * 0.15, 0.4)
            adjusted_score = min(adjusted_score + boost, 1.0)
            confidence += 0.1

        # Check for strong bearish keywords
        bearish_matches = len(self.bearish_pattern.findall(text))
        if bearish_matches > 0:
            # Boost negative sentiment
            boost = min(bearish_matches * 0.15, 0.4)
            adjusted_score = max(adjusted_score - boost, -1.0)
            confidence += 0.1

        # Clamp final score
        adjusted_score = max(-1.0, min(1.0, adjusted_score))
        confidence = max(0.0, min(1.0, confidence))

        # Determine sentiment level
        if adjusted_score > 0.2:
            sentiment_level = "positive"
        elif adjusted_score < -0.2:
            sentiment_level = "negative"
        else:
            sentiment_level = "neutral"

        # Detect related instruments
        detected_instruments = self._detect_instruments(text)

        return {
            "sentiment_score": round(adjusted_score, 3),
            "sentiment_level": sentiment_level,
            "confidence": round(confidence, 3),
            "detected_instruments": detected_instruments,
            "base_polarity": round(base_polarity, 3),
            "subjectivity": round(subjectivity, 3),
            "bullish_signals": bullish_matches,
            "bearish_signals": bearish_matches,
            "economic_signals": len(re.findall(r'\b(' + '|'.join(self.ECONOMIC_KEYWORDS) + r')\b', text.lower()))
        }

    def _detect_instruments(self, text: str) -> List[str]:
        """
        Detect which instruments the text relates to.

        Args:
            text: Text to analyze

        Returns:
            List of detected instrument names
        """
        text_lower = text.lower()
        detected = []

        for instrument, keywords in self.INSTRUMENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    if instrument not in detected:
                        detected.append(instrument)
                    break

        return detected

    def calculate_impact_score(self, sentiment_result: Dict, text: str) -> int:
        """
        Calculate impact score (0-100) based on sentiment and content.

        Args:
            sentiment_result: Result from analyze() method
            text: Original text

        Returns:
            Impact score from 0 to 100
        """
        base_score = 50

        # Sentiment contribution (up to 30 points)
        sentiment_contribution = abs(sentiment_result["sentiment_score"]) * 30

        # Confidence contribution (up to 20 points)
        confidence_contribution = sentiment_result["confidence"] * 20

        # Strong signals contribution (up to 25 points)
        strong_signals = sentiment_result.get("bullish_signals", 0) + sentiment_result.get("bearish_signals", 0)
        signals_contribution = min(strong_signals * 5, 25)

        # Economic signals contribution (up to 15 points)
        economic_contribution = min(sentiment_result.get("economic_signals", 0) * 5, 15)

        # Instrument relevance (up to 10 points)
        instrument_contribution = len(sentiment_result["detected_instruments"]) * 3

        total_score = (
            base_score +
            sentiment_contribution +
            confidence_contribution +
            signals_contribution +
            economic_contribution +
            instrument_contribution
        )

        return max(0, min(100, int(total_score)))

    def extract_tags(self, text: str) -> List[str]:
        """
        Extract relevant tags from text.

        Args:
            text: Text to analyze

        Returns:
            List of extracted tags
        """
        tags = []

        # Extract mentioned instruments
        tags.extend(self._detect_instruments(text))

        # Extract economic terms
        text_lower = text.lower()
        for keyword in self.ECONOMIC_KEYWORDS:
            if keyword in text_lower:
                tags.append(keyword.upper())

        return list(set(tags))[:10]  # Limit to 10 tags


# Global instance for reuse
sentiment_analyzer = SentimentAnalyzer()
