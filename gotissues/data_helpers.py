import datetime
import requests
import json
import operator
from psycopg2 import connect, extras

from httplib2 import Http
from oauth2client.client import SignedJwtAssertionCredentials
from apiclient.discovery import build

from config import *

#
# Setup for DB
#
def dict_cursor(conn, cursor_factory=extras.RealDictCursor):
    return conn.cursor(cursor_factory=cursor_factory)


#
# Setup for all GA queries
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
# Setup for all Github queries
#
if 'GITHUB_TOKEN' in os.environ:
    github_auth = (os.environ['GITHUB_TOKEN'], '')
else:
    github_auth = None

#
# Methods + data for Google Analytics requests
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
    }
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

  elif choice == "total_page_views":
    results = edit_request_query(choice)
    total_page_views = results["rows"][0][0]
    return total_page_views

  elif choice == "total_clicks":
    results = edit_request_query(choice)
    total_clicks = results["rows"][0][0]
    return total_clicks

  else:
    response = {
        "Error" : "Bad query request, not added to our dictionary"
    }
    return response


#
# Helper functions to parse responses from Google Analytics for our DB
#
def find(lst, key, value):
    for i, dic in enumerate(lst):
        if dic[key] == value:
            return i
    return False

def ga_time_to_timestamp(date, minute):
  '''Format should be 2015-06-29T16:35:39Z (Year-Mo-DaTHr:Mi:00Z) '''
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

def github_html_url_to_api(url):
    """ Convert https://github.com links to https://api.gitub.com """
    if url.startswith('https://github.com/'):
        return "https://api.github.com/repos/" + url[19:]
    else:
        return url

def get_github_project_data(issue_url):
  ''' Converting link to API request link + data -->
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


#
# Methods for our 'clicked-activity' table and fetches all our clicks
#
def get_click_activity(clicks):
  ''' Get github activity related to each click in our click table '''
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
  ''' Filter out activity that happened too far away from our clicks '''
  action_time = datetime.datetime.strptime(activity["created_at"], '%Y-%m-%dT%H:%M:%SZ')
  click_time = datetime.datetime.strptime(click["timestamp"], '%Y-%m-%dT%H:%M:%S')
  timedelta = action_time - click_time
  if timedelta < datetime.timedelta(hours=hours) and timedelta > datetime.timedelta(minutes=0):
    print timedelta
    return True
  else:
    return False

def trim_activity(activities, click):
  ''' Filter out extraneous Github data that was returned about the activity'''
  trimmed_activities = {}
  trimmed_activities["issue_url"] = click["issue_url"]
  trimmed_activities["click_timestamp"] = click["timestamp"]
  trimmed_activities["activity_type"] = activities["type"]
  trimmed_activities["activity_timestamp"] = activities["created_at"]
  return trimmed_activities

def check_events(trimmed_activity, activity_git):
  ''' Filter out specific activities that we don't think are useful '''
  filtered_activities = ["PushEvent","DeleteEvent","GollumEvent","IssueEvent"]
  for activity in filtered_activities:
    if trimmed_activity["activity_type"] == activity:
      return False
    if trimmed_activity["activity_type"] == "IssueCommentEvent":
      if activity_git["payload"]["issue"]["html_url"] != trimmed_activity["issue_url"]:
        print activity_git["payload"]["issue"]["html_url"] 
        print trimmed_activity["issue_url"]
        return False
  return True

#
# Methods for 'frequent-data' table that takes activity data and interprets them
#
def get_info_activity(db):
  '''Get top activity types and their urls'''
  db.execute(''' SELECT activity_type,issue_url FROM activity ORDER BY activity_type ''')
  results = db.fetchall()

  activities = {}

  for row in results:
    if row["activity_type"] not in activities.keys():
      activities[row["activity_type"]] = []
      activities[row["activity_type"]].append(row["issue_url"])
    else:
      activities[row["activity_type"]].append(row["issue_url"])

  final_dict = {
        "titles": {},
        "labels": {},
  }

  title_dict = {}
  label_dict = {}
  
  for key in activities.keys():
    title_array = []
    label_array = []

    for activity in activities[key]:
      db_response = get_title_info_db(db, activity)
      if db_response:
        title_array.append(db_response['title'])
        label_array.append(filter_labels(db_response['labels'])) # db_resp is json
      else:
        print "The url (%s) was not in our issues db!" % activity
    
    final_label_arr = []
    for array in label_array:
      if len(array) != 0:
        for tag in array:
          final_label_arr.append(tag)

    title_dict[key] = title_array
    label_dict[key] = final_label_arr


    label_temp = {"frequencies" : get_frequencies(label_dict[key])}
    title_temp = {"frequencies" : get_frequencies(title_dict[key])}

    label_dict[key] = []
    title_dict[key] = []

    label_dict[key].append(label_temp)
    title_dict[key].append(title_temp)

  final_dict["titles"] = title_dict
  final_dict["labels"] = label_dict
  #print final_dict["labels"]

  return final_dict["labels"], final_dict["titles"]

def filter_labels(label_json):
  label_arr = []
  for label in label_json:
    for key,val in label.iteritems():
      if label['name'] != "help wanted" and label['name'] not in label_arr:
        label_arr.append(label['name'])

  
  return label_arr

def get_title_info_db(db, url):
  ''' Get title info based on url'''
  string = ''' SELECT title,labels,body FROM issues WHERE html_url=\'%s\'''' % (url)
  db.execute(string)
  result = db.fetchone()

  return result


def get_frequencies(db_array):
  #print str(db_array) + "\n"
  string = ""

  for query in db_array:
    string += query + " "
    freq = freq_function(string)
    db_array = freq

  return db_array

def freq_function(string):
  words_to_ignore = ["that","what","with","this","would","from","your","which","while","these", "the", "their", "those", "earch"]
  things_to_strip = [".",",","?",")","(","\"",":",";","'s","'","\\"]
  words_min_size = 4
  words = string.lower().split()

  wordcount = {}
  for word in words:
    for thing in things_to_strip:
      if thing in word:
        word = word.replace(thing,"")
    if word not in words_to_ignore and len(word) >= words_min_size:
      if word in wordcount:
        wordcount[word] += 1
      else:
        wordcount[word] = 1

  sortedbyfrequency =  sorted(wordcount,key=wordcount.get,reverse=True)

  return wordcount, sortedbyfrequency

def get_compare_activity_summary(db):
  db.execute('''SELECT title,labels,html_url FROM issues''')

  results = db.fetchall()

  issues = []

  for row in results:
    if row["html_url"] not in issues:
      issues.append({
        "url":row["html_url"],
        "title":row["title"],
        "labels":row["labels"]
        })

  title_dict = {}
  label_dict = {}

  label_array = []
  title_array = []

  for issue in issues:
    if issue["title"] and issue["labels"]:
      title_array.append(issue["title"])
      label_array.append(filter_labels(issue["labels"])) # db_resp is json

  final_label_arr = []
  for array in label_array:
    if len(array) != 0:
      for tag in array:
        if tag not in final_label_arr:
          final_label_arr.append(tag)

  # print final_label_arr
  label_dict["labels"] = final_label_arr
  title_dict["titles"] = title_array

  final_dict = {
      "titles": {},
      "labels": {},
  }
  string = ""

  for key in title_dict["titles"]:
    string += key + " "
  
  freq = freq_function(string)
  final_dict["titles"] = freq

  string = ""

  for key in label_dict["labels"]:
    string += key + " "

  freq = freq_function(string)
  final_dict["labels"] = freq
  
  return final_dict

def get_top_activity(db):
    ''' Get the top five activity types '''
    db.execute(''' SELECT activity_type FROM activity ''')
    results = db.fetchall()

    activities = {}
    for row in results:
        if row["activity_type"] not in activities.keys():
            activities[row["activity_type"]] = 1
        else:
            activities[row["activity_type"]] += 1
    return activities

def get_activity_summaries_array(db):
    activity_summary_array = []
    activity_summary = get_info_activity(db)
    counts = get_top_activity(db)
    titles = activity_summary["titles"]
    labels = activity_summary["labels"]

    for key,value in titles.iteritems():
        new_dict = {
            "activity_type": key,
            "common_titles": value
            }
        activity_summary_array.append(new_dict)

    for key,value in labels.iteritems():
        for entry in activity_summary_array:
            if key == entry["activity_type"]:
                entry["common_labels"] = value
 
    for key,value in counts.iteritems():
        for entry in activity_summary_array:
            if key == entry["activity_type"]:
                entry["count"] = value

    return activity_summary_array

