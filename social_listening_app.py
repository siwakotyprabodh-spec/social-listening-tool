import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import dateparser
import re
from datetime import datetime
from nepali_datetime import date as nep_date
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.chrome.service import Service
import time
import concurrent.futures
from deep_translator import GoogleTranslator, MyMemoryTranslator
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    print("Warning: transformers pipeline not available. Using fallback summarization.")
    TRANSFORMERS_AVAILABLE = False
import json
from database import DatabaseManager
from login_ui import check_login_status, show_logout

# Initialize translator and summarizer
@st.cache_resource
def load_ai_models():
    # Try multiple translation services for better quality
    translators = []
    
    # Primary: Google Translator (free, reliable)
    try:
        google_translator = GoogleTranslator(source='ne', target='en')
        translators.append(('Google', google_translator))
    except Exception as e:
        print(f"GoogleTranslator failed to initialize: {e}")
    
    # Secondary: MyMemory Translator (free, good fallback)
    try:
        mymemory_translator = MyMemoryTranslator(source='ne', target='en')
        translators.append(('MyMemory', mymemory_translator))
    except Exception as e:
        print(f"MyMemoryTranslator failed to initialize: {e}")
    
    if not translators:
        # Fallback to Google if all else fails
        try:
            google_translator = GoogleTranslator(source='ne', target='en')
            translators.append(('Google', google_translator))
        except Exception as e:
            print(f"All translation services failed to initialize: {e}")
            st.error("Translation services are not available. Please check your internet connection.")
    
    # Initialize summarizer
    if TRANSFORMERS_AVAILABLE:
        try:
            summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        except Exception as e:
            print(f"Transformers summarizer failed to initialize: {e}")
            summarizer = None
    else:
        summarizer = None
    
    return translators, summarizer

def preprocess_text(text):
    """Clean and prepare text for better translation"""
    if not text:
        return ""
    
    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove common HTML artifacts
    text = re.sub(r'&[a-zA-Z]+;', ' ', text)
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # Remove special characters that might confuse translators, but keep Nepali characters
    text = re.sub(r'[^\w\s\.\,\!\?\:\;\-\(\)\[\]\"\'\u0900-\u097F]', ' ', text)
    
    # Ensure proper sentence endings
    text = re.sub(r'([।!?])\s*([a-zA-Z\u0900-\u097F])', r'\1 \2', text)
    
    # Fix common Nepali text issues
    # Remove extra spaces around Nepali punctuation
    text = re.sub(r'\s+([।!?])\s*', r'\1 ', text)
    
    # Normalize Nepali numbers to English if present
    nepali_to_english_numbers = {
        '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
        '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'
    }
    for nepali, english in nepali_to_english_numbers.items():
        text = text.replace(nepali, english)
    
    return text.strip()

def postprocess_translation(translated_text):
    """Improve the quality of translated text"""
    if not translated_text:
        return translated_text
    
    # Fix common translation issues
    # Remove extra spaces
    translated_text = re.sub(r'\s+', ' ', translated_text.strip())
    
    # Fix common punctuation issues
    translated_text = re.sub(r'\s+([.,!?;:])', r'\1', translated_text)
    
    # Ensure proper capitalization
    sentences = translated_text.split('. ')
    corrected_sentences = []
    for sentence in sentences:
        if sentence:
            sentence = sentence.strip()
            if sentence and sentence[0].isalpha():
                sentence = sentence[0].upper() + sentence[1:]
            corrected_sentences.append(sentence)
    
    return '. '.join(corrected_sentences)

def simple_summarize(text, max_length=300, min_length=150):
    """Simple summarization when transformers is not available"""
    if not text:
        return text
    
    # Split into sentences
    sentences = text.split('. ')
    
    # Simple heuristics for summarization
    if len(sentences) <= 3:
        return text
    
    # Take first few sentences and last sentence
    summary_sentences = sentences[:2]  # First 2 sentences
    
    # Add last sentence if it's different from the first ones
    if len(sentences) > 3 and sentences[-1] not in summary_sentences:
        summary_sentences.append(sentences[-1])
    
    summary = '. '.join(summary_sentences)
    
    # Ensure proper ending
    if not summary.endswith('.'):
        summary += '.'
    
    # Limit length
    if len(summary) > max_length:
        summary = summary[:max_length-3] + '...'
    
    return summary

def extract_news_content_from_soup(soup):
    """Extract main news content from a BeautifulSoup object"""
    try:
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Try to find main content areas
        content_selectors = [
            'article', '.article-content', '.news-content', '.post-content',
            '.entry-content', '.content', 'main', '.main-content'
        ]
        
        content = None
        for selector in content_selectors:
            content = soup.select_one(selector)
            if content:
                break
        
        if not content:
            # Fallback: get all text from body
            content = soup.find('body')
        
        if content:
            # Get text and clean it
            text = content.get_text(separator=' ', strip=True)
            # Remove extra whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            return text[:2000]  # Limit to first 2000 characters
        return None
    except Exception as e:
        print(f"[ERROR] Failed to extract content from soup: {e}")
        return None

def extract_news_content(url):
    """Extract main news content from a URL"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return None
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        return extract_news_content_from_soup(soup)
    except Exception as e:
        print(f"[ERROR] Failed to extract content from {url}: {e}")
        return None

def translate_with_fallback(text, translators, quality_mode='Standard (Fast)'):
    """Translate text using multiple services with fallback"""
    if not text or len(text.strip()) < 10:
        return "Content too short to translate"
    
    # Preprocess the text
    cleaned_text = preprocess_text(text)
    
    # Split text into sentences for better translation if using high quality mode
    if quality_mode in ['High Quality (Slower)', 'Best Quality (Slowest)']:
        # Split by Nepali sentence endings and other punctuation
        sentences = re.split(r'[।!?]+', cleaned_text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) > 1:
            translated_sentences = []
            for sentence in sentences:
                if len(sentence) < 5:  # Skip very short sentences
                    continue
                    
                # Try each translator for each sentence
                sentence_translated = False
                for service_name, translator in translators:
                    try:
                        translated_sentence = translator.translate(sentence)
                        if len(translated_sentence) > 3:
                            translated_sentences.append(translated_sentence)
                            sentence_translated = True
                            break
                    except Exception:
                        continue
                
                if not sentence_translated:
                    # If translation fails, keep original sentence
                    translated_sentences.append(sentence)
            
            # Combine sentences
            combined_translation = ' '.join(translated_sentences)
            return postprocess_translation(combined_translation)
    
    # Standard mode: translate entire text at once
    for service_name, translator in translators:
        try:
            print(f"Attempting translation with {service_name}...")
            translated = translator.translate(cleaned_text)
            
            # Post-process the translation
            improved_translation = postprocess_translation(translated)
            
            # Basic quality check
            if len(improved_translation) > 10 and not improved_translation.isupper():
                print(f"Successfully translated with {service_name}")
                return improved_translation
            else:
                print(f"{service_name} produced poor quality translation, trying next...")
                continue
                
        except Exception as e:
            print(f"{service_name} translation failed: {e}")
            continue
    
    # If all translators fail, return a message
    return "Translation failed - could not process content"

def translate_and_summarize(text, translators, summarizer, quality_mode='Standard (Fast)', summary_length='Medium (2 paragraphs)'):
    """Translate Nepali text to English and generate summary"""
    try:
        if not text or len(text.strip()) < 50:
            return "Content too short to process"
        
        # Translate to English with fallback
        english_text = translate_with_fallback(text, translators, quality_mode)
        
        if english_text in ["Content too short to translate", "Translation failed - could not process content"]:
            return english_text
        
        if len(english_text) < 100:
            return english_text
        
        # Configure summary parameters based on length preference
        if summary_length == 'Short (1 paragraph)':
            max_len = 150
            min_len = 80
            target_paragraphs = 1
        elif summary_length == 'Medium (2 paragraphs)':
            max_len = 300
            min_len = 150
            target_paragraphs = 2
        else:  # Long (3+ paragraphs)
            max_len = 450
            min_len = 250
            target_paragraphs = 3
        
        # Summarize the translated text
        try:
            if summarizer and TRANSFORMERS_AVAILABLE:
                # Use transformers summarizer
                summary = summarizer(
                    english_text, 
                    max_length=max_len,
                    min_length=min_len,
                    do_sample=False,
                    num_beams=4,     # Better quality generation
                    length_penalty=1.0,  # Encourage longer summaries
                    early_stopping=True
                )
                
                summary_text = summary[0]['summary_text']
            else:
                # Use fallback summarization
                summary_text = simple_summarize(english_text, max_len, min_len)
            
            # Format into paragraphs based on target
            if target_paragraphs > 1 and len(summary_text) > 150:
                sentences = summary_text.split('. ')
                if len(sentences) >= target_paragraphs * 2:  # Need at least 2 sentences per paragraph
                    if target_paragraphs == 2:
                        # Create two paragraphs
                        mid_point = len(sentences) // 2
                        para1 = '. '.join(sentences[:mid_point]) + '.'
                        para2 = '. '.join(sentences[mid_point:])
                        if not para2.endswith('.'):
                            para2 += '.'
                        return f"{para1}\n\n{para2}"
                    elif target_paragraphs >= 3:
                        # Create three or more paragraphs
                        sentences_per_para = len(sentences) // target_paragraphs
                        paragraphs = []
                        for i in range(target_paragraphs):
                            start_idx = i * sentences_per_para
                            end_idx = start_idx + sentences_per_para if i < target_paragraphs - 1 else len(sentences)
                            para = '. '.join(sentences[start_idx:end_idx])
                            if not para.endswith('.'):
                                para += '.'
                            paragraphs.append(para)
                        return '\n\n'.join(paragraphs)
            
            return summary_text
            
        except Exception as e:
            print(f"Summarization failed, returning translation: {e}")
            return english_text
            
    except Exception as e:
        print(f"[ERROR] Translation/summarization failed: {e}")
        return "Failed to process content"

# Nepali months
NEPALI_MONTHS = ['बैशाख', 'जेठ', 'असार', 'श्रावण', 'भदौ', 'आश्विन', 'कार्तिक', 'मंसिर', 'पुष', 'माघ', 'फाल्गुण', 'चैत्र']

# Helper to get internal links
def get_internal_links(base_url, soup):
    links = set()
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        joined = urljoin(base_url, href)
        if urlparse(joined).netloc == urlparse(base_url).netloc:
            links.add(joined)
    return links

# Helper to parse Nepali date string like '६ साउन २०८२' to Gregorian
def parse_nepali_date_string(date_str):
    try:
        parts = date_str.strip().split()
        if len(parts) != 3:
            return None
        day = int(parts[0])
        month = NEPALI_MONTHS.index(parts[1]) + 1
        year = int(parts[2])
        nepali_date = nep_date(year, month, day)
        return nepali_date.to_datetime_date()
    except Exception:
        return None

# Helper to extract date from page
def extract_date(soup):
    for tag in ['article:published_time', 'date', 'pubdate', 'publishdate', 'timestamp', 'dc.date', 'dcterms.created']:
        meta = soup.find('meta', attrs={'name': tag}) or soup.find('meta', attrs={'property': tag})
        if meta and meta.get('content'):
            dt = dateparser.parse(meta['content'])
            if dt:
                return dt, meta['content']
    for time_tag in soup.find_all('time'):
        if time_tag.get('datetime'):
            dt = dateparser.parse(time_tag['datetime'])
            if dt:
                return dt, time_tag['datetime']
        if time_tag.text:
            dt = dateparser.parse(time_tag.text)
            if dt:
                return dt, time_tag.text
    text = soup.get_text()
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
    if date_match:
        dt = dateparser.parse(date_match.group(1))
        if dt:
            return dt, date_match.group(1)
    nepali_date_match = re.search(r'(\d{1,2} [\u0900-\u097F]+ \d{4})', soup.get_text())
    if nepali_date_match:
        nepali_greg = parse_nepali_date_string(nepali_date_match.group(1))
        return nepali_greg, nepali_date_match.group(1)
    return None, None

def check_keywords(page_text, keywords, logic):
    """Check if page text contains keywords based on logic (AND/OR)"""
    if not keywords:
        return False
    if logic == 'AND':
        return all(kw.lower() in page_text.lower() for kw in keywords)
    else:
        return any(kw.lower() in page_text.lower() for kw in keywords)

def crawl_site_requests(start_url, keywords, logic, date_from, date_to, max_pages=100, save_html=False, site_timeout=120):
    visited = set()
    to_visit = [start_url]
    matches = []
    debug_rows = []
    page_num = 0
    start_time = time.time()
    while to_visit and len(visited) < max_pages:
        if time.time() - start_time > site_timeout:
            print(f"[TIMEOUT] Site {start_url} reached {site_timeout} seconds, skipping to next site.")
            break
        url = to_visit.pop(0)
        if url in visited:
            print(f"[SKIP] Already visited: {url}")
            continue
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                print(f"[SKIP] Non-200 status: {url}")
                continue
            resp.encoding = 'utf-8'
            html = resp.text
            soup = BeautifulSoup(html, 'html.parser')
            page_text = soup.get_text(separator=' ', strip=True)
            keyword_found = check_keywords(page_text, keywords, logic)
            page_date, raw_date = extract_date(soup)
            
            # Extract content during crawl to avoid re-crawling later
            extracted_content = None
            if keyword_found:
                extracted_content = extract_news_content_from_soup(soup)
                print(f"[DEBUG] Extracted content length for {url}: {len(extracted_content) if extracted_content else 0} characters")
            
            if save_html:
                with open(f'rendered_page_{page_num}.html', 'w', encoding='utf-8') as f:
                    f.write(html)
            debug_rows.append({
                'url': url,
                'keyword_found': keyword_found,
                'date': page_date.strftime('%Y-%m-%d') if page_date else 'Unknown',
                'raw_date': raw_date if raw_date else 'N/A'
            })
            print(f"[DEBUG] {url} | Keyword found: {keyword_found} | Extracted date: {page_date} | Raw: {raw_date}")
            if keyword_found:
                if page_date:
                    if date_from and page_date < date_from:
                        pass
                    elif date_to and page_date > date_to:
                        pass
                    else:
                        matches.append({
                            'url': url, 
                            'date': page_date.strftime('%Y-%m-%d') if page_date else 'Unknown', 
                            'raw_date': raw_date if raw_date else 'N/A',
                            'content': extracted_content  # Store content during crawl
                        })
                        print(f"[DEBUG] Stored content for {url}: {len(extracted_content) if extracted_content else 0} characters")
                else:
                    matches.append({
                        'url': url, 
                        'date': page_date.strftime('%Y-%m-%d') if page_date else 'Unknown', 
                        'raw_date': raw_date if raw_date else 'N/A',
                        'content': extracted_content  # Store content during crawl
                    })
                    print(f"[DEBUG] Stored content for {url}: {len(extracted_content) if extracted_content else 0} characters")
            for link in get_internal_links(start_url, soup):
                if link not in visited and link not in to_visit:
                    to_visit.append(link)
            page_num += 1
        except Exception as e:
            print(f"[ERROR] {url} | {e}")
            continue
        visited.add(url)
    return matches, debug_rows

# Progress bar for Streamlit
from contextlib import contextmanager
def stqdm(seq, desc=None):
    import time
    total = len(seq)
    my_bar = st.progress(0)
    for i, item in enumerate(seq):
        yield item
        my_bar.progress((i+1)/total)
        time.sleep(0.01)
    my_bar.empty()

def main():
    # Set page configuration for wider layout
    st.set_page_config(
        page_title="Social Listening Tool",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Show translation service status
    if 'translation_status_shown' not in st.session_state:
        st.session_state.translation_status_shown = True
        with st.expander("ℹ️ Translation Services Status", expanded=False):
            st.info("""
            **Translation Services:**
            - **Google Translator**: Free, reliable, no API key required
            - **MyMemory Translator**: Free, good fallback option
            
            The app will automatically use available services with fallback options.
            """)
    
    # Check login status first
    if not check_login_status():
        return  # Stop execution if not logged in
    
    # Add custom CSS for better styling and wider layout
    st.markdown("""
    <style>
    /* Increase main content width */
    .main .block-container {
        max-width: 1400px;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        padding-top: 0rem;
    }
    
    .main-header {
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 30px;
    }
    
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
        margin: 10px 0;
    }
    
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #c3e6cb;
    }
    
    .warning-message {
        background-color: #fff3cd;
        color: #856404;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #ffeaa7;
    }
    
    .info-message {
        background-color: #d1ecf1;
        color: #0c5460;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #bee5eb;
    }
    
    /* User info styling */
    .user-info {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .logout-button {
        background: linear-gradient(135deg, #ff6b6b, #ee5a24);
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .logout-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    /* Preferences styling */
    .preferences-section {
        background: linear-gradient(135deg, #74b9ff, #0984e3);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Show logout button in sidebar
    show_logout()
    
    # Load user preferences
    db = DatabaseManager()
    user_prefs = db.get_user_preferences(st.session_state.user_id)
    
    # User preferences panel with beautiful styling
    st.sidebar.markdown("""
    <div class="preferences-section">
        <div style="display: flex; align-items: center; margin-bottom: 15px;">
            <span style="font-size: 20px; margin-right: 8px;">⚙️</span>
            <span style="font-weight: bold; font-size: 16px;">User Preferences</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.sidebar.expander("🔧 Configure Settings", expanded=False):
        if user_prefs:
            translation_quality = st.selectbox(
                '🌐 Translation Quality',
                ['Standard (Fast)', 'High Quality (Slower)', 'Best Quality (Slowest)'],
                index=['Standard (Fast)', 'High Quality (Slower)', 'Best Quality (Slowest)'].index(user_prefs['translation_quality']),
                help="Choose translation quality. Higher quality takes longer but produces better results."
            )
            summary_length = st.selectbox(
                '📝 Summary Length',
                ['Short (1 paragraph)', 'Medium (2 paragraphs)', 'Long (3+ paragraphs)'],
                index=['Short (1 paragraph)', 'Medium (2 paragraphs)', 'Long (3+ paragraphs)'].index(user_prefs['summary_length']),
                help="Choose how detailed you want the summaries to be."
            )
            max_crawl_pages = st.number_input(
                '🕷️ Max Crawl Pages', 
                min_value=10, 
                max_value=500, 
                value=user_prefs['max_crawl_pages'],
                help="Maximum number of pages to crawl per website"
            )
            crawl_timeout = st.number_input(
                '⏱️ Crawl Timeout (seconds)', 
                min_value=30, 
                max_value=300, 
                value=user_prefs['crawl_timeout'],
                help="Maximum time to spend crawling each website"
            )
        else:
            translation_quality = st.selectbox(
                '🌐 Translation Quality', 
                ['Standard (Fast)', 'High Quality (Slower)', 'Best Quality (Slowest)'],
                help="Choose translation quality. Higher quality takes longer but produces better results."
            )
            summary_length = st.selectbox(
                '📝 Summary Length', 
                ['Short (1 paragraph)', 'Medium (2 paragraphs)', 'Long (3+ paragraphs)'],
                help="Choose how detailed you want the summaries to be."
            )
            max_crawl_pages = st.number_input(
                '🕷️ Max Crawl Pages', 
                min_value=10, 
                max_value=500, 
                value=100,
                help="Maximum number of pages to crawl per website"
            )
            crawl_timeout = st.number_input(
                '⏱️ Crawl Timeout (seconds)', 
                min_value=30, 
                max_value=300, 
                value=120,
                help="Maximum time to spend crawling each website"
            )
        
        # Save button with better styling
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("💾 Save Preferences", help="Save your current preferences"):
                preferences = {
                    'translation_quality': translation_quality,
                    'summary_length': summary_length,
                    'max_crawl_pages': max_crawl_pages,
                    'crawl_timeout': crawl_timeout
                }
                if db.save_user_preferences(st.session_state.user_id, preferences):
                    st.success("✅ Preferences saved!")
                else:
                    st.error("❌ Failed to save preferences!")
        with col2:
            st.markdown("**Settings applied**")
    
    # Main header with better styling using custom CSS
    st.markdown("""
    <div class="main-header">
        <h1 style="color: white; text-align: center; margin-bottom: 10px;">🔍 Social Listening Tool</h1>
        <p style="color: white; text-align: center; font-size: 16px; margin-bottom: 0;">
            Monitor and analyze Nepali social media content with AI-powered translation and summarization
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # File upload section with better styling
    st.markdown("### 📁 Upload Data")
    st.markdown("Upload a CSV or Excel file containing URLs to analyze:")

    # Initialize session state
    if 'crawled_results' not in st.session_state:
        st.session_state.crawled_results = None
    if 'debug_rows_all' not in st.session_state:
        st.session_state.debug_rows_all = None
    if 'keyword' not in st.session_state:
        st.session_state.keyword = None
    if 'filter_from' not in st.session_state:
        st.session_state.filter_from = None
    if 'filter_to' not in st.session_state:
        st.session_state.filter_to = None

    # Use translation settings from user preferences
    translation_mode = translation_quality
    summary_length = summary_length
    
    # Load AI models
    with st.spinner('Loading AI models...'):
        translators, summarizer = load_ai_models()

    uploaded_file = st.file_uploader(
        'Choose a CSV or Excel file',
        type=['csv', 'xlsx'],
        help='File should contain a column with URLs to analyze'
    )
    # --- Multiple Keyword Input Section ---
    if 'keywords' not in st.session_state:
        st.session_state.keywords = ["", "", "", "", ""]
    if 'search_logic' not in st.session_state:
        st.session_state.search_logic = 'AND'

    # Keywords section with better styling
    st.sidebar.markdown("### 🔍 Search Keywords")
    st.sidebar.markdown("Add up to 5 keywords to search for:")
    
    # Keyword inputs with better styling
    for i in range(5):
        st.session_state.keywords[i] = st.sidebar.text_input(
            f"Keyword {i+1}", 
            value=st.session_state.keywords[i], 
            key=f"kw_{i}",
            placeholder=f"Enter keyword {i+1}",
            help=f"Enter keyword {i+1} to search for"
        )
    
    # Search logic with better styling
    st.sidebar.markdown("**Search Logic:**")
    st.session_state.search_logic = st.sidebar.radio(
        'Logic', 
        ['AND', 'OR'], 
        index=0 if st.session_state.search_logic=='AND' else 1,
        help='AND: All keywords must be present | OR: Any keyword can be present'
    )
    
    # Clear button with better styling
    if st.sidebar.button('🗑️ Clear All Keywords', help='Clear all keywords'):
        st.session_state.keywords = ["", "", "", "", ""]

    # Helper to get active keywords (automatically detect based on text input)
    def get_active_keywords():
        return [kw for kw in st.session_state.keywords if kw.strip()]

    # --- Replace old keyword input ---
    active_keywords = get_active_keywords()
    search_logic = st.session_state.search_logic
    if not active_keywords:
        st.warning('Please enter and activate at least one keyword.')
        return

    # --- Multiple keyword search logic is now handled by the check_keywords function ---
    # The crawl_site_requests function now accepts keywords and logic parameters
    # and uses the check_keywords function to determine if a page matches

    # Date range section with better styling
    st.markdown("---")
    st.markdown("### 📅 Date Range Filter")
    st.markdown("Choose either English or Nepali calendar dates (optional):")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**🌍 English Calendar**")
        date_from = st.date_input(
            'From date (optional)', 
            value=None, 
            key='eng_from',
            help='Start date for filtering results'
        )
        date_to = st.date_input(
            'To date (optional)', 
            value=None, 
            key='eng_to',
            help='End date for filtering results'
        )
    
    with col2:
        st.markdown("**🇳🇵 Nepali Calendar**")
        nep_years = list(range(2070, 2091))
        nep_months = NEPALI_MONTHS
        nep_days = list(range(1, 33))
        
        st.markdown("**From date:**")
        nep_from_year = st.selectbox(
            'Year', 
            nep_years, 
            index=nep_years.index(2082), 
            key='nep_from_year',
            help='Nepali year'
        )
        nep_from_month = st.selectbox(
            'Month', 
            nep_months, 
            index=2, 
            key='nep_from_month',
            help='Nepali month'
        )
        nep_from_day = st.selectbox(
            'Day', 
            nep_days, 
            index=0, 
            key='nep_from_day',
            help='Nepali day'
        )
        
        st.markdown("**To date:**")
        nep_to_year = st.selectbox(
            'Year ', 
            nep_years, 
            index=nep_years.index(2082), 
            key='nep_to_year',
            help='Nepali year'
        )
        nep_to_month = st.selectbox(
            'Month ', 
            nep_months, 
            index=2, 
            key='nep_to_month',
            help='Nepali month'
        )
        nep_to_day = st.selectbox(
            'Day ', 
            nep_days, 
            index=0, 
            key='nep_to_day',
            help='Nepali day'
        )

    # Convert Nepali dates if selected
    nepali_from_greg = nep_date(nep_from_year, nep_months.index(nep_from_month)+1, nep_from_day).to_datetime_date() if nep_from_year and nep_from_month and nep_from_day else None
    nepali_to_greg = nep_date(nep_to_year, nep_months.index(nep_to_month)+1, nep_to_day).to_datetime_date() if nep_to_year and nep_to_month and nep_to_day else None

    # Use Nepali date if selected, else English
    filter_from = nepali_from_greg if nepali_from_greg else (pd.to_datetime(date_from) if date_from else None)
    filter_to = nepali_to_greg if nepali_to_greg else (pd.to_datetime(date_to) if date_to else None)

    # Check if we already have crawled results
    if st.session_state.crawled_results is not None:
        st.success("✅ Using previously crawled results. Upload a new file or change settings to re-crawl.")
        results = st.session_state.crawled_results
        debug_rows_all = st.session_state.debug_rows_all
        keyword = st.session_state.keyword
        filter_from = st.session_state.filter_from
        filter_to = st.session_state.filter_to
    if uploaded_file and active_keywords:
        # Initialize variables
        results = []
        debug_rows_all = []
        urls = []
        results_placeholder = st.empty()  # Placeholder for real-time results
        
        # Check if we already have results for this keyword and date range
        if (st.session_state.crawled_results is not None and 
            st.session_state.keyword == active_keywords and
            st.session_state.filter_from == filter_from and
            st.session_state.filter_to == filter_to):
            
            st.success("Using cached results from previous crawl!")
            results = st.session_state.crawled_results
            debug_rows_all = st.session_state.debug_rows_all
        else:
            # New crawl needed
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            url_col = None
            for col in df.columns:
                if 'url' in col.lower() or 'domain' in col.lower():
                    url_col = col
                    break
            if not url_col:
                url_col = df.columns[0]
            urls = df[url_col].dropna().unique().tolist()
            # Ensure URLs start with http:// or https://
            def ensure_http(url):
                if not url.startswith('http://') and not url.startswith('https://'):
                    return 'http://' + url
                return url
            urls = [ensure_http(u) for u in urls]
            st.write(f'Found {len(urls)} URLs to check.')
        
        # Crawl buttons with better styling
        st.markdown("### 🚀 Start Analysis")
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            start_crawl = st.button(
                "🚀 Start Crawl", 
                type="primary",
                help="Begin crawling the uploaded URLs for content matching your keywords"
            )
        
        with col2:
            if st.session_state.crawled_results is not None:
                re_crawl = st.button(
                    "🔄 Re-crawl", 
                    help="Re-crawl all sites with current settings"
                )
            else:
                re_crawl = False
        
        with col3:
            st.markdown(f"**URLs to analyze:** {len(urls)}")
        
        # Start crawling when button is clicked
        if (start_crawl or re_crawl) and urls:
            with st.spinner('Crawling sites...'):
                for url in stqdm(urls, desc='Crawling sites'):
                    st.write(f'Crawling site: {url}')
                    print(f'[START] Crawling site: {url}')
                    site_start_time = time.time()
                    try:
                        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                            future = executor.submit(crawl_site_requests, url, active_keywords, search_logic, filter_from, filter_to, 100, False, 120)
                            try:
                                matches, debug_rows = future.result(timeout=130)
                            except concurrent.futures.TimeoutError:
                                st.write(f"[TIMEOUT] Crawling {url} exceeded 2 minutes, skipping to next site.")
                                print(f"[TIMEOUT] Crawling {url} exceeded 2 minutes, skipping to next site.")
                                continue
                        results.extend(matches)
                        debug_rows_all.extend(debug_rows)
                        # Update results in real time
                        if results:
                            results_df = pd.DataFrame(results)
                            results_placeholder.write('### Results (updating...)')
                            results_placeholder.dataframe(results_df)
                        site_end_time = time.time()
                        elapsed = site_end_time - site_start_time
                        st.write(f'Finished crawling: {url} (Time taken: {elapsed:.2f} seconds)')
                        print(f'[FINISH] Crawling site: {url} (Time taken: {elapsed:.2f} seconds)')
                    except Exception as e:
                        st.write(f"[ERROR] Crawling {url} failed: {e}")
                        print(f"[ERROR] Crawling {url} failed: {e}")
                        continue
            
            # Store results in session state to avoid re-crawling
            st.session_state.crawled_results = results
            st.session_state.debug_rows_all = debug_rows_all
            st.session_state.keyword = active_keywords
            st.session_state.filter_from = filter_from
            st.session_state.filter_to = filter_to
        
        # Show initial results without translation
        if not results and not (start_crawl or re_crawl):
            st.info("📋 Ready to crawl! Upload a file, set your keywords, and click 'Start Crawl' to begin.")
        
        if results:
            # Results header with better styling
            st.markdown("### 📊 Analysis Results")
            st.markdown(f"**Found {len(results)} matching pages**")
            
            # Create DataFrame and ensure content column is included
            results_df = pd.DataFrame(results)
            results_df['Visit Link'] = results_df['url'].apply(lambda x: f'[Visit Link]({x})')
            
            # Debug: Check if content is in the DataFrame
            print(f"[DEBUG] DataFrame columns: {results_df.columns.tolist()}")
            print(f"[DEBUG] Number of results with content: {sum(1 for r in results if r.get('content'))}")
            
            # Show debug info to user in a collapsible section
            with st.expander("🔍 Debug Information"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Total results:** {len(results)}")
                    st.write(f"**Results with content:** {sum(1 for r in results if r.get('content'))}")
                    st.write(f"**Using cached results:** {st.session_state.crawled_results is not None}")
                with col2:
                    st.write(f"**DataFrame columns:** {results_df.columns.tolist()}")
                    if results:
                        st.write(f"**First result content length:** {len(results[0].get('content', ''))}")
                
                # Add clear cache button
                if st.button("🗑️ Clear Cache & Re-crawl", help="Clear cached results and start fresh"):
                    st.session_state.crawled_results = None
                    st.session_state.debug_rows_all = None
                    st.session_state.keyword = None
                    st.session_state.filter_from = None
                    st.session_state.filter_to = None
                    st.rerun()
            
            # Selection instructions
            st.markdown("**Select the pages you want to translate and summarize:**")
            
            # Initialize selected_indices first
            selected_indices = []
            
            # Bulk selection options with better styling
            st.markdown("**Quick Selection:**")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                select_all = st.button("✅ Select All", help="Select all results")
            with col2:
                select_none = st.button("❌ Select None", help="Deselect all results")
            with col3:
                select_recent = st.button("🕒 Select Recent (Last 5)", help="Select the 5 most recent results")
            with col4:
                st.markdown(f"**Selected:** {len(selected_indices)} items")
            
            # Handle bulk selection outside form to avoid re-execution
            if select_all:
                selected_indices = list(range(len(results_df)))
            elif select_none:
                selected_indices = []
            elif select_recent:
                selected_indices = list(range(min(5, len(results_df))))
            
            # Create a form for selection
            with st.form("translation_selection"):
                # Display results in a more organized way with better column layout
                for i, row in results_df.iterrows():
                    # Create a container for each result with better spacing
                    with st.container():
                        # Use better column proportions: Select | URL/Info | Content Preview | Actions
                        col1, col2, col3, col4 = st.columns([0.08, 0.35, 0.42, 0.15])
                        
                        with col1:
                            # Pre-select based on bulk actions
                            default_value = i in selected_indices
                            if st.checkbox("", key=f"select_{i}", value=default_value, help=f"Select result {i+1}"):
                                selected_indices.append(i)
                        
                        with col2:
                            # URL and date information
                            display_url = row['url']
                            if len(display_url) > 50:
                                display_url = display_url[:50] + "..."
                            st.markdown(f"**{display_url}**")
                            st.markdown(f"📅 **{row['date']}**")
                        
                        with col3:
                            # Content preview with better formatting
                            if i < len(results):
                                content = results[i].get('content')
                                if content:
                                    # Show first 100 characters of content
                                    preview = content[:100] + "..." if len(content) > 100 else content
                                    st.markdown(f"📄 **Content Preview:**")
                                    st.markdown(f"*{preview}*")
                                    
                                    # Show content length indicator
                                    content_length = len(content)
                                    if content_length > 1000:
                                        st.markdown("🟢 **Long content**")
                                    elif content_length > 500:
                                        st.markdown("🟡 **Medium content**")
                                    else:
                                        st.markdown("🔴 **Short content**")
                                else:
                                    st.markdown("❌ **No content available**")
                            else:
                                st.markdown("❓ **Unknown**")
                        
                        with col4:
                            # Action buttons
                            st.markdown(f"[🔗 Visit]({row['url']})", unsafe_allow_html=True)
                            if i < len(results) and results[i].get('content'):
                                st.markdown("✅ **Ready to translate**")
                            else:
                                st.markdown("⚠️ **No content**")
                        
                        # Add separator between results
                        st.markdown("---")
                
                # Translation options with better styling
                st.markdown("---")
                st.markdown("### 🌐 Translation & Summarization")
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    translate_selected = st.form_submit_button(
                        "🚀 Translate & Summarize Selected", 
                        type="primary",
                        help="Translate Nepali content to English and generate summaries"
                    )
                with col2:
                    st.markdown(f"**Selected:** {len(selected_indices)} items")
                with col3:
                    if selected_indices:
                        st.markdown("✅ **Ready to process**")
                    else:
                        st.markdown("⚠️ **No items selected**")
            
            # Process selected results with AI translation and summarization
            if translate_selected and selected_indices:
                st.markdown("### 🤖 AI Processing")
                st.markdown("**Translating and summarizing selected content...**")
                processed_results = []
                
                # Create progress bar for selected items
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for idx, i in enumerate(selected_indices):
                    result = results[i].copy()
                    status_text.text(f'Processing {idx + 1}/{len(selected_indices)}: {result["url"][:50]}...')
                    
                    # Use stored content from crawl - NO RE-CRAWLING
                    content = result.get('content')
                    print(f"[DEBUG] Translation: Content for {result['url']}: {'Available' if content else 'NOT AVAILABLE'}")
                    if content:
                        # Translate and summarize
                        summary = translate_and_summarize(content, translators, summarizer, translation_mode, summary_length)
                        result['Summary (English)'] = summary
                    else:
                        # No fallback - content should have been stored during crawl
                        result['Summary (English)'] = "No content available (was not stored during crawl)"
                        print(f"[WARNING] No content stored for {result['url']}")
                    processed_results.append(result)
                    
                    # Update progress
                    progress_bar.progress((idx + 1) / len(selected_indices))
                
                progress_bar.empty()
                status_text.empty()
                
                # Display processed results with better styling
                if processed_results:
                    processed_df = pd.DataFrame(processed_results)
                    processed_df['Visit Link'] = processed_df['url'].apply(lambda x: f'[Visit Link]({x})')
                    
                    st.markdown("### 📋 Translation Results")
                    st.markdown(f"**Successfully processed {len(processed_results)} items**")
                    
                    # Display results in a better format
                    for i, result in enumerate(processed_results):
                        with st.expander(f"📄 Result {i+1}: {result['url'][:50]}...", expanded=True):
                            col1, col2 = st.columns([1, 1])
                            with col1:
                                st.markdown("**🔗 Original URL:**")
                                st.markdown(f"[{result['url']}]({result['url']})")
                                st.markdown(f"**📅 Date:** {result['date']}")
                                st.markdown(f"**📊 Content Length:** {len(result.get('content', ''))} characters")
                            
                            with col2:
                                st.markdown("**🌐 English Summary:**")
                                st.markdown(f"*{result['Summary (English)']}*")
                    
                    # Download options
                    st.markdown("### 💾 Download Results")
                    col1, col2 = st.columns(2)
                    with col1:
                        csv = processed_df.drop(columns=['Visit Link']).to_csv(index=False)
                        st.download_button(
                            '📥 Download as CSV', 
                            data=csv, 
                            file_name='translated_results.csv', 
                            mime='text/csv',
                            help="Download results as CSV file"
                        )
                    with col2:
                        # Create a formatted text report
                        report = "TRANSLATION RESULTS REPORT\n"
                        report += "=" * 50 + "\n\n"
                        for i, result in enumerate(processed_results, 1):
                            report += f"Result {i}:\n"
                            report += f"URL: {result['url']}\n"
                            report += f"Date: {result['date']}\n"
                            report += f"Summary: {result['Summary (English)']}\n"
                            report += "-" * 30 + "\n\n"
                        
                        st.download_button(
                            '📄 Download as Text Report', 
                            data=report, 
                            file_name='translation_report.txt', 
                            mime='text/plain',
                            help="Download results as formatted text report"
                        )
                    
                    # Show extracted dates for debugging in collapsible section
                    with st.expander("🔍 Debug: Raw Date Information"):
                        debug_df = pd.DataFrame(processed_results)[['url', 'raw_date']]
                        st.dataframe(debug_df)
            
            elif translate_selected and not selected_indices:
                st.warning("⚠️ **Please select at least one item to translate and summarize.**")
            
            # Show debug table for all crawled pages in collapsible section
            if debug_rows_all:
                with st.expander("🔍 Debug: All Crawled Pages"):
                    debug_df = pd.DataFrame(debug_rows_all)
                    st.markdown(f"**Total pages crawled:** {len(debug_df)}")
                    st.dataframe(debug_df)
            
            # Session management
            st.write("---")
            st.write("### Session Management")
            col1, col2 = st.columns(2)
            
            with col1:
                # Save session
                if st.button("💾 Save Session"):
                    # Clean results for saving (remove content to reduce file size)
                    clean_results = []
                    for result in results:
                        clean_result = result.copy()
                        if 'content' in clean_result:
                            del clean_result['content']  # Remove content to save space
                        clean_results.append(clean_result)
                    
                    session_data = {
                        'results': clean_results,
                        'keyword': keyword,
                        'date_from': str(filter_from) if filter_from else None,
                        'date_to': str(filter_to) if filter_to else None,
                        'timestamp': datetime.now().isoformat()
                    }
                    session_json = json.dumps(session_data, default=str)
                    st.download_button(
                        "Download Session File",
                        data=session_json,
                        file_name=f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
            
            with col2:
                # Load session
                uploaded_session = st.file_uploader("Load Previous Session", type=['json'])
                if uploaded_session:
                    try:
                        session_data = json.load(uploaded_session)
                        st.success(f"Session loaded from {session_data.get('timestamp', 'unknown time')}")
                        st.write(f"Keyword: {session_data.get('keyword', 'N/A')}")
                        st.write(f"Date range: {session_data.get('date_from', 'N/A')} to {session_data.get('date_to', 'N/A')}")
                        st.write(f"Results: {len(session_data.get('results', []))} links")
                    except Exception as e:
                        st.error(f"Failed to load session: {e}")
        else:
            results_placeholder.write('No matches found.')
        # Show debug table for all crawled pages
        if debug_rows_all:
            debug_df = pd.DataFrame(debug_rows_all)
            st.write('#### Debug: All Crawled Pages')
            st.dataframe(debug_df)
    else:
        st.write('Please upload a file and enter a keyword.')

if __name__ == '__main__':
    main() 