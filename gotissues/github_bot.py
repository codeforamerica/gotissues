from psycopg2 import connect, extras

import requests
import json
import datetime

from config import *

#
# Setup for DB
#
def dict_cursor(conn, cursor_factory=extras.RealDictCursor):
    return conn.cursor(cursor_factory=cursor_factory)


#
# Setup for all Github queries
#
if 'GITHUB_TOKEN' in os.environ:
    github_auth = (os.environ['BOT_GITHUB_TOKEN'], '')
else:
    github_auth = None


def github_html_url_to_api(url):
    """ Convert https://github.com links to https://api.gitub.com """
    if url.startswith('https://github.com/'):
        return "https://api.github.com/repos/" + url[19:]
    else:
        return None


#
# Fetch urls that we want to ping
#
def get_urls(db, url=None):
  ''' Search the issues table for specific issues we want to ping, Testing w/ fake added issue'''
  #testing if url is not none
  if url:
    q = ''' SELECT html_url,clicks,view_sources,created_at,comments FROM issues WHERE html_url=\'%s\'''' % (url)
  else:
    q = ''' SELECT html_url,clicks,view_sources,created_at,labels,comments FROM issues WHERE state='open' ORDER BY created_at ASC'''

  db.execute(q)
  results = db.fetchall()
  return results

def filter_issues(results):

  # Only return help wanted labels
  hw_issues = []
  for issue in results:
    labels = issue.get('labels')
    if labels:
      for label in labels:
        if label["name"] == "help wanted":
          hw_issues.append(issue)

  # Only return issues older than a year
  old_issues = []
  for issue in hw_issues:
    today = datetime.datetime.today()
    year_ago = today.replace(year=today.year-1)
    if issue["created_at"] < year_ago:
      old_issues.append(issue)

  # Filter out government issues
  filtered_issues = []
  for issue in old_issues:
    dont_add_flag = False
    for gov_github in ["https://github.com/presidential-innovation-fellows", "https://github.com/uscensusbureau", "https://github.com/chicago", "https://github.com/GSA", "https://github.com/project-open-data", "https://github.com/datasf","https://github.com/18f"]:
      if issue["html_url"].lower().startswith(gov_github.lower()):
        dont_add_flag = True
    if not dont_add_flag:
      filtered_issues.append(issue)

  return filtered_issues


#
# Write the urls that we posted to a db
#
def write_pinged_to_db(ping, db):
  q = ''' INSERT INTO pinged_issues (html_url, status) 
          VALUES ( %(html_url)s, %(status)s) '''

  db.execute(q, {"html_url":ping["html_url"], "status":ping["status"]})

def get_github_post(url):
  ''' Post a generic message to github based on if there are sources or not '''
  print "Requesting %s" % (url["html_url"])

  if url["view_sources"] and url['clicks']:
    issues_url = "/".join(url["html_url"].split("/")[:6])
    clicks = str(url["clicks"])
    top_source = str(url["view_sources"][0])

    text = '''Hello! This issue looks like it still needs help! 
    It's been clicked on %s times through the [Civic Issue Finder](https://www.codeforamerica.org/geeks/civicissues) on [%s](%s). 
    Can this issue be closed or does it still need some assistance? 
    \nIf you wrote this issue, you can always update the labels for specifying tasks, add more info in the description to make it easier to contribute, or re-write the title to make more contributors interested in helping out.
    If you are an open source contributor, ask and see how you can help by commenting or check out more open issues in this repo at [%s](%s). \n\n Just doing a little :seedling: open source gardening :seedling: of Brigade projects! 
    For more info/tools for creating civic issues, check out [Got Issues](https://got-issues.herokuapp.com/) Thank you!''' % (clicks, top_source, top_source, issues_url, issues_url)
    post = {
      "body": text
    }
    return post
  
  elif url['clicks']:
    issues_url = "/".join(url["html_url"].split("/")[:6])
    clicks = str(url['clicks'])

    text = ''' Hello! This issue looks like it still needs help! 
    It's been clicked on %s times through the [Civic Issue Finder](https://www.codeforamerica.org/geeks/civicissues)! 
    Can this issue be closed or does it still need some assistance? 
    \nIf you wrote this issue, you can always update the labels for specifying tasks, add more info in the description to make it easier to contribute, or re-write the title to make more contributors interested in helping out.
    If you are an open source contributor, ask and see how you can help by commenting or check out more open issues in this repo at [%s](%s). \n\n Just doing a little :seedling: open source gardening :seedling: of Brigade projects! 
    For more info/tools for creating civic issues, check out [Got Issues](https://got-issues.herokuapp.com/). Thank you!''' % (clicks, issues_url, issues_url)
    post = {
      "body": text
    }
    return post

  elif not url['clicks']:
    print "Error. No clicks for url: %s" % (url["html_url"])
    return "error"

def post_on_github(url, post, headers=None):
  if github_html_url_to_api(url):
    auth_url = github_html_url_to_api(url) + "/comments"
    r = requests.post(auth_url, json.dumps(post), auth=github_auth, headers=headers)
    print "You just posted: \n" + str(post["body"])
    print "Successfully posted to %s" % (url)
    return "success"

  else:
    print "Error. Could not post to invalid url: %s" % (url["html_url"])
    return "error"


#
# Check if we have already pinged an issue
#
def check_pinged(ping, db):
  q = '''SELECT * FROM pinged_issues WHERE html_url = %(html_url)s '''

  db.execute(q, {"html_url": ping["html_url"]})
  exists = db.fetchone()

  if exists:
    return True
  else:
    return False

#
# Write the urls that we posted to a db
#
def write_pinged_to_db(ping, db):
  q = '''SELECT * FROM pinged_issues WHERE html_url = %(html_url)s '''

  db.execute(q, {"html_url": ping["html_url"]})
  exists = db.fetchone()

  if not exists:
    q = ''' INSERT INTO pinged_issues (html_url, status, comments)
        VALUES ( %(html_url)s, %(status)s, %(comments)s) '''

  db.execute(q, {"html_url":ping["html_url"], "status":ping["status"], "comments":ping["comments"]})

#
# Fetch urls from the db
#
def run_civic_bot():
  with connect(os.environ['DATABASE_URL']) as conn:
    with dict_cursor(conn) as db:

      url_list = filter_issues(get_urls(db))
      # Test Issue Url must have clicks, html_url. created_at and view_sources optional

      # Since this will ping one random url in our url list, make sure the list
      # We are working with doesn't have urls that are already in the database
      new_url_list = []
      for url in url_list:
        if not check_pinged(url, db):
          new_url_list.append(url)

      
      print "The number of potential issues we can ping is " + str(len(new_url_list))
      if new_url_list:
        url = new_url_list[0]
        print "We are about to post on %s.\nLast Updated: %s" % (url["html_url"], url["created_at"])

        ping = {
          "html_url":url["html_url"],
          "status":post_on_github(url["html_url"], get_github_post(url)),
          "comments": url["comments"]
        }
        write_pinged_to_db(ping, db)


if __name__ == '__main__':
  run_civic_bot()
