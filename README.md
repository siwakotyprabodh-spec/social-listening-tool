# Social Listening Tool with Enhanced AI Translation

## Overview
This tool crawls websites to find content containing specific keywords and translates Nepali content to English using advanced AI translation techniques.

## Recent Improvements

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
   - Normalizes Nepali numbers to English
   - Fixes common Nepali text formatting issues
   - Preserves Nepali characters during processing

4. **Post-processing**: 
   - Fixes punctuation and spacing issues
   - Ensures proper capitalization
   - Removes translation artifacts

5. **Error Handling**: Robust error handling with multiple fallback options

## Installation

### Basic Installation (Translation Only)
1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
streamlit run social_listening_app.py
```

### Advanced Installation (With AI Summarization)
For better summarization quality, install transformers:
```bash
pip install transformers torch
```

**Note**: The application will work without transformers, using a simple fallback summarization method.

## Usage

1. **Upload Data**: Upload a CSV or Excel file containing URLs
2. **Enter Keyword**: Specify the keyword to search for
3. **Set Date Range**: Choose English or Nepali date range
4. **Configure Settings**: Choose from the sidebar:
   - **Translation Quality**: Standard (Fast), High Quality (Slower), or Best Quality (Slowest)
   - **Summary Length**: Short (1 paragraph), Medium (2 paragraphs), or Long (3+ paragraphs)
5. **Crawl Sites**: The tool will crawl sites and find matches
6. **Select Links to Translate**: 
   - Review the crawled results
   - Use bulk selection options (Select All, Select None, Select Recent)
   - Check individual links you want to translate
   - See content length preview for each link
7. **Translate Selected**: Click "Translate Selected Links" to process only chosen content
8. **Save/Load Sessions**: Save your work and load previous sessions

## Translation Quality Tips

- **For News Articles**: Use "High Quality" mode for better sentence structure
- **For Short Content**: "Standard" mode is usually sufficient
- **For Complex Content**: Use "Best Quality" mode for maximum accuracy
- **For Large Datasets**: Start with "Standard" mode to test, then upgrade if needed

## Troubleshooting

If translations are still poor quality:
1. Check that the source text is actually in Nepali
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