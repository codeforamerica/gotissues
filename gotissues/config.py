# All of Got Issues config values
import os
import logging

# Logging Setup
logging.basicConfig(level=logging.INFO)

# Variables
GOOGLE_ANALYTICS_PROFILE_ID = "41226190"
GOOGLE_SERVICE_ACCOUNT_EMAIL = os.environ["GOOGLE_SERVICE_ACCOUNT_EMAIL"]
GOOGLE_SERVICE_ACCOUNT_SECRET_KEY = os.environ["GOOGLE_SERVICE_ACCOUNT_SECRET_KEY"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
DATABASE_URL = os.environ["DATABASE_URL"]