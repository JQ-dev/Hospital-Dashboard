"""
Hospital KPI Dashboard - Production Application
Deployable to free cloud services (Render, Railway, Fly.io)
"""

import os
from pathlib import Path

# Import the authenticated app
from app_with_auth import app, server, auth_manager

# ============================================================================
# PRODUCTION CONFIGURATION
# ============================================================================

# Get port from environment variable (for cloud deployment)
PORT = int(os.environ.get('PORT', 8050))

# Get host from environment variable
HOST = os.environ.get('HOST', '0.0.0.0')

# Set debug mode based on environment
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# Ensure data directory exists
DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True)

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    # Cleanup expired sessions on startup
    try:
        cleaned = auth_manager.cleanup_expired_sessions()
        if cleaned > 0:
            print(f"Cleaned up {cleaned} expired sessions")
    except Exception as e:
        print(f"Warning: Could not clean sessions: {e}")

    print("\n" + "="*70)
    print("Hospital KPI Dashboard with Authentication")
    print("="*70)
    print(f"\nEnvironment: {'Development' if DEBUG else 'Production'}")
    print(f"Server starting on {HOST}:{PORT}")
    print(f"\nLanding Page: http://{HOST}:{PORT}")
    print(f"Dashboard App: http://{HOST}:{PORT}/app")
    print("\nSupported account types:")
    print("  - Company (organizations with employees)")
    print("  - Employee (part of a company)")
    print("  - Individual (independent users)")

    if not DEBUG:
        print("\n⚠️  Running in PRODUCTION mode")
        print("   - Debug mode is OFF")
        print("   - Using gunicorn in production")

    print("\n" + "="*70 + "\n")

    # Run server
    app.run_server(
        debug=DEBUG,
        host=HOST,
        port=PORT
    )
