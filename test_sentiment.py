#!/usr/bin/env python3
"""
Test script for sentiment analysis functionality
"""

from sentiment_analyzer import SentimentAnalyzer, quick_sentiment

def test_sentiment_analysis():
    """Test the sentiment analyzer with various text samples"""
    
    print("🧠 Testing Sentiment Analysis")
    print("=" * 50)
    
    # Test texts in different languages and sentiments
    test_texts = [
        {
            "text": "This is amazing news! I'm so happy about this development.",
            "expected": "positive",
            "language": "English"
        },
        {
            "text": "This is terrible news. I'm very disappointed with the outcome.",
            "expected": "negative", 
            "language": "English"
        },
        {
            "text": "The weather is cloudy today. It might rain later.",
            "expected": "neutral",
            "language": "English"
        },
        {
            "text": "The company reported record profits and increased market share.",
            "expected": "positive",
            "language": "English"
        },
        {
            "text": "The accident caused significant damage and multiple injuries.",
            "expected": "negative",
            "language": "English"
        },
        {
            "text": "¡Esta es una noticia muy buena! Estoy muy feliz con esto.",
            "expected": "positive",
            "language": "Spanish"
        },
        {
            "text": "Esta es una noticia muy mala. Estoy muy decepcionado con el resultado.",
            "expected": "negative",
            "language": "Spanish"
        }
    ]
    
    # Test different methods
    methods = ['vader', 'textblob', 'hybrid']
    
    for method in methods:
        print(f"\n🔧 Testing {method.upper()} method:")
        print("-" * 30)
        
        analyzer = SentimentAnalyzer(method=method)
        
        for test_case in test_texts:
            text = test_case["text"]
            expected = test_case["expected"]
            language = test_case["language"]
            
            try:
                result = analyzer.analyze_sentiment(text)
                
                if 'error' not in result:
                    compound_score = result.get('compound', 0)
                    sentiment_label = analyzer.get_sentiment_label(compound_score)
                    emoji = analyzer.get_sentiment_emoji(compound_score)
                    
                    # Check if prediction matches expected
                    status = "✅" if sentiment_label.lower() == expected else "❌"
                    
                    print(f"{status} {language}: {emoji} {sentiment_label} (Score: {compound_score:.3f})")
                    print(f"   Text: {text[:50]}...")
                    
                    # Show additional details for hybrid method
                    if method == 'hybrid' and 'overall_sentiment' in result:
                        print(f"   Overall: {result['overall_sentiment']} (Confidence: {result.get('confidence', 'N/A')})")
                    
                else:
                    print(f"❌ Error: {result['error']}")
                    
            except Exception as e:
                print(f"❌ Exception: {e}")
        
        print()
    
    # Test quick sentiment function
    print("🚀 Testing Quick Sentiment Function:")
    print("-" * 30)
    
    quick_text = "This is a fantastic development that will benefit everyone!"
    quick_result = quick_sentiment(quick_text, method='vader')
    
    if 'error' not in quick_result:
        print(f"✅ Quick analysis: {quick_result.get('compound', 0):.3f}")
    else:
        print(f"❌ Quick analysis failed: {quick_result['error']}")

if __name__ == "__main__":
    test_sentiment_analysis() 