# Social Listening Tool with Enhanced AI Translation

## Overview
This tool crawls websites to find content containing specific keywords and translates content to English using advanced AI translation techniques.

## Recent Improvements

### 🧠 Sentiment Analysis Integration
- **Automatic Sentiment Detection**: Analyze sentiment of crawled news content automatically
- **Multiple Analysis Methods**: Choose from VADER (fast), TextBlob (balanced), or Hybrid (most accurate)
- **Real-time Sentiment Display**: See sentiment scores and labels for each result
- **Sentiment Summary Dashboard**: View overall sentiment statistics and distribution charts
- **Multi-language Support**: Works with content in various languages
- **Configurable Settings**: Enable/disable sentiment analysis and choose your preferred method

### Selective Translation System
- **Choose What to Translate**: Select specific links instead of translating everything
- **Bulk Selection Options**: Select All, Select None, or Select Recent (last 5)
- **Content Preview**: See content length before deciding to translate
- **Session Management**: Save and load your work sessions
- **Progress Tracking**: Real-time progress bar during translation
- **Optimized Performance**: Content extracted during crawl, no re-crawling during translation

### Enhanced Translation Quality
The translation system has been significantly improved with the following features:

1. **Multiple Translation Services**: Uses Google Translator and MyMemory Translator with automatic fallback
2. **Quality Modes**: Three translation quality options:
   - **Standard (Fast)**: Quick translation of entire text
   - **High Quality (Slower)**: Sentence-by-sentence translation for better accuracy
   - **Best Quality (Slowest)**: Advanced sentence processing with multiple fallbacks

### Improved Summarization
3. **Configurable Summary Length**: Three summary length options:
   - **Short (1 paragraph)**: 80-150 characters, single paragraph
   - **Medium (2 paragraphs)**: 150-300 characters, two paragraphs (default)
   - **Long (3+ paragraphs)**: 250-450 characters, three or more paragraphs
4. **Smart Paragraph Formatting**: Automatically splits summaries into natural paragraphs
5. **Better Quality Generation**: Uses beam search and length penalty for improved summaries

3. **Text Preprocessing**: 
   - Cleans HTML artifacts and special characters
   - Normalizes numbers to English
- Fixes common text formatting issues
- Preserves special characters during processing

4. **Post-processing**: 
   - Fixes punctuation and spacing issues
   - Ensures proper capitalization
   - Removes translation artifacts

5. **Error Handling**: Robust error handling with multiple fallback options

## Installation

### Basic Installation (Translation + Sentiment Analysis)
1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
streamlit run social_listening_app.py
```

**Note**: The sentiment analysis packages (textblob, vaderSentiment, plotly) are included in requirements.txt and will be installed automatically.

### Advanced Installation (With AI Summarization)
For better summarization quality, install transformers:
```bash
pip install transformers torch
```

**Note**: The application will work without transformers, using a simple fallback summarization method.

## Usage

1. **Upload Data**: Upload a CSV or Excel file containing URLs
2. **Enter Keyword**: Specify the keyword to search for
3. **Set Date Range**: Choose date range for filtering
4. **Configure Settings**: Choose from the sidebar:
   - **Translation Quality**: Standard (Fast), High Quality (Slower), or Best Quality (Slowest)
   - **Summary Length**: Short (1 paragraph), Medium (2 paragraphs), or Long (3+ paragraphs)
   - **Sentiment Analysis**: Enable/disable and choose method (VADER, TextBlob, or Hybrid)
5. **Crawl Sites**: The tool will crawl sites and find matches
6. **Select Links to Translate**: 
   - Review the crawled results
   - Use bulk selection options (Select All, Select None, Select Recent)
   - Check individual links you want to translate
   - See content length preview for each link
7. **Translate Selected**: Click "Translate Selected Links" to process only chosen content
8. **Save/Load Sessions**: Save your work and load previous sessions

## Sentiment Analysis Features

### Analysis Methods
- **VADER**: Fast and effective for social media content, handles emojis and slang well
- **TextBlob**: Balanced approach with subjectivity analysis, good for formal content
- **Hybrid**: Combines both methods for highest accuracy and confidence scoring

### Sentiment Display
- **Individual Results**: Each crawled result shows sentiment score and label
- **Summary Dashboard**: Overall statistics with positive/negative/neutral counts
- **Visual Charts**: Pie charts showing sentiment distribution (requires plotly)
- **Score Range**: -1.0 (very negative) to +1.0 (very positive)

### Sentiment Filtering
- **Category Filtering**: Filter by Positive, Negative, or Neutral sentiment
- **Score Range Filtering**: Set minimum and maximum sentiment scores (-1.0 to +1.0)
- **Quick Filter Buttons**: One-click filtering for common sentiment categories
- **Combined Filtering**: Apply both category and score range filters simultaneously
- **Real-time Updates**: See filtered results immediately in the interface

### Best Practices
- **For News Monitoring**: Use VADER method for fast analysis of large volumes
- **For Detailed Analysis**: Use Hybrid method for highest accuracy
- **For Social Media**: VADER handles informal language and emojis best
- **For Reports**: TextBlob provides additional subjectivity insights
- **For Filtering**: Start with category filters, then refine with score ranges

## Translation Quality Tips

- **For News Articles**: Use "High Quality" mode for better sentence structure
- **For Short Content**: "Standard" mode is usually sufficient
- **For Complex Content**: Use "Best Quality" mode for maximum accuracy
- **For Large Datasets**: Start with "Standard" mode to test, then upgrade if needed

## Troubleshooting

If translations are still poor quality:
1. Check that the source text is in the expected language
2. Try different quality modes
3. Ensure the text is not too short (minimum 50 characters)
4. Check the console output for translation service errors

## Technical Details

The translation system uses:
- **Google Translator**: Primary service (free, reliable)
- **Google Translator**: Secondary service
- **MyMemory Translator**: Tertiary service
- **Sentence-by-sentence processing**: For high-quality modes
- **Automatic fallback**: If one service fails, tries the next

## File Structure
- `social_listening_app.py`: Main application
- `requirements.txt`: Python dependencies
- `README.md`: This documentation 