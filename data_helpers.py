''' one function that can talk to google! '''
from gotissues import *
# Variables
GOOGLE_ANALYTICS_PROFILE_ID = "41226190"
GOOGLE_SERVICE_ACCOUNT_EMAIL = os.environ["GOOGLE_SERVICE_ACCOUNT_EMAIL"]
GOOGLE_SERVICE_ACCOUNT_SECRET_KEY = os.environ["GOOGLE_SERVICE_ACCOUNT_SECRET_KEY"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]

def login_to_google_analytics():
    credentials = SignedJwtAssertionCredentials(GOOGLE_SERVICE_ACCOUNT_EMAIL, GOOGLE_SERVICE_ACCOUNT_SECRET_KEY,
    'https://www.googleapis.com/auth/analytics.readonly')
    http = Http()
    credentials.authorize(http)
    service = build("analytics", "v3", http=http)
    return service, credentials.access_token

service, access_token = login_to_google_analytics()

#
# Methods that return data from Google Analytics
#
choice_dict = {
    "clicked_issues": {
      'metrics':'ga:totalEvents',
      'dimensions':'ga:eventLabel',
      'sort':'-ga:totalEvents',
      'filters':'ga:eventCategory==Civic Issues;ga:eventLabel=@github.com',
      'max_results':None,
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
      'dimensions':'ga:eventLabel, ga:date',
      'sort':'-ga:date',
      'filters':'ga:eventCategory==Civic Issues',
      'max_results':1,
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
      'filters':'ga:eventCategory=@Civic Issues',
      'max_results':None,
      'fields':None
    },

    "viewed_issues": {
      'metrics':'ga:totalEvents',
      'dimensions':'ga:eventLabel',
      'sort':'-ga:totalEvents',
      'filters':'ga:eventCategory==Civic Issue View',
      'max_results':20,
      'fields':None
    }
}

def edit_request_query(choice_dict_query):
  results = service.data().ga().get(
          ids="ga:" + GOOGLE_ANALYTICS_PROFILE_ID,
          start_date='2014-08-24',
          end_date=datetime.date.today().strftime("%Y-%m-%d"),
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
    most_recent_clicked_issue = results["rows"][0][0]
    return most_recent_clicked_issue

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