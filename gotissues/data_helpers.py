import datetime
import requests
import json
import operator
from psycopg2 import connect, extras

from httplib2 import Http
from oauth2client.client import SignedJwtAssertionCredentials
from apiclient.discovery import build

from config import *


def dict_cursor(conn, cursor_factory=extras.RealDictCursor):
    return conn.cursor(cursor_factory=cursor_factory)


def login_to_google_analytics():
    credentials = SignedJwtAssertionCredentials(GOOGLE_SERVICE_ACCOUNT_EMAIL, GOOGLE_SERVICE_ACCOUNT_SECRET_KEY,
    'https://www.googleapis.com/auth/analytics.readonly')
    http = Http()
    credentials.authorize(http)
    service = build("analytics", "v3", http=http)
    return service, credentials.access_token

service, access_token = login_to_google_analytics()

# Github Auth set up
if 'GITHUB_TOKEN' in os.environ:
    github_auth = (os.environ['GITHUB_TOKEN'], '')
else:
    github_auth = None

#
# Methods that return data from Google Analytics
#
choice_dict = {
    "clicked_issues": {
      'start_date' : 'today',
      'metrics':'ga:totalEvents',
      'dimensions':'ga:eventLabel',
      'sort':'-ga:totalEvents',
      'filters':'ga:eventCategory==Civic Issues;ga:eventLabel=@github.com',
      'max_results':10000,
      'fields':None
    },

    "top_cities": {
      'metrics':'ga:totalEvents',
      'dimensions':'ga:city',
      'sort':'-ga:totalEvents',
      'filters':'ga:eventCategory==Civic Issues',
      'max_results':5,
      'fields':None
    },

    "least_clicked": {
      'metrics':'ga:totalEvents',
      'dimensions':'ga:eventLabel',
      'sort':'ga:totalEvents',
      'filters':'ga:eventCategory==Civic Issues;ga:eventLabel=@github.com',
      'max_results':5,
      'fields':'rows'
    },

    "most_clicked": {
      'metrics':'ga:totalEvents',
      'dimensions':'ga:eventLabel',
      'sort':'-ga:totalEvents',
      'filters':'ga:eventCategory==Civic Issues;ga:eventLabel=@github.com',
      'max_results':5,
      'fields':'rows'
    },

    "recently_clicked": {
      'metrics':'ga:totalEvents',
      'dimensions':'ga:eventLabel, ga:dateHour, ga:minute',
      'sort':'-ga:dateHour',
      'filters':'ga:eventCategory==Civic Issues;ga:eventLabel=@github.com',
      'max_results':10000,
      'fields':None
    },

    "total_page_views": {
      'metrics':'ga:pageviews',
      'dimensions':None,
      'sort':None,
      'filters':'ga:pagePath=@civicissues',
      'max_results':10,
      'fields':None
    },
    
    "total_clicks": {
      'metrics':'ga:totalEvents',
      'dimensions':None,
      'sort':None,
      'filters':'ga:eventCategory==Civic Issues',
      'max_results':None,
      'fields':None
    },

    "viewed_issues": {
      'start_date' : 'today',
      'metrics':'ga:totalEvents',
      'dimensions':'ga:eventLabel',
      'sort':'-ga:totalEvents',
      'filters':'ga:eventCategory==Civic Issue View',
      'max_results':20,
      'fields':None
    },

    "all_clicks": {
      'start_date':'today',
      'end_date':'today',
      'metrics':'ga:totalEvents',
      'dimensions':'ga:eventLabel, ga:dateHour, ga:minute',
      'sort':'-ga:dateHour',
      'filters':'ga:eventCategory==Civic Issues',
      'max_results':10000,
      'fields':'rows'
    },

}

def edit_request_query(choice_dict_query):
  print "Asking GA for: " + choice_dict_query
  results = service.data().ga().get(
          ids="ga:" + GOOGLE_ANALYTICS_PROFILE_ID,
          start_date=choice_dict[choice_dict_query].get("start_date",'2014-08-23'),
          end_date=choice_dict[choice_dict_query].get("end_date", 'today'),
          metrics=choice_dict[choice_dict_query]['metrics'],
          dimensions=choice_dict[choice_dict_query]['dimensions'],
          sort=choice_dict[choice_dict_query]['sort'],
          max_results=choice_dict[choice_dict_query]['max_results'],
          filters=choice_dict[choice_dict_query]['filters'],
          fields=choice_dict[choice_dict_query]['fields']).execute()

  return results

def get_analytics_query(choice):  
  if choice == "clicked_issues":
    results = edit_request_query(choice)
    clicked_issues = []
    for row in results["rows"]:
        issue = {
            "url" : row[0],
            "clicks" : row[1]
        }
        clicked_issues.append(issue)
    return clicked_issues


  elif choice == "top_cities":
    results = edit_request_query(choice)
    top_clicked_cities = results["rows"]
    return top_clicked_cities

  elif choice == "least_clicked":
    results = edit_request_query(choice)
    least_clicked_issues = results["rows"]
    return least_clicked_issues

  elif choice == "most_clicked":
    results = edit_request_query(choice)
    top_clicked_issues = results["rows"]
    return top_clicked_issues

  elif choice == "recently_clicked":
    results = edit_request_query(choice)
    clicked_timestamps = []
    for row in results["rows"]:
      clicked_timestamps.append(return_timestamp_dict(row))
    return clicked_timestamps

  elif choice == "total_page_views":
    results = edit_request_query(choice)
    total_page_views = results["rows"][0][0]
    return total_page_views

  elif choice == "total_clicks":
    results = edit_request_query(choice)
    total_clicks = results["rows"][0][0]
    return total_clicks

  elif choice == "viewed_issues":
    results = edit_request_query(choice)
    viewed_issues = []
    for row in results["rows"]:
        viewed_issue = {
            "url" : row[0].split(',')[0],
            "views" : row[1],
            "view_sources" : [row[0].split(',')[1]]
        }

        # If the github url already exists in our list, add the new source to it
        found = find(viewed_issues, "url", viewed_issue["view_sources"][0])
        if found:
            viewed_issues[found]["view_sources"].append(viewed_issue["view_sources"][0])
        else:
            viewed_issues.append(viewed_issue)
    return viewed_issues

  elif choice == "all_clicks":
    results = edit_request_query(choice)
    clicks = []
    for row in results["rows"]:
      click = {
        "issue_url" : row[0],
        "timestamp" : ga_time_to_timestamp(row[1], row[2])[0],
        "readable_date" : ga_time_to_timestamp(row[1], row[2])[1]
      }
      clicks.append(click)
    return clicks

  else:
    response = {
        "Error" : "Bad query request, not added to our dictionary"
    }
    return response

def find(lst, key, value):
    for i, dic in enumerate(lst):
        if dic[key] == value:
            return i
    return False

def ga_time_to_timestamp(date, minute):
  # Format should be 2015-06-29T16:35:39Z
  # or Year-Mo-DaTHr:Mi:00Z
  year = int(date[:4])
  month = int(date[4:6])
  day = int(date[6:8])
  hour = int(date[8:10])
  minute = int(minute)

  new_time = datetime.datetime(year, month, day, hour, minute)
  iso_time = new_time.isoformat()
  new_time = new_time.strftime('%A, %B %d %Y %I:%M%p')
  return iso_time, new_time

def return_timestamp_dict(row):
  new_time = ga_time_to_timestamp(row[1], row[2])
  # print str(new_time) + "\n"
  clicked_timestamp = {
      "url": row[0],
      "timestamp": new_time[0],
      "readable_date" : new_time[1]
  }
  return clicked_timestamp
#
# Methods that return data from Github
#

def get_github_with_auth(url, headers=None):
  ''' Get authorized by github'''
  print "Asking github for: " + url
  got = requests.get(url, auth=github_auth, headers=headers)
  if got.status_code == 404:
    print "404 Error: " + url 
    return None
  else:
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

def get_github_project_data(issue_url):
  ''' Converting -->
      https://github.com/:org/:repo/issues/:no -->
      https://api.github.com/repos/:org/:repo/issues/:no -->
      https://api.github.com/repos/:org/:repo/events '''
  if issue_url.startswith('https://github.com/'):
    api_issue = "https://api.github.com/repos/" + issue_url[19:]
    issue_var = api_issue.split("/")[7]
    api_issue = api_issue.replace("issues/" + str(issue_var), 'events')
    result = get_github_with_auth(api_issue)
    if result:
      gitdata = result.json()
      return gitdata
    else:
      return None
  else:
    print "Error in this issue url: " + str(issue_url)
    return None

def get_click_activity(clicks):
  activities = []
  total = 0
  for click in clicks:
    activity_list = get_github_project_data(click["issue_url"])
    for activity in activity_list:
      if check_timestamp(activity, click, 1):
        trimmed_activity = trim_activity(activity, click)
        if check_events(trimmed_activity, activity):
          activities.append(trimmed_activity)
          print str(trimmed_activity) + "\n"
  return activities

def check_timestamp(activity, click, hours):
  action_time = datetime.datetime.strptime(activity["created_at"], '%Y-%m-%dT%H:%M:%SZ')
  click_time = datetime.datetime.strptime(click["timestamp"], '%Y-%m-%dT%H:%M:%S')
  timedelta = action_time - click_time
  if timedelta < datetime.timedelta(hours=hours) and timedelta > datetime.timedelta(minutes=0):
    print timedelta
    return True
  else:
    return False

def trim_activity(activities, click):
  trimmed_activities = {}
  trimmed_activities["issue_url"] = click["issue_url"]
  trimmed_activities["click_timestamp"] = click["timestamp"]
  trimmed_activities["activity_type"] = activities["type"]
  trimmed_activities["activity_timestamp"] = activities["created_at"]
  return trimmed_activities

def check_events(trimmed_activity, activity_git):
    filtered_activities = ["PushEvent","DeleteEvent"]
    for activity in filtered_activities:
      if trimmed_activity["activity_type"] == activity:
        return False
      if trimmed_activity["activity_type"] == "IssueCommentEvent":
        if activity_git["payload"]["issue"]["html_url"] != trimmed_activity["issue_url"]:
          print activity_git["payload"]["issue"]["html_url"] 
          print trimmed_activity["issue_url"]
          return False
    return True

def get_closed_count(db):
  ''' Pull out data from the database '''
  q = ''' SELECT COUNT(*) FROM issues WHERE state = 'closed' '''

  db.execute(q)
  closed_count = db.fetchone()["count"]
  return closed_count

