#!/usr/bin/env python3
"""
Simple startup script for the Atlan Customer Support AI Copilot
"""

import subprocess
import sys
import os

def main():
    print("🎯 Starting Atlan Customer Support AI Copilot...")
    
    # Set environment to avoid telemetry prompts
    env = os.environ.copy()
    env['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
    
    try:
        # Start Streamlit with specific configuration
        cmd = [
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port=8501",
            "--server.address=localhost",
            "--server.headless=false",
            "--browser.serverAddress=localhost",
            "--browser.serverPort=8501"
        ]
        
        print("🚀 Starting server on http://localhost:8501")
        print("📋 The application will open in your default browser")
        print("⏹️  Press Ctrl+C to stop the server")
        print("-" * 50)
        
        subprocess.run(cmd, env=env)
        
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        print("\nTry running manually: streamlit run app.py")

if __name__ == "__main__":
    main()
