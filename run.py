import json
import os
import datetime
import logging

import requests
from functools import partial
from httplib2 import Http
from psycopg2 import connect, extras
from data_helpers import *
from view_helpers import *

from oauth2client.client import SignedJwtAssertionCredentials
from apiclient.discovery import build

from flask import Flask, render_template, request

# Logging Setup
logging.basicConfig(level=logging.INFO)


# Config
app = Flask(__name__)

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

#
# Functions used in Routes
#

def get_total_clicks():
    ''' Get the total amount of clicks ever '''
    results = service.data().ga().get(
        ids="ga:" + GOOGLE_ANALYTICS_PROFILE_ID,
        start_date='2014-08-24',
        end_date=datetime.date.today().strftime("%Y-%m-%d"),
        metrics='ga:totalEvents',
        filters='ga:eventCategory=@Civic Issues').execute()

    total_clicks = results["rows"][0][0]

    return total_clicks


def get_total_page_views():
    ''' Get the total page views for the civic issue finder. '''
    results = service.data().ga().get(
        ids="ga:" + GOOGLE_ANALYTICS_PROFILE_ID,
        start_date='2014-08-24',
        end_date=datetime.date.today().strftime("%Y-%m-%d"),
        metrics='ga:pageviews',
        filters='ga:pagePath=@civicissues',
        max_results=10).execute()

    total_page_views = results["rows"][0][0]
    return total_page_views


def get_percentage_of_views_with_clicks(total_clicks, total_page_views):
    ''' What percentage of views have a click? '''
    clicks_per_view = ( float(total_clicks) / float(total_page_views) ) * 100
    return int(clicks_per_view)


def get_top_clicked_issues():
    ''' Get the top clicked issues '''
    results = service.data().ga().get(
        ids="ga:" + GOOGLE_ANALYTICS_PROFILE_ID,
        start_date='2014-08-24',
        end_date=datetime.date.today().strftime("%Y-%m-%d"),
        metrics='ga:totalEvents',
        dimensions='ga:eventLabel',
        sort='-ga:totalEvents',
        filters='ga:eventCategory=@Civic Issues',
        max_results=5,
        fields='rows').execute()

    top_clicked_issues = results["rows"]

    return top_clicked_issues

#
# Routes
#

@app.route("/", methods=["GET", "POST"])
def index():
    total_clicks = get_total_clicks()
    total_page_views = get_total_page_views()
    top_clicked_issues = get_top_clicked_issues()
    least_clicked_issues = get_least_clicked_issues()
    most_recent_clicked_issue = get_most_recent_clicked_issue()
    clicks_per_view = get_percentage_of_views_with_clicks(total_clicks, total_page_views)
    issue_list = get_clicked_issues()
    total_issues = len(issue_list)
    top_cities = get_top_city_clicks()
    no_cities = len(top_cities)

    if request.method == "POST":
        check_clicked_github = get_github_data(request.form["issue"])
    else:
        check_clicked_github = []

    #get total number of closed issues differently

    return render_template("index.html",total_clicks=total_clicks,
        total_page_views=total_page_views,
        top_clicked_issues=top_clicked_issues,
        least_clicked_issues=least_clicked_issues, 
        most_recent_clicked_issue=most_recent_clicked_issue,
        clicks_per_view=clicks_per_view,
        access_token=access_token,
        total_issues=total_issues,
        issue_list=issue_list,
        top_cities = top_cities,
        no_cities=no_cities,
        check_clicked_github = check_clicked_github)


if __name__ == '__main__':
    app.run(debug=True)