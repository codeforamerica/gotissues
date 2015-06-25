''' gotissues.py: the core of gotissues. 
    it should pull in functions from the others. '''
import os
import logging
import datetime
import requests
import json

from httplib2 import Http
from psycopg2 import connect, extras
from data_helpers import *


from oauth2client.client import SignedJwtAssertionCredentials
from apiclient.discovery import build

from flask import Flask, render_template, request
# Config
app = Flask(__name__)
from views import *

# Logging Setup
logging.basicConfig(level=logging.INFO)

# Variables
GOOGLE_ANALYTICS_PROFILE_ID = "41226190"
GOOGLE_SERVICE_ACCOUNT_EMAIL = os.environ["GOOGLE_SERVICE_ACCOUNT_EMAIL"]
GOOGLE_SERVICE_ACCOUNT_SECRET_KEY = os.environ["GOOGLE_SERVICE_ACCOUNT_SECRET_KEY"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]

if 'GITHUB_TOKEN' in os.environ:
    github_auth = (os.environ['GITHUB_TOKEN'], '')
else:
    github_auth = None

#
# Runs when server starts
#
def login_to_google_analytics():
    credentials = SignedJwtAssertionCredentials(GOOGLE_SERVICE_ACCOUNT_EMAIL, GOOGLE_SERVICE_ACCOUNT_SECRET_KEY,
    'https://www.googleapis.com/auth/analytics.readonly')
    http = Http()
    credentials.authorize(http)
    service = build("analytics", "v3", http=http)
    return service, credentials.access_token

service, access_token = login_to_google_analytics()

#
# Database setup
#
def db_connect(app):
    return connect(app.config['DATABASE_URL'])

def db_cursor(conn, cursor_factory=extras.RealDictCursor):
    return conn.cursor(cursor_factory=cursor_factory)


if __name__ == '__main__':
    app.run(debug=True)