#!/usr/bin/env python3
"""
Startup script for the Atlan Customer Support AI Copilot
"""

import os
import sys
import subprocess
from pathlib import Path

def check_requirements():
    """Check if all requirements are satisfied"""
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("❌ requirements.txt not found!")
        return False
    
    try:
        import streamlit
        import openai
        import requests
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Run: pip install -r requirements.txt")
        return False

def check_api_key():
    """Check if OpenAI API key is configured"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("⚠️  OpenAI API key not found in environment variables")
        print("You can either:")
        print("1. Set OPENAI_API_KEY environment variable")
        print("2. Create a .env file with OPENAI_API_KEY=your_key_here")
        print("3. Enter the API key in the application sidebar")
        return False
    print("✅ OpenAI API key configured")
    return True

def check_sample_data():
    """Check if sample data exists"""
    sample_file = Path("sample_tickets.json")
    if not sample_file.exists():
        print("❌ sample_tickets.json not found!")
        return False
    print("✅ Sample data available")
    return True

def main():
    """Main startup function"""
    print("🎯 Atlan Customer Support AI Copilot")
    print("=" * 50)
    
    # Check all prerequisites
    if not check_requirements():
        sys.exit(1)
    
    check_api_key()  # Not critical, can be set in app
    
    if not check_sample_data():
        print("⚠️  Sample data missing but application can still run")
    
    print("\n🚀 Starting application...")
    print("Navigate to: http://localhost:8501")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    # Launch Streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port=8501",
            "--server.address=localhost"
        ])
    except KeyboardInterrupt:
        print("\n👋 Application stopped")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
