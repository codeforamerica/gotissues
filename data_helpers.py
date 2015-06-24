''' one function that can talk to google! '''
from gotissues import *


#
# Methods that return data from Google Analytics
#


def get_clicked_issues():
    ''' Get all the clicked issues as json'''
    results = service.data().ga().get(
        ids="ga:" + GOOGLE_ANALYTICS_PROFILE_ID,
        start_date='2014-08-24',
        end_date=datetime.date.today().strftime("%Y-%m-%d"),
        metrics='ga:totalEvents',
        dimensions='ga:eventLabel',
        sort='-ga:totalEvents',
        filters='ga:eventCategory==Civic Issues;ga:eventLabel=@github.com').execute()

    issues = []
    for row in results["rows"]:
        issue = {
            "url" : row[0],
            "clicks" : row[1]
        }
        issues.append(issue)
    return issues

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
    return top_clicked_cities

def get_least_clicked_issues():
    ''' Get the least clicked issues '''
    results = service.data().ga().get(
        ids="ga:" + GOOGLE_ANALYTICS_PROFILE_ID,
        start_date='2014-08-24',
        end_date=datetime.date.today().strftime("%Y-%m-%d"),
        metrics='ga:totalEvents',
        dimensions='ga:eventLabel',
        sort='ga:totalEvents',
        filters='ga:eventCategory=@Civic Issues;ga:eventLabel=@github.com',
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
# Methods that return data from Github
#

def get_github_with_auth(url, headers=None):
  ''' Get authorized by github'''
  got = requests.get(url, auth=github_auth, headers=headers)
  return got

def get_github_data(issue_url):
    url = "https://api.github.com/repos/"
    if issue_url.startswith('https://github.com/'):
        git_data = get_github_with_auth(url + issue_url[19:]).json()
    else:
      git_data = {
        "Error" : "Link invalid"
      }
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
        filters='ga:eventCategory==Civic Issues;ga:eventLabel=@github.com').execute()

    # sorted by click frequency (same as all freq)
    dates = results["rows"]
    for date in dates:
        date[0] = analytics_formatted_date(date[0])

    return dates