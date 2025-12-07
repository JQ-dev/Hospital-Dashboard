"""
Hospital KPI Dashboard - Production Application
Deployable to free cloud services (Render, Railway, Fly.io)
"""

import os
from pathlib import Path

from utils.logging_config import get_logger

# Import the authenticated app
from app_with_auth import app, server, auth_manager

logger = get_logger(__name__)

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
            logger.info(f"Cleaned up {cleaned} expired sessions")
    except Exception as e:
        logger.warning(f"Warning: Could not clean sessions: {e}")

    logger.info("\n" + "="*70)
    logger.info("Hospital KPI Dashboard with Authentication")
    logger.info("="*70)
    logger.debug(f"\nEnvironment: {'Development' if DEBUG else 'Production'}")
    logger.info(f"Server starting on {HOST}:{PORT}")
    logger.info("\nSupported account types:")
    logger.info("  - Company (organizations with employees)")
    logger.info("  - Employee (part of a company)")
    logger.info("  - Individual (independent users)")

    if not DEBUG:
        logger.info("\nRunning in PRODUCTION mode")
        logger.debug("   - Debug mode is OFF")
        logger.info("   - Using gunicorn in production")

    logger.info("\n" + "="*70 + "\n")

    # Run server
    app.run(
        debug=DEBUG,
        host=HOST,
        port=PORT
    )
