#!/usr/bin/env python3
"""
Test database connection for Social Listening Tool
"""

try:
    from database import DatabaseManager
    print("✅ Database module imported successfully!")
    
    db = DatabaseManager()
    if db.connect():
        print("✅ Database connection successful!")
        db.disconnect()
    else:
        print("❌ Database connection failed!")
        
except Exception as e:
    print(f"❌ Error: {e}")