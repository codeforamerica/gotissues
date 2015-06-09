import json
import os
import datetime
import logging
from httplib2 import Http

from oauth2client.client import SignedJwtAssertionCredentials
from apiclient.discovery import build

from flask import Flask

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
    return service

service = login_to_google_analytics()


#
# Functions used in Routes
#
def get_clicked_issue_urls(service, id):
    ''' Get the each issue and the total times its been clicked in desc order '''
    results = service.data().ga().get(
        ids="ga:" + id,
        start_date='2014-08-24',
        end_date=datetime.date.today().strftime("%Y-%m-%d"),
        metrics='ga:totalEvents',
        dimensions='ga:eventLabel',
        sort='-ga:totalEvents',
        # Some older entries have different labels. Filter them out
        filters='ga:eventLabel=@github.com',
        fields='rows').execute()

    return results


def cleanup_clicked_issues(results):
    ''' Turn Google Analytics results into nice labeled json '''

    clicked_issues = []
    for row in results["rows"]:
        clicked_issue = {
            "issue" : row[0],
            "clicks" : row[1]
        }
        clicked_issues.append(clicked_issue)

    return clicked_issues

#
# Routes
#
@app.route("/")
def index():
    results = get_clicked_issue_urls(service, GOOGLE_ANALYTICS_PROFILE_ID)
    clicked_issues = cleanup_clicked_issues(results)
    return json.dumps(clicked_issues, indent=4)


if __name__ == '__main__':
    app.run(debug=True)