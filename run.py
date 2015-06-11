import json
import os
import datetime
import logging
from httplib2 import Http

from oauth2client.client import SignedJwtAssertionCredentials
from apiclient.discovery import build

from flask import Flask, render_template

# Logging Setup
logging.basicConfig(level=logging.INFO)


# Config
app = Flask(__name__)


# Variables
GOOGLE_ANALYTICS_PROFILE_ID = "41226190"
GOOGLE_SERVICE_ACCOUNT_EMAIL = os.environ["GOOGLE_SERVICE_ACCOUNT_EMAIL"]
GOOGLE_SERVICE_ACCOUNT_SECRET_KEY = os.environ["GOOGLE_SERVICE_ACCOUNT_SECRET_KEY"]

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
# Functions used in Routes
#

def get_total_clicks():
    ''' Get the total amount of clicks ever '''

    results = service.data().ga().get(
        ids="ga:" + GOOGLE_ANALYTICS_PROFILE_ID,
        start_date='2014-08-24',
        end_date=datetime.date.today().strftime("%Y-%m-%d"),
        metrics='ga:totalEvents',
        dimensions='ga:eventCategory').execute()

    # Can't seem to filter on ga:eventCategory in the query
    # so we do it by code.
    for row in results["rows"]:
        if row[0] == "Civic Issues":
            total_clicks = row[1]

    return total_clicks


def get_top_ten_clicked_issues():
    ''' Get the top ten clicked issues '''
    results = service.data().ga().get(
        ids="ga:" + GOOGLE_ANALYTICS_PROFILE_ID,
        start_date='2014-08-24',
        end_date=datetime.date.today().strftime("%Y-%m-%d"),
        metrics='ga:totalEvents',
        dimensions='ga:eventLabel',
        sort='-ga:totalEvents',
        # Only include github events
        filters='ga:eventLabel=@github.com',
        max_results=10,
        fields='rows').execute()

    top_ten_clicked_issues = results["rows"]
    return top_ten_clicked_issues


def get_most_recent_clicked_issue():
    ''' Get the most recently clicked link '''
    results = service.data().ga().get(
        ids="ga:" + GOOGLE_ANALYTICS_PROFILE_ID,
        start_date='7daysAgo',
        end_date=datetime.date.today().strftime("%Y-%m-%d"),
        metrics='ga:totalEvents',
        dimensions='ga:eventLabel, ga:date',
        # Only include github events
        filters='ga:eventLabel=@github.com',
        max_results=1,
        fields='rows').execute()

    most_recent_clicked_issue = results["rows"][0][0]
    return most_recent_clicked_issue


#
# Routes
#
@app.route("/")
def index():
    total_clicks = get_total_clicks()
    top_ten_clicked_issues = get_top_ten_clicked_issues()
    most_recent_clicked_issue = get_most_recent_clicked_issue()
    return render_template("index.html",total_clicks=total_clicks, 
        top_ten_clicked_issues=top_ten_clicked_issues, 
        most_recent_clicked_issue=most_recent_clicked_issue,
        access_token=access_token)


if __name__ == '__main__':
    app.run(debug=True)