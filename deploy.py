#!/usr/bin/env python3
"""
Deployment Helper Script for Social Listening Tool
This script helps test your deployment setup and provides guidance.
"""

import os
import sys
import subprocess
import importlib.util

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} detected. Python 3.8+ required.")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible!")
    return True

def check_dependencies():
    """Check if all required packages are installed"""
    print("\n📦 Checking dependencies...")
    required_packages = [
        'streamlit', 'pandas', 'requests', 'beautifulsoup4', 
        'deep_translator', 'bcrypt', 'mysql.connector'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            importlib.import_module(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - Missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies installed!")
    return True

def check_database_connection():
    """Test database connection"""
    print("\n🗄️  Testing database connection...")
    try:
        from database import DatabaseManager
        db = DatabaseManager()
        if db.connect():
            print("✅ Database connection successful!")
            db.disconnect()
            return True
        else:
            print("❌ Database connection failed!")
            return False
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def check_environment_variables():
    """Check environment variables"""
    print("\n🔧 Checking environment variables...")
    env_vars = ['MYSQL_HOST', 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DATABASE']
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var} = {value[:3]}***" if 'PASSWORD' in var else f"✅ {var} = {value}")
        else:
            print(f"⚠️  {var} - Not set (using default)")
    
    return True

def test_streamlit_app():
    """Test if Streamlit app can be imported"""
    print("\n🚀 Testing Streamlit app...")
    try:
        import streamlit as st
        print("✅ Streamlit imported successfully!")
        return True
    except Exception as e:
        print(f"❌ Streamlit error: {e}")
        return False

def show_deployment_options():
    """Show deployment options"""
    print("\n" + "="*60)
    print("🚀 DEPLOYMENT OPTIONS")
    print("="*60)
    
    print("\n1️⃣  STREAMLIT CLOUD (Recommended - Free)")
    print("   • Go to: https://share.streamlit.io")
    print("   • Sign in with GitHub")
    print("   • Deploy your repository")
    print("   • Set environment variables in dashboard")
    
    print("\n2️⃣  RAILWAY (Easy - Free Tier)")
    print("   • Install: npm install -g @railway/cli")
    print("   • Run: railway login && railway up")
    print("   • Set environment variables: railway variables set KEY=VALUE")
    
    print("\n3️⃣  VPS/SERVER (Advanced)")
    print("   • Upload files to server")
    print("   • Install dependencies: pip install -r requirements.txt")
    print("   • Run: streamlit run social_listening_app.py")
    
    print("\n📋 NEXT STEPS:")
    print("1. Push code to GitHub")
    print("2. Set up MySQL database (local or cloud)")
    print("3. Configure environment variables")
    print("4. Deploy to your chosen platform")

def main():
    """Main deployment check function"""
    print("🔍 Social Listening Tool - Deployment Check")
    print("="*50)
    
    checks = [
        check_python_version(),
        check_dependencies(),
        check_database_connection(),
        check_environment_variables(),
        test_streamlit_app()
    ]
    
    print("\n" + "="*50)
    if all(checks):
        print("🎉 All checks passed! Your app is ready for deployment.")
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
    
    show_deployment_options()

if __name__ == "__main__":
    main() 