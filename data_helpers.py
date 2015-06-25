''' one function that can talk to google! '''
from gotissues import *


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
      'sort':'-ga:totalEvents',
      'filters':'ga:eventCategory==Civic Issues;ga:eventLabel=@github.com',
      'max_results':5,
      'fields':'rows'
    },

    "most_clicked": {
      'metrics':'ga:totalEvents',
      'dimensions':'ga:eventLabel',
      'sort':'ga:totalEvents',
      'filters':'ga:eventCategory==Civic Issues;ga:eventLabel=@github.com',
      'max_results':5,
      'fields':'rows'
    },

    "recently_clicked": {
      'metrics':'ga:totalEvents',
      'dimensions':'ga:eventLabel, ga:date',
      'sort':'-ga:dates',
      'filters':'ga:eventCategory==Civic Issues;ga:eventLabel=@github.com',
      'max_results':None
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
      'filters':'ga:pagePath=@Civic Issues',
      'max_results':None,
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
  
  print "THE RESULTS"
  print results
  return results

def get_analytics_query(choice):
  #choice_list = ["clicked_issues", "top_cities"]
  
  if choice == "clicked_issues":
    #print choice_dict[choice]
    results = edit_request_query(choice_dict[choice])
    issues = []
    for row in results["rows"]:
        issue = {
            "url" : row[0],
            "clicks" : row[1]
        }
        issues.append(issue)
    return issues


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
    print "RESULTS ARE FINALLY WORKING"
    print results.keys()
    total_page_views = results["rows"][0][0]
    return total_page_views

  elif choice == "total_clicks":
    print "Dictionary Test\n"
    print choice_dict[choice]['metrics']
    results = edit_request_query(choice)
    total_clicks = results["rows"][0][0]
    return total_clicks

def get_percentage_of_views_with_clicks(total_clicks, total_page_views):
    ''' What percentage of views have a click? '''
    clicks_per_view = ( float(total_clicks) / float(total_page_views) ) * 100
    return int(clicks_per_view)


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