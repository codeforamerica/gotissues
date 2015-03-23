import httplib2
import os
import datetime
import json

from apiclient.errors import HttpError
from apiclient.discovery import build
from oauth2client import client

from flask import Flask, session, request, redirect, url_for, jsonify


# CONFIG
app = Flask(__name__)
app.secret_key = os.environ['SECRET_KEY']

CLIENT_ID = os.environ['CLIENT_ID']
CLIENT_SECRET = os.environ['CLIENT_SECRET']


# ROUTES
@app.route('/')
def index():
    if 'credentials' not in session:
        return redirect(url_for('login'))

    credentials = client.Credentials.new_from_json(session['credentials'])

    http = httplib2.Http()
    http = credentials.authorize(http)
    service = build("analytics", "v3", http=http)

    id = get_id(service)
    results = get_clicked_issue_urls(service, id)
    clicked_issues = cleanup_clicked_issues(results)

    return json.dumps(clicked_issues, indent=4)


@app.route('/login')
def login():
    flow = client.OAuth2WebServerFlow(client_id=CLIENT_ID,
                                      client_secret=CLIENT_SECRET,
                                      scope='https://www.googleapis.com/auth/analytics.readonly',
                                      redirect_uri='http://localhost:5000/oauth2callback',
                                      access_type="offline")

    auth_uri = flow.step1_get_authorize_url()
    return redirect(auth_uri)


@app.route('/signout')
def signout():
    del session['credentials']
    session['message'] = "You have logged out"

    return redirect(url_for('index'))


@app.route('/oauth2callback')
def oauth2callback():
    code = request.args.get('code')
    if code:
        # exchange the authorization code for user credentials
        flow = client.OAuth2WebServerFlow(CLIENT_ID, CLIENT_SECRET,
                                          "https://www.googleapis.com/auth/analytics.readonly")
        flow.redirect_uri = request.base_url
        try:
            credentials = flow.step2_exchange(code)
        except Exception as e:
            print "Unable to get an access token because ", e.message

        # store these credentials for the current user in the session
        # This stores them in a cookie, which is insecure. Update this
        # with something better if you deploy to production land
        session['credentials'] = credentials.to_json()
        return redirect("/")


def get_id(service):
    # Try to make a request to the API. Print the results or handle errors.
    try:
        first_profile_id = get_first_profile_id(service)
        if not first_profile_id:
            print 'Could not find a valid profile for this user.'
        else:
            return first_profile_id

    except TypeError, error:
        # Handle errors in constructing a query.
        print ('There was an error in constructing your query : %s' % error)

    except HttpError, error:
        # Handle API errors.
        print ('Arg, there was an API error : %s : %s' %
               (error.resp.status, error._get_reason()))

    except client.AccessTokenRefreshError:
        # Handle Auth errors.
        print ('The credentials have been revoked or expired, please re-run '
               'the application to re-authorize')

def get_first_profile_id(service):
    """Traverses Management API to return the first profile id.

    This first queries the Accounts collection to get the first account ID.
    This ID is used to query the Webproperties collection to retrieve the first
    webproperty ID. And both account and webproperty IDs are used to query the
    Profile collection to get the first profile id.

    Args:
    service: The service object built by the Google API Python client library.

    Returns:
    A string with the first profile ID. None if a user does not have any
    accounts, webproperties, or profiles.
    """

    accounts = service.management().accounts().list().execute()

    if accounts.get('items'):
        firstAccountId = accounts.get('items')[0].get('id')
        webproperties = service.management().webproperties().list(
            accountId=firstAccountId).execute()

    if webproperties.get('items'):
        firstWebpropertyId = webproperties.get('items')[0].get('id')
        profiles = service.management().profiles().list(
            accountId=firstAccountId,
            webPropertyId=firstWebpropertyId).execute()

        if profiles.get('items'):
            return profiles.get('items')[0].get('id')

    return None


def get_clicked_issue_urls(service, id):
    try:
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

    except TypeError, error:
        # Handle errors in constructing a query.
        print ('There was an error in constructing your query : %s' % error)

    except HttpError, error:
        # Handle API service errors.
        print ('There was an API error : %s : %s' %
               (error.resp.status, error._get_reason()))


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


if __name__ == '__main__':
    app.secret_key = 'hello world'
    app.run(debug=True)
