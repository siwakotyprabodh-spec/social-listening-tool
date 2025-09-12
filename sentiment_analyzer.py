#!/usr/bin/env python3
"""
Sentiment Analysis Module for Social Listening Tool
Provides multiple sentiment analysis methods for news content
"""

import re
from typing import Dict, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """Multi-method sentiment analyzer for news content"""
    
    def __init__(self, method='vader'):
        """
        Initialize sentiment analyzer
        
        Args:
            method (str): 'vader', 'textblob', or 'hybrid'
        """
        self.method = method
        self.vader_analyzer = None
        self.textblob_analyzer = None
        
        # Initialize analyzers based on method
        if method in ['vader', 'hybrid']:
            try:
                from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
                self.vader_analyzer = SentimentIntensityAnalyzer()
                logger.info("VADER sentiment analyzer initialized")
            except ImportError:
                logger.warning("VADER not available, falling back to TextBlob")
                method = 'textblob'
        
        if method in ['textblob', 'hybrid']:
            try:
                from textblob import TextBlob
                self.textblob_analyzer = TextBlob
                logger.info("TextBlob sentiment analyzer initialized")
            except ImportError:
                logger.warning("TextBlob not available, falling back to VADER")
                method = 'vader'
        
        # Update method if fallback occurred
        if method == 'hybrid' and not (self.vader_analyzer and self.textblob_analyzer):
            self.method = 'vader' if self.vader_analyzer else 'textblob'
        
        logger.info(f"Sentiment analyzer initialized with method: {self.method}")
    
    def clean_text_for_sentiment(self, text: str) -> str:
        """
        Clean text for better sentiment analysis
        
        Args:
            text (str): Raw text content
            
        Returns:
            str: Cleaned text
        """
        if not text:
            return ""
        
        # Remove HTML tags and special characters
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'[^\w\s\.\,\!\?\-]', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove very short texts (likely not meaningful for sentiment)
        if len(text) < 10:
            return ""
        
        return text
    
    def analyze_sentiment_vader(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment using VADER
        
        Args:
            text (str): Text to analyze
            
        Returns:
            Dict with sentiment scores
        """
        if not self.vader_analyzer:
            return {"error": "VADER analyzer not available"}
        
        try:
            scores = self.vader_analyzer.polarity_scores(text)
            return {
                'compound': scores['compound'],
                'positive': scores['pos'],
                'negative': scores['neg'],
                'neutral': scores['neu']
            }
        except Exception as e:
            logger.error(f"VADER sentiment analysis error: {e}")
            return {"error": str(e)}
    
    def analyze_sentiment_textblob(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment using TextBlob
        
        Args:
            text (str): Text to analyze
            
        Returns:
            Dict with sentiment scores
        """
        if not self.textblob_analyzer:
            return {"error": "TextBlob analyzer not available"}
        
        try:
            blob = self.textblob_analyzer(text)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity
            
            # Convert polarity to compound score (-1 to 1)
            compound = polarity
            
            # Categorize sentiment
            if polarity > 0.1:
                sentiment = "positive"
            elif polarity < -0.1:
                sentiment = "negative"
            else:
                sentiment = "neutral"
            
            return {
                'compound': compound,
                'polarity': polarity,
                'subjectivity': subjectivity,
                'sentiment': sentiment
            }
        except Exception as e:
            logger.error(f"TextBlob sentiment analysis error: {e}")
            return {"error": str(e)}
    
    def analyze_sentiment_hybrid(self, text: str) -> Dict[str, any]:
        """
        Analyze sentiment using both methods and combine results
        
        Args:
            text (str): Text to analyze
            
        Returns:
            Dict with combined sentiment analysis
        """
        if not (self.vader_analyzer and self.textblob_analyzer):
            # Fallback to available method
            if self.vader_analyzer:
                return self.analyze_sentiment_vader(text)
            elif self.textblob_analyzer:
                return self.analyze_sentiment_textblob(text)
            else:
                return {"error": "No sentiment analyzers available"}
        
        try:
            vader_scores = self.analyze_sentiment_vader(text)
            textblob_scores = self.analyze_sentiment_textblob(text)
            
            # Check for errors
            if 'error' in vader_scores or 'error' in textblob_scores:
                # Return the working one
                if 'error' not in vader_scores:
                    return vader_scores
                elif 'error' not in textblob_scores:
                    return textblob_scores
                else:
                    return {"error": "Both analyzers failed"}
            
            # Combine scores (weighted average)
            compound = (vader_scores['compound'] + textblob_scores['compound']) / 2
            
            # Determine overall sentiment
            if compound > 0.1:
                overall_sentiment = "positive"
            elif compound < -0.1:
                overall_sentiment = "negative"
            else:
                overall_sentiment = "neutral"
            
            return {
                'compound': compound,
                'overall_sentiment': overall_sentiment,
                'vader': vader_scores,
                'textblob': textblob_scores,
                'confidence': 'high' if abs(compound) > 0.3 else 'medium'
            }
            
        except Exception as e:
            logger.error(f"Hybrid sentiment analysis error: {e}")
            return {"error": str(e)}
    
    def analyze_sentiment(self, text: str) -> Dict[str, any]:
        """
        Main sentiment analysis method
        
        Args:
            text (str): Text to analyze
            
        Returns:
            Dict with sentiment analysis results
        """
        # Clean text first
        cleaned_text = self.clean_text_for_sentiment(text)
        if not cleaned_text:
            return {
                'sentiment': 'neutral',
                'compound': 0.0,
                'confidence': 'low',
                'error': 'Text too short for meaningful analysis'
            }
        
        # Analyze based on method
        if self.method == 'vader':
            result = self.analyze_sentiment_vader(cleaned_text)
        elif self.method == 'textblob':
            result = self.analyze_sentiment_textblob(cleaned_text)
        elif self.method == 'hybrid':
            result = self.analyze_sentiment_hybrid(cleaned_text)
        else:
            result = {"error": f"Unknown method: {self.method}"}
        
        # Add metadata
        if 'error' not in result:
            result['text_length'] = len(cleaned_text)
            result['method_used'] = self.method
            from datetime import datetime
            result['timestamp'] = str(datetime.now())
        
        return result
    
    def get_sentiment_label(self, compound_score: float) -> str:
        """
        Convert compound score to human-readable label
        
        Args:
            compound_score (float): Sentiment compound score (-1 to 1)
            
        Returns:
            str: Sentiment label
        """
        if compound_score >= 0.05:
            return "Positive"
        elif compound_score <= -0.05:
            return "Negative"
        else:
            return "Neutral"
    
    def get_sentiment_emoji(self, compound_score: float) -> str:
        """
        Get emoji for sentiment score
        
        Args:
            compound_score (float): Sentiment compound score (-1 to 1)
            
        Returns:
            str: Emoji representation
        """
        if compound_score >= 0.05:
            return "😊"
        elif compound_score <= -0.05:
            return "😞"
        else:
            return "😐"

# Convenience function for quick sentiment analysis
def quick_sentiment(text: str, method: str = 'vader') -> Dict[str, any]:
    """
    Quick sentiment analysis function
    
    Args:
        text (str): Text to analyze
        method (str): Analysis method
        
    Returns:
        Dict with sentiment results
    """
    analyzer = SentimentAnalyzer(method=method)
    return analyzer.analyze_sentiment(text)

if __name__ == "__main__":
    # Test the sentiment analyzer
    test_texts = [
        "This is amazing news! I'm so happy about this development.",
        "This is terrible news. I'm very disappointed with the outcome.",
        "The weather is cloudy today. It might rain later.",
        "The company reported record profits and increased market share.",
        "The accident caused significant damage and multiple injuries."
    ]
    
    analyzer = SentimentAnalyzer(method='hybrid')
    
    print("🧠 Sentiment Analysis Test")
    print("=" * 50)
    
    for text in test_texts:
        result = analyzer.analyze_sentiment(text)
        emoji = analyzer.get_sentiment_emoji(result.get('compound', 0))
        label = analyzer.get_sentiment_label(result.get('compound', 0))
        
        print(f"\n📝 Text: {text[:60]}...")
        print(f"🎯 Sentiment: {emoji} {label}")
        print(f"📊 Score: {result.get('compound', 0):.3f}")
        if 'overall_sentiment' in result:
            print(f"🔍 Overall: {result['overall_sentiment']}")
        if 'confidence' in result:
            print(f"💪 Confidence: {result['confidence']}") 