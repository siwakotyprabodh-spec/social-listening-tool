#!/usr/bin/env python3
"""
WSGI entry point for Streamlit app on PythonAnywhere
"""

import sys
import os

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import and run the Streamlit app
if __name__ == "__main__":
    import subprocess
    import sys
    
    # Run streamlit with proper configuration for PythonAnywhere
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", 
        "social_listening_app.py",
        "--server.port=8080",
        "--server.address=0.0.0.0",
        "--server.headless=true",
        "--server.enableCORS=false",
        "--server.enableXsrfProtection=false"
    ])
