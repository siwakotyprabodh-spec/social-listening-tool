#!/usr/bin/env python3
"""
Test script for sentiment filtering functionality
"""

from sentiment_analyzer import SentimentAnalyzer

def test_sentiment_filtering():
    """Test the sentiment filtering functions"""
    
    print("🧠 Testing Sentiment Filtering Functions")
    print("=" * 50)
    
    # Create sample results with sentiment data
    sample_results = [
        {
            'url': 'https://example1.com',
            'content': 'This is amazing news! I love it!',
            'sentiment': {'compound': 0.8, 'positive': 0.8, 'negative': 0.0, 'neutral': 0.2}
        },
        {
            'url': 'https://example2.com',
            'content': 'This is terrible news. I hate it!',
            'sentiment': {'compound': -0.9, 'positive': 0.0, 'negative': 0.9, 'neutral': 0.1}
        },
        {
            'url': 'https://example3.com',
            'content': 'The weather is cloudy today.',
            'sentiment': {'compound': 0.0, 'positive': 0.0, 'negative': 0.0, 'neutral': 1.0}
        },
        {
            'url': 'https://example4.com',
            'content': 'Great success in the market!',
            'sentiment': {'compound': 0.6, 'positive': 0.6, 'negative': 0.0, 'neutral': 0.4}
        },
        {
            'url': 'https://example5.com',
            'content': 'No sentiment data available',
            'sentiment': None
        }
    ]
    
    # Test filtering by sentiment category
    print("\n🔍 Testing Category Filtering:")
    print("-" * 30)
    
    # Test positive filter
    positive_results = filter_results_by_sentiment(sample_results, "Positive", -1.0, 1.0)
    print(f"Positive results: {len(positive_results)}")
    for result in positive_results:
        print(f"  - {result['url']}: {result['sentiment']['compound']:.2f}")
    
    # Test negative filter
    negative_results = filter_results_by_sentiment(sample_results, "Negative", -1.0, 1.0)
    print(f"Negative results: {len(negative_results)}")
    for result in negative_results:
        print(f"  - {result['url']}: {result['sentiment']['compound']:.2f}")
    
    # Test neutral filter
    neutral_results = filter_results_by_sentiment(sample_results, "Neutral", -1.0, 1.0)
    print(f"Neutral results: {len(neutral_results)}")
    for result in neutral_results:
        print(f"  - {result['url']}: {result['sentiment']['compound']:.2f}")
    
    # Test score range filtering
    print("\n📊 Testing Score Range Filtering:")
    print("-" * 30)
    
    # Test high positive scores only
    high_positive = filter_results_by_sentiment(sample_results, "All", 0.5, 1.0)
    print(f"High positive scores (0.5-1.0): {len(high_positive)}")
    for result in high_positive:
        print(f"  - {result['url']}: {result['sentiment']['compound']:.2f}")
    
    # Test negative scores only
    negative_scores = filter_results_by_sentiment(sample_results, "All", -1.0, -0.5)
    print(f"Negative scores (-1.0 to -0.5): {len(negative_scores)}")
    for result in negative_scores:
        print(f"  - {result['url']}: {result['sentiment']['compound']:.2f}")
    
    # Test combined filtering
    print("\n🎯 Testing Combined Filtering:")
    print("-" * 30)
    
    # Positive sentiment with score > 0.5
    combined_filter = filter_results_by_sentiment(sample_results, "Positive", 0.5, 1.0)
    print(f"Positive + High Score (>0.5): {len(combined_filter)}")
    for result in combined_filter:
        print(f"  - {result['url']}: {result['sentiment']['compound']:.2f}")
    
    print("\n✅ Sentiment filtering tests completed!")

def filter_results_by_sentiment(results, sentiment_category="All", min_score=-1.0, max_score=1.0):
    """
    Filter results based on sentiment analysis
    
    Args:
        results (list): List of result dictionaries
        sentiment_category (str): "All", "Positive", "Negative", or "Neutral"
        min_score (float): Minimum sentiment score (-1.0 to 1.0)
        max_score (float): Maximum sentiment score (-1.0 to 1.0)
    
    Returns:
        list: Filtered results
    """
    if not results:
        return []
    
    filtered = []
    
    for result in results:
        # Check if result has sentiment data
        if 'sentiment' not in result or not result['sentiment']:
            # If no sentiment data and we're not filtering by category, include it
            if sentiment_category == "All":
                filtered.append(result)
            continue
        
        sentiment_data = result['sentiment']
        
        # Skip if sentiment analysis failed
        if 'error' in sentiment_data:
            if sentiment_category == "All":
                filtered.append(result)
            continue
        
        # Get compound score
        compound_score = sentiment_data.get('compound', 0.0)
        
        # Apply score range filter
        if compound_score < min_score or compound_score > max_score:
            continue
        
        # Apply category filter
        if sentiment_category != "All":
            if sentiment_category == "Positive" and compound_score <= 0.05:
                continue
            elif sentiment_category == "Negative" and compound_score >= -0.05:
                continue
            elif sentiment_category == "Neutral" and (compound_score > 0.05 or compound_score < -0.05):
                continue
        
        filtered.append(result)
    
    return filtered

if __name__ == "__main__":
    test_sentiment_filtering() 