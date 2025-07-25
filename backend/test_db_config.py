#!/usr/bin/env python3
"""Test database configuration."""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print(f"DATABASE_URL from env: {os.getenv('DATABASE_URL')}")

# Test the settings
from app.core.config import settings
print(f"Database URL from settings: {settings.database_url}")