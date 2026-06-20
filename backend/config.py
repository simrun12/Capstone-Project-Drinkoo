"""
Configuration settings for DRINKOO platform.
Handles dev/prod branching and environment variables.
"""

import os
import subprocess
from typing import Optional

# Detect git branch for production mode
def get_current_branch() -> str:
    """Get current git branch name."""
    try:
        return subprocess.check_output(
            ['git', 'branch', '--show-current'],
            cwd=os.path.dirname(__file__)
        ).decode().strip()
    except Exception:
        return os.getenv('BRANCH', 'main')


# Load environment variables
DEBUG = os.getenv('DEBUG', 'true').lower() == 'true'
CURRENT_BRANCH = get_current_branch()
IS_PRODUCTION = CURRENT_BRANCH in ['prod', 'production']

# Database configuration
DATABASE_PATH = os.getenv('DATABASE_PATH', './data/drinkoo.db')
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

# Authentication settings
if IS_PRODUCTION:
    # Production mode: strict auth
    AUTH_MODE = "production"
    TOKEN_EXPIRY_HOURS = 1
    ENFORCE_HTTPS = True
    ENFORCE_PASSWORD_HASHING = True
    RATE_LIMIT_PER_MINUTE = 10
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'change-this-in-production')
else:
    # Development mode: loose auth
    AUTH_MODE = "development"
    TOKEN_EXPIRY_HOURS = 24
    ENFORCE_HTTPS = False
    ENFORCE_PASSWORD_HASHING = False
    RATE_LIMIT_PER_MINUTE = 100
    JWT_SECRET_KEY = "dev-secret-key-not-secure"

# Default credentials (dev only)
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "password"

# API configuration
API_VERSION = "v1"
API_HOST = os.getenv('API_HOST', 'localhost')
API_PORT = int(os.getenv('API_PORT', '8000'))
API_PREFIX = f"/api/{API_VERSION}"

# Cache settings
CACHE_TTL_SECONDS = 300  # 5 minutes
MAX_CACHE_SIZE = 1000

# Image upload settings
UPLOAD_DIRECTORY = "./uploads"
ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/png', 'image/webp'}
MAX_IMAGE_SIZE_MB = 5
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024

# Ollama RAG settings
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'mistral')
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'nomic-embed-text')
EMBEDDING_DIMENSION = 384
RAG_RESPONSE_TIMEOUT = 30  # seconds

# Pagination defaults
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 500

# Logging configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO' if IS_PRODUCTION else 'DEBUG')
LOG_FILE = './logs/drinkoo.log'
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# Application info
APP_NAME = "DRINKOO SKU Management Platform"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Beverage inventory and freight management system for DRINKOO"

# Print configuration on startup (dev only)
if DEBUG:
    print(f"""
    ╔══════════════════════════════════════╗
    ║     DRINKOO Configuration Loaded     ║
    ╠══════════════════════════════════════╣
    ║ Mode: {AUTH_MODE.upper():^33} ║
    ║ Branch: {CURRENT_BRANCH:^30} ║
    ║ Database: {DATABASE_PATH:^28} ║
    ║ Ollama: {OLLAMA_BASE_URL:^29} ║
    ║ API: http://{API_HOST}:{API_PORT:<20} ║
    ╚══════════════════════════════════════╝
    """)
