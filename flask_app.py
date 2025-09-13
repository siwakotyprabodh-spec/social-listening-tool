#!/usr/bin/env python3
"""
Flask version of Social Listening Tool for PythonAnywhere deployment
Integrated with all Streamlit features
"""

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
try:
    db = DatabaseManager()
except Exception as e:
    print(f"Warning: Database not available: {e}")
    db = None

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
def index():
    """Main dashboard - check if user is logged in"""
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # User is logged in, show full dashboard
    user_prefs = db.get_user_preferences(session['user_id']) if db else None
    return render_template('index.html', user_prefs=user_prefs)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if db:
            user = db.get_user_by_username(username)
            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                flash('Login successful!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password', 'error')
        else:
            flash('Database not available', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form.get('email', '')
        
        if not db:
            flash('Database not available', 'error')
            return render_template('register.html')
        
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

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Social Listening Tool is running',
        'version': '2.0.0',
        'features': {
            'database': db is not None,
            'sentiment_analysis': SENTIMENT_AVAILABLE,
            'translation': len(translators) > 0,
            'summarization': summarizer is not None
        }
    })

@app.route('/demo')
def demo():
    """Demo endpoint showing all features"""
    return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Demo - Social Listening Tool</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-4">
        <div class="text-center mb-4">
            <h1><i class="fas fa-play-circle"></i> Demo Mode</h1>
            <p class="lead">Try out the social listening features</p>
        </div>
        
        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-upload"></i> File Upload Demo</h5>
                    </div>
                    <div class="card-body">
                        <p>Upload a CSV or Excel file with URLs to analyze.</p>
                        <div class="mb-3">
                            <input type="file" class="form-control" accept=".csv,.xlsx">
                        </div>
                        <button class="btn btn-primary">Upload File</button>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-search"></i> Keyword Search Demo</h5>
                    </div>
                    <div class="card-body">
                        <p>Enter keywords to search for in the content.</p>
                        <div class="mb-3">
                            <input type="text" class="form-control" placeholder="Enter keywords">
                        </div>
                        <button class="btn btn-success">Search</button>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="mt-4">
            <div class="card">
                <div class="card-header">
                    <h5><i class="fas fa-chart-bar"></i> Sample Results</h5>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-striped">
                            <thead>
                                <tr>
                                    <th>URL</th>
                                    <th>Date</th>
                                    <th>Sentiment</th>
                                    <th>Keywords</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td><a href="#" target="_blank">https://example1.com</a></td>
                                    <td>2024-01-15</td>
                                    <td><span class="badge bg-success">Positive</span></td>
                                    <td>technology, innovation</td>
                                </tr>
                                <tr>
                                    <td><a href="#" target="_blank">https://example2.com</a></td>
                                    <td>2024-01-14</td>
                                    <td><span class="badge bg-warning">Neutral</span></td>
                                    <td>business, market</td>
                                </tr>
                                <tr>
                                    <td><a href="#" target="_blank">https://example3.com</a></td>
                                    <td>2024-01-13</td>
                                    <td><span class="badge bg-danger">Negative</span></td>
                                    <td>crisis, challenge</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="text-center mt-4">
            <a href="/" class="btn btn-outline-primary">
                <i class="fas fa-arrow-left"></i> Back to Home
            </a>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
    """)

if __name__ == '__main__':
    # Load AI models on startup
    load_ai_models()
    app.run(debug=True)