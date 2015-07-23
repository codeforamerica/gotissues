from psycopg2 import connect, extras
import requests
import json

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

#
# Github url related methods
#
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
    q = ''' SELECT html_url,clicks,view_sources FROM issues WHERE html_url=\'%s\'''' % (url)
  else:
    q = ''' SELECT html_url,clicks,view_sources,created_at FROM issues WHERE state='open' ORDER BY created_at ASC'''

  db.execute(q)
  results = db.fetchall()
  return results

def post_on_github(url, body=None, headers=None):
  ''' Post either a specific message to the brigades or a generic one based on if there are sources or not '''
  print "Requesting %s" % (url["html_url"])
  if body:
    post = {"body":body}
  else:
    if url["view_sources"] and url['clicks']:
      clicks = str(url["clicks"])
      top_source = str(url["view_sources"][0])
      post = {"body":"""Hello! Do you still need help with this issue? It's been
      clicked on %s times through the [Civic Issue Finder](https://www.codeforamerica.org/geeks/civicissues)
      on %s.\nCan this issue be closed or does it still need some assistance? You can
      always update the labels or add more info in the description to make it
      easier to contribute. \n Just doing a little open source gardening of Brigade 
      projects! For more info/tools for creating civic issues, check out [Got Issues](https://got-issues.herokuapp.com/)
      Thank you!"""} % (clicks, top_source)
    
    elif url['clicks']:
      clicks = str(url['clicks'])
      text = ''' Hello! Do you still need help with this issue? It's been clicked 
      on %s times through the [Civic Issue Finder](https://www.codeforamerica.org/geeks/civicissues)!
      \nCan this issue be closed or does it still need some assistance? You can
      always update the labels or add more info in the description to make it
      easier to contribute. \n\n Just doing a little open source gardening of Brigade 
      projects! For more info/tools for creating civic issues, check out [Got Issues](https://got-issues.herokuapp.com/).
      Thank you!''' % (clicks)
      post = {
        "body": text
      }
  print post["body"]

  if github_html_url_to_api(url["html_url"]):
    #auth_url = github_html_url_to_api(url["html_url"]) + "/comments"
    #r = requests.post(auth_url, json.dumps(post), auth=github_auth, headers=headers)
    print "Successfully posted to %s" % (url["html_url"])
    return "success"

  else:
    print "Error. Could not post to invalid url: %s" % (url["html_url"])
    return "error"

''' Fetch urls from the db '''  
with connect(os.environ['DATABASE_URL']) as conn:
  with dict_cursor(conn) as db:
    # test issue url
    # url = 'https://github.com/codeforamerica/gotissues/issues/36'
    # url_list = get_urls(db, url)
    url_list = get_urls(db)
    posted_list = []

    for url in url_list:
      response = None
      while not response:
        print "Reply 'y' or 'n'. We are about to post on %s. \n Last Updated: %s" % (url["html_url"], url["created_at"])
        response = raw_input()
        if response == "y":
          posted_list.append({
            "url":url["html_url"],
            "status":post_on_github(url)
          })
        elif response == "n":
          print "Not posted to Github"
        else:
          print "Please re-enter a valid character\n"
          response = None
