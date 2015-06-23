import json
import os
import datetime
import logging
import requests
from httplib2 import Http

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
# Get authorized by github
#
def get_github_auth(url, headers=None):
    got = requests.get(url, auth=github_auth, headers=headers)
    return got

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

# Define a route that measures most recent click of the last top issues

def get_least_clicked_issues():
    ''' Get the least clicked issues '''
    results = service.data().ga().get(
        ids="ga:" + GOOGLE_ANALYTICS_PROFILE_ID,
        start_date='2014-08-24',
        end_date=datetime.date.today().strftime("%Y-%m-%d"),
        metrics='ga:totalEvents',
        dimensions='ga:eventLabel',
        sort='ga:totalEvents',
        filters='ga:eventCategory=@Civic Issues',
        max_results=5,
        fields='rows').execute()

    least_clicked_issues = results["rows"]
    return least_clicked_issues

def get_most_recent_clicked_issue():
    ''' Get the 5 most recently clicked links'''
    results = service.data().ga().get(
        ids="ga:" + GOOGLE_ANALYTICS_PROFILE_ID,
        start_date='1daysAgo',
        end_date=datetime.date.today().strftime("%Y-%m-%d"),
        metrics='ga:totalEvents',
        dimensions='ga:eventLabel, ga:date',
        filters='ga:eventCategory==Civic Issues',
        sort='-ga:date',
        max_results=1).execute()
    # we should try to get the github statuses of each recently clicked issue
    most_recent_clicked_issue = results["rows"][0][0]
    return most_recent_clicked_issue



#
# Github
#

def get_stripped_url(url):
    #handle other urls later
    if url.startswith('https://github.com/'):
        return url[19:]
    else:
        return url

def get_top_github_data():
    ''' Let's see if I can get some issue comment data from the top_clicked_issues'''
    top_issues = get_top_clicked_issues()
    ga_github =[]
    url = "https://api.github.com/repos/"
    # define a stripping link method that takes away "https://github.com/"
    for link in top_issues:
        stripped_link = get_stripped_url(link[0])
        request_link = url + stripped_link
        response = get_github_auth(request_link).json()
        response_list =[]
        response_list.append(response)
        response_list.append(link)
        ga_github.append(response_list)
    return ga_github


#
# Tests
#
def get_top_city_clicks():
    results = service.data().ga().get(
        ids="ga:" + GOOGLE_ANALYTICS_PROFILE_ID,
        start_date='2014-08-24',
        end_date=datetime.date.today().strftime("%Y-%m-%d"),
        metrics='ga:totalEvents',
        dimensions='ga:city',
        max_results=5,
        sort='-ga:totalEvents',
        filters='ga:eventCategory=@Civic Issues').execute()

    top_clicked_cities = results["rows"]

    # You can do today's date minus the most recent, and once you figure out most recent,  compare the time delta and if the time delta is smaller then you add it to the dictionry
    return top_clicked_cities

def get_all_the_issues():
    ''' We will look at the percentage of issues are doing X or Y soon'''
    results = service.data().ga().get(
        ids="ga:" + GOOGLE_ANALYTICS_PROFILE_ID,
        start_date='2014-08-24',
        end_date=datetime.date.today().strftime("%Y-%m-%d"),
        metrics='ga:totalEvents',
        dimensions='ga:eventLabel',
        sort='-ga:totalEvents',
        #fields='rows, columnHeaders'
        filters='ga:eventCategory==Civic Issues;ga:eventLabel=@github.com').execute()

    total_issues=results["rows"]
    return total_issues


def get_all_github_data(all_issues):
    # Let's see if I can get some issue comment data from the top_clicked_issues'''
    ga_github = []
    url = "https://api.github.com/repos/"
    total = 0
    # define a stripping link method that takes away "https://github.com/"
    for link in all_issues:
        ga_github.append(get_github_auth(url + link[1][19:]).json())
        total += 1
        print "Completed " + str(total*100/len(all_issues)) +  " percent!"
    return ga_github

def get_github_data(issue, scripting=True):
    # Let's see if I can get some issue comment data from the top_clicked_issues'''
    url = "https://api.github.com/repos/"
    # define a stripping link method that takes away "https://github.com/"
    if scripting== False:
        git_data = get_github_auth(url + issue[19:]).json()
    else:
        print "Running Script"
    return git_data

def get_date_of_issues():
    results = service.data().ga().get(
        ids="ga:" + GOOGLE_ANALYTICS_PROFILE_ID,
        start_date='2014-08-24',
        end_date=datetime.date.today().strftime("%Y-%m-%d"),
        metrics='ga:totalEvents',
        dimensions='ga:date, ga:eventLabel',
        sort='-ga:date',
        max_results=5,
        #fields='rows, columnHeaders'
        filters='ga:eventCategory==Civic Issues;ga:eventLabel=@github.com').execute()

    # sorted by click frequency (same as all freq)
    dates = results["rows"]
    for date in dates:
        date[0] = analytics_formatted_date(date[0])

    return dates

def analytics_formatted_date(date):
    #monthDict={'01':'Jan', '02':'Feb', '03':'Mar', '04':'Apr', '05':'May', '06':'Jun', '07':'Jul', '08':'Aug', '09':'Sep', '10':'Oct', '11':'Nov', '12':'Dec'}
    year = date[:4]
    month = date[4:6]
    #if month in monthDict:
        #for key in monthDict:
            #month=monthDict.get(key)
    day = date[6:]
    return month + " " + day + ", " + year


#
# Routes
#

@app.route("/")
def index():
    total_clicks = get_total_clicks()
    total_page_views = get_total_page_views()
    top_clicked_issues = get_top_clicked_issues()
    least_clicked_issues = get_least_clicked_issues()
    most_recent_clicked_issue = get_most_recent_clicked_issue()
    clicks_per_view = get_percentage_of_views_with_clicks(total_clicks, total_page_views)
    github_data = get_top_github_data()
    return render_template("index.html",total_clicks=total_clicks,
        total_page_views=total_page_views,
        top_clicked_issues=top_clicked_issues,
        least_clicked_issues=least_clicked_issues, 
        most_recent_clicked_issue=most_recent_clicked_issue,
        clicks_per_view=clicks_per_view,
        github_data = github_data,
        access_token=access_token)

@app.route("/test", methods=["GET", "POST"])
def test():
    top_cities = get_top_city_clicks()
    issue_list = get_all_the_issues()
    total_issues = len(issue_list)
    no_cities = len(top_cities)
    dates_of_issues = get_date_of_issues()
    if request.method == "POST":
        data_list = []
        data_list.append(get_github_data(request.form["issue"], False))
        recently_clicked_github = data_list
        all_clicked_github = data_list
    else:
        recently_clicked_github = get_all_github_data(dates_of_issues)
        all_clicked_github = []
    #all_github_data = get_all_github_data(issue_list) Takes like 4-5 minutes
    return render_template("test.html", all_clicked_github= all_clicked_github, recently_clicked_github = recently_clicked_github, dates_of_issues=dates_of_issues, no_cities=no_cities, total_issues=total_issues, top_cities=top_cities, issue_list=issue_list)


if __name__ == '__main__':
    app.run(debug=True)