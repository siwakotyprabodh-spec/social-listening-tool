from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import dateparser
import re
from datetime import datetime
import time
import concurrent.futures
import json
import os
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
import traceback

# Import your existing modules
try:
    from database import DatabaseManager
    from sentiment_analyzer import SentimentAnalyzer
    from deep_translator import GoogleTranslator, MyMemoryTranslator
    SENTIMENT_AVAILABLE = True
    TRANSFORMERS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Some modules not available: {e}")
    SENTIMENT_AVAILABLE = False
    TRANSFORMERS_AVAILABLE = False

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'xlsx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize database
db = DatabaseManager()

# Initialize sentiment analyzer
sentiment_analyzer = SentimentAnalyzer() if SENTIMENT_AVAILABLE else None

# Global variables for AI models
translators = []
summarizer = None

def login_required(f):
    """Decorator to require login for certain routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def load_ai_models():
    """Load AI models for translation and summarization"""
    global translators, summarizer
    
    # Initialize translators
    try:
        google_translator = GoogleTranslator(source='ne', target='en')
        translators.append(('Google', google_translator))
    except Exception as e:
        print(f"GoogleTranslator failed to initialize: {e}")
    
    try:
        mymemory_translator = MyMemoryTranslator(source='ne', target='en')
        translators.append(('MyMemory', mymemory_translator))
    except Exception as e:
        print(f"MyMemoryTranslator failed to initialize: {e}")
    
    # Initialize summarizer
    if TRANSFORMERS_AVAILABLE:
        try:
            from transformers import pipeline
            summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        except Exception as e:
            print(f"Transformers summarizer failed to initialize: {e}")
            summarizer = None

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def preprocess_text(text):
    """Clean and prepare text for better translation"""
    if not text:
        return ""
    
    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove common HTML artifacts
    text = re.sub(r'&[a-zA-Z]+;', ' ', text)
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # Remove special characters that might confuse translators
    text = re.sub(r'[^\w\s\.\,\!\?\:\;\-\(\)\[\]\"\']', ' ', text)
    
    # Ensure proper sentence endings
    text = re.sub(r'([.!?])\s*([a-zA-Z])', r'\1 \2', text)
    
    return text.strip()

def postprocess_translation(translated_text):
    """Improve the quality of translated text"""
    if not translated_text:
        return ""
    
    # Fix common translation issues
    translated_text = re.sub(r'\s+', ' ', translated_text.strip())
    translated_text = re.sub(r'([.!?])\s*([a-zA-Z])', r'\1 \2', translated_text)
    
    # Ensure proper capitalization
    sentences = re.split(r'([.!?]+)', translated_text)
    result = ""
    for i, part in enumerate(sentences):
        if i == 0 or (i > 0 and sentences[i-1] and sentences[i-1][-1] in '.!?'):
            result += part.capitalize()
        else:
            result += part
    
    return result.strip()

def translate_text(text, quality_mode='Standard'):
    """Translate text using available translators"""
    if not text or not translators:
        return text
    
    processed_text = preprocess_text(text)
    if not processed_text:
        return text
    
    for service_name, translator in translators:
        try:
            if quality_mode == 'Standard (Fast)':
                # Simple translation
                translated = translator.translate(processed_text)
            elif quality_mode == 'High Quality (Slower)':
                # Sentence by sentence translation
                sentences = re.split(r'([.!?]+)', processed_text)
                translated_parts = []
                for sentence in sentences:
                    if sentence.strip() and not re.match(r'^[.!?]+$', sentence):
                        try:
                            translated_part = translator.translate(sentence)
                            translated_parts.append(translated_part)
                        except:
                            translated_parts.append(sentence)
                    else:
                        translated_parts.append(sentence)
                translated = ''.join(translated_parts)
            else:  # Best Quality
                # Advanced processing with multiple attempts
                try:
                    translated = translator.translate(processed_text)
                    # If translation seems poor, try sentence by sentence
                    if len(translated) < len(processed_text) * 0.3:
                        sentences = re.split(r'([.!?]+)', processed_text)
                        translated_parts = []
                        for sentence in sentences:
                            if sentence.strip() and not re.match(r'^[.!?]+$', sentence):
                                try:
                                    translated_part = translator.translate(sentence)
                                    translated_parts.append(translated_part)
                                except:
                                    translated_parts.append(sentence)
                            else:
                                translated_parts.append(sentence)
                        translated = ''.join(translated_parts)
                except:
                    # Fallback to simple translation
                    translated = translator.translate(processed_text)
            
            if translated and translated != processed_text:
                return postprocess_translation(translated)
        except Exception as e:
            print(f"Translation failed with {service_name}: {e}")
            continue
    
    return text

def summarize_text(text, length='Medium'):
    """Summarize text using AI or fallback method"""
    if not text or len(text) < 100:
        return text
    
    if summarizer:
        try:
            # Calculate target length based on setting
            if length == 'Short (1 paragraph)':
                max_length = 100
                min_length = 50
            elif length == 'Medium (2 paragraphs)':
                max_length = 200
                min_length = 100
            else:  # Long
                max_length = 300
                min_length = 150
            
            # Truncate text if too long for summarizer
            if len(text) > 1000:
                text = text[:1000] + "..."
            
            summary = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
            
            if isinstance(summary, list) and len(summary) > 0:
                summary_text = summary[0]['summary_text']
                # Format into paragraphs
                sentences = re.split(r'([.!?]+)', summary_text)
                paragraphs = []
                current_paragraph = ""
                
                for sentence in sentences:
                    if sentence.strip():
                        current_paragraph += sentence
                        if sentence.strip()[-1] in '.!?' and len(current_paragraph) > 50:
                            paragraphs.append(current_paragraph.strip())
                            current_paragraph = ""
                
                if current_paragraph.strip():
                    paragraphs.append(current_paragraph.strip())
                
                return '\n\n'.join(paragraphs)
            else:
                return text
        except Exception as e:
            print(f"Summarization failed: {e}")
    
    # Fallback summarization
    sentences = text.split('.')
    if len(sentences) > 3:
        # Take first few sentences
        if length == 'Short (1 paragraph)':
            return '. '.join(sentences[:2]) + '.'
        elif length == 'Medium (2 paragraphs)':
            mid = len(sentences) // 2
            return '. '.join(sentences[:mid]) + '.\n\n' + '. '.join(sentences[mid:mid+2]) + '.'
        else:  # Long
            third = len(sentences) // 3
            return '. '.join(sentences[:third]) + '.\n\n' + '. '.join(sentences[third:third*2]) + '.\n\n' + '. '.join(sentences[third*2:third*3]) + '.'
    
    return text

# Routes
@app.route('/')
@login_required
def index():
    """Main dashboard"""
    user_prefs = db.get_user_preferences(session['user_id']) if 'user_id' in session else None
    return render_template('index.html', user_prefs=user_prefs)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = db.get_user_by_username(username)
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form.get('email', '')
        
        # Check if user already exists
        if db.get_user_by_username(username):
            flash('Username already exists', 'error')
            return render_template('register.html')
        
        # Create new user
        password_hash = generate_password_hash(password)
        if db.create_user(username, password_hash, email):
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Registration failed', 'error')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """Handle file upload"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process file and extract URLs
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(filepath)
            else:
                df = pd.read_excel(filepath)
            
            # Find URL column
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
            
            # Store in session
            session['uploaded_urls'] = urls
            session['uploaded_filename'] = filename
            
            return jsonify({
                'success': True,
                'urls': urls,
                'count': len(urls),
                'filename': filename
            })
            
        except Exception as e:
            return jsonify({'error': f'Error processing file: {str(e)}'}), 400
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/crawl', methods=['POST'])
@login_required
def crawl_sites():
    """Start crawling process"""
    try:
        data = request.get_json()
        keywords = data.get('keywords', [])
        search_logic = data.get('search_logic', 'AND')
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        max_pages = data.get('max_pages', 100)
        enable_sentiment = data.get('enable_sentiment', True)
        sentiment_method = data.get('sentiment_method', 'vader')
        
        urls = session.get('uploaded_urls', [])
        if not urls:
            return jsonify({'error': 'No URLs uploaded'}), 400
        
        if not keywords:
            return jsonify({'error': 'No keywords provided'}), 400
        
        # Start crawling in background (simplified for demo)
        results = []
        
        # This is a simplified version - you'd want to implement the full crawl_site_requests function
        for url in urls[:5]:  # Limit to 5 URLs for demo
            try:
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    text = soup.get_text()
                    
                    # Check if keywords are found
                    found_keywords = []
                    for keyword in keywords:
                        if keyword.lower() in text.lower():
                            found_keywords.append(keyword)
                    
                    if found_keywords:
                        # Simple sentiment analysis
                        sentiment_result = {'compound': 0, 'label': 'neutral'}
                        if enable_sentiment and sentiment_analyzer:
                            try:
                                sentiment_result = sentiment_analyzer.analyze_sentiment(text[:1000])
                            except:
                                pass
                        
                        results.append({
                            'url': url,
                            'date': datetime.now().strftime('%Y-%m-%d'),
                            'content': text[:500] + '...' if len(text) > 500 else text,
                            'sentiment': sentiment_result,
                            'keywords_found': found_keywords
                        })
            except Exception as e:
                print(f"Error crawling {url}: {e}")
                continue
        
        session['crawl_results'] = results
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results)
        })
        
    except Exception as e:
        return jsonify({'error': f'Crawling failed: {str(e)}'}), 500

@app.route('/translate', methods=['POST'])
@login_required
def translate_content():
    """Translate and summarize selected content"""
    try:
        data = request.get_json()
        selected_indices = data.get('selected_indices', [])
        translation_quality = data.get('translation_quality', 'Standard (Fast)')
        summary_length = data.get('summary_length', 'Medium (2 paragraphs)')
        
        results = session.get('crawl_results', [])
        if not results:
            return jsonify({'error': 'No crawl results available'}), 400
        
        translated_results = []
        
        for idx in selected_indices:
            if idx < len(results):
                result = results[idx].copy()
                content = result.get('content', '')
                
                if content:
                    # Translate
                    translated_content = translate_text(content, translation_quality)
                    result['translated_content'] = translated_content
                    
                    # Summarize
                    summary = summarize_text(translated_content, summary_length)
                    result['summary'] = summary
                
                translated_results.append(result)
        
        session['translated_results'] = translated_results
        return jsonify({
            'success': True,
            'results': translated_results
        })
        
    except Exception as e:
        return jsonify({'error': f'Translation failed: {str(e)}'}), 500

@app.route('/preferences', methods=['GET', 'POST'])
@login_required
def preferences():
    """User preferences management"""
    if request.method == 'POST':
        data = request.get_json()
        preferences = {
            'translation_quality': data.get('translation_quality', 'Standard (Fast)'),
            'summary_length': data.get('summary_length', 'Medium (2 paragraphs)'),
            'max_crawl_pages': data.get('max_crawl_pages', 100),
            'crawl_timeout': data.get('crawl_timeout', 120),
            'sentiment_method': data.get('sentiment_method', 'vader'),
            'enable_sentiment': data.get('enable_sentiment', True)
        }
        
        if db.save_user_preferences(session['user_id'], preferences):
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to save preferences'}), 500
    
    # GET request - return current preferences
    user_prefs = db.get_user_preferences(session['user_id'])
    return jsonify(user_prefs or {})

@app.route('/results')
@login_required
def results():
    """Display results page"""
    crawl_results = session.get('crawl_results', [])
    translated_results = session.get('translated_results', [])
    
    return render_template('results.html', 
                         crawl_results=crawl_results,
                         translated_results=translated_results)

if __name__ == '__main__':
    # Load AI models on startup
    load_ai_models()
    app.run(debug=True)
