#!/usr/bin/env python3
"""
WSGI configuration for PythonAnywhere deployment
"""

import sys
import os

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import the Streamlit app
from social_listening_app import app

# This is the WSGI application that PythonAnywhere will use
application = app
