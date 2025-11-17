"""
Quick Debug Launcher for Local Development
Simulates Render deployment environment locally
"""

import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("[OK] Loaded environment from .env file")
except ImportError:
    print("[!] python-dotenv not installed. Using system environment variables.")
    print("    Install with: pip install python-dotenv")

# Force debug mode for local development
os.environ['DEBUG'] = 'true'
os.environ['PORT'] = os.environ.get('PORT', '8050')
os.environ['HOST'] = os.environ.get('HOST', '0.0.0.0')

print("\n" + "="*80)
print("LOCAL DEBUG MODE - Simulating Render Deployment")
print("="*80)
print(f"\nConfiguration:")
print(f"  DEBUG: {os.environ.get('DEBUG')}")
print(f"  HOST: {os.environ.get('HOST')}")
print(f"  PORT: {os.environ.get('PORT')}")
print(f"  DATABASE_PATH: {os.environ.get('DATABASE_PATH', 'data/auth.db')}")
print(f"\nServer will start at: http://localhost:{os.environ.get('PORT')}")
print("="*80 + "\n")

# Import and run the app
try:
    from app import app, server, auth_manager, DEBUG, HOST, PORT

    # Clean up expired sessions
    try:
        cleaned = auth_manager.cleanup_expired_sessions()
        if cleaned > 0:
            print(f"[OK] Cleaned up {cleaned} expired sessions\n")
    except Exception as e:
        print(f"[!] Warning: Could not clean sessions: {e}\n")

    # Start server
    print("Starting development server...\n")
    app.run_server(
        debug=True,  # Always use debug mode for local development
        host=HOST,
        port=PORT,
        dev_tools_hot_reload=True,  # Auto-reload on file changes
        dev_tools_ui=True,  # Show dev tools in browser
        dev_tools_serve_dev_bundles=True
    )

except KeyboardInterrupt:
    print("\n\n" + "="*80)
    print("Server stopped by user")
    print("="*80)
    sys.exit(0)

except Exception as e:
    print("\n\n" + "="*80)
    print("ERROR STARTING SERVER")
    print("="*80)
    print(f"\nError: {e}")
    print("\nTroubleshooting:")
    print("  1. Make sure all dependencies are installed:")
    print("     pip install -r requirements.txt")
    print("  2. Check that data/ directory exists and is writable")
    print("  3. Ensure port 8050 is not already in use")
    print("  4. Check .env file for correct configuration")
    print("\n" + "="*80)

    import traceback
    traceback.print_exc()
    sys.exit(1)
