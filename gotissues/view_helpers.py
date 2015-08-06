''' view_helpers.py: This file includes helper functions for the views
    redirects, logic for multiple views
'''
import operator

#
# Index
#

#
# data["sources"]
#
def get_top_sources(db):
  ''' Get the top 5 view sources '''
  q = ''' SELECT view_sources FROM issues WHERE view_sources IS NOT NULL '''

  db.execute(q)
  view_sources = db.fetchall()

  sources = {}
  for row in view_sources:
    for source in row["view_sources"]:
      if source.startswith("https://"):
        source = source.replace("https://","http://")
      if source not in sources.keys():
        sources[source] = 1
      else:
        sources[source] += 1
  sorted_sources = sorted(sources.items(), key=operator.itemgetter(1), reverse=True)
  return sorted_sources


#
# data["total_count"]
#
def get_total_count(db):
  ''' Pull out the number of closed issues from our database '''
  q = ''' SELECT COUNT(*) FROM issues '''

  db.execute(q)
  total_count = db.fetchone()["count"]
  return total_count

#
# data["closed_count"]
#
def get_closed_count(db):
  ''' Pull out the number of closed issues from our database '''
  q = ''' SELECT COUNT(*) FROM issues WHERE state = 'closed' '''

  db.execute(q)
  closed_count = db.fetchone()["count"]
  return closed_count

#
# data["open_count"]
#
def get_open_count(db):
  ''' Pull out the number of closed issues from our database '''
  q = ''' SELECT COUNT(*) FROM issues WHERE state = 'open' '''

  db.execute(q)
  open_count = db.fetchone()["count"]
  return open_count

#
# data["top_clicks"]
#
def get_most_clicked(db, N):
  ''' Pull out the top N issues from our database '''
  q = ''' SELECT html_url,clicks,views,title,labels,created_at,view_sources,body,comments FROM issues WHERE views IS NOT NULL ORDER BY clicks DESC'''
  db.execute(q)
  most_count = db.fetchmany(size=N)
  for dic in most_count:
    #print dic["body"]
    #print "\n\n BREAK"
    dic["click-ratio"] = int(100*dic["clicks"]/float(dic["views"]))
    dic["created_at"] = dic["created_at"].strftime('%B %Y')
  return most_count

#
# data["least_clicks"]
#
def get_least_clicked(db, N):
  ''' Pull out the bottom N issues from our database '''
  q = ''' SELECT html_url,clicks,views,title,labels,created_at,view_sources,body,comments FROM issues WHERE views IS NOT NULL ORDER BY clicks ASC'''
  db.execute(q)
  least_count = db.fetchmany(size=N)
  for dic in least_count:
    dic["click-ratio"] = int(100*dic["clicks"]/float(dic["views"]))
    dic["created_at"] = dic["created_at"].strftime('%B %Y')
  return least_count

#
# data["closed_clicks"]
#
def get_closed_clicked(db, N):
  ''' Pull out the bottom N issues from our database '''
  q = ''' SELECT html_url,clicks,title,labels,created_at,closed_at,comments FROM issues WHERE state='closed' ORDER BY clicks DESC'''
  db.execute(q)
  closed = db.fetchmany(size=N)
  for dic in closed:
    dic["days_open"] = (dic["closed_at"] - dic["created_at"]).days
    dic["created"] = dic["created_at"]
    dic["closed"] = dic["closed_at"]
    dic["created_at"] = dic["created_at"].strftime('%B %Y')
    dic["closed_at"] = dic["closed_at"].strftime('%B %Y')

  return closed


#
# data['pinged_issues']
#
def get_pinged_issues(db):
  q = '''SELECT * FROM pinged_issues '''

  db.execute(q)
  results = db.fetchall()
  return results

#
# db_results in analytics
#
def get_all_activity(db):
  ''' Get all the activity '''
  db.execute(''' SELECT * FROM activity ORDER BY activity_type''')
  results = db.fetchall()

  return results

#
# changing db_results in analytiics
#
def get_edited_activity(db, order, category):
  ''' Get edited activity '''
  categories = ["Activity Type", "Issue Url"]
  category = str(category)
  if category == categories[0]:
    category = "activity_type"
  elif category == categories[1]:
    category = "issue_url"

  string = '''SELECT * FROM activity ORDER BY %s %s''' % (category, order)

  db.execute(string)
  results = db.fetchall()

  return results

#
# data["activity_summary"]
#
def get_activity_summary(db):
  ''' Get activity summary table info '''
  db.execute('''SELECT * FROM activity_summary ORDER BY activity_type''')
  results = db.fetchall()

  return results

#
# data["total_pinged"] in analytics
#
def get_total_pinged(db):
  ''' Pull out the number of closed issues from our database '''
  q = ''' SELECT COUNT(*) FROM pinged_issues '''

  db.execute(q)
  total_count = db.fetchone()["count"]
  return total_count

#
# data["closed_pinged"] in analytics
#
def get_issue_status(db, html_url):
  ''' Pull out the number of closed issues from our database '''

  q = ''' SELECT state FROM issues WHERE html_url=\'%s\'''' % (html_url)

  db.execute(q)
  issue_status = db.fetchone()["state"]
  return issue_status

def count_closed(db, issue_list):
  total_closed = 0
  for issue in issue_list:
    status = get_issue_status(db, issue["html_url"])
    if status =="closed":
      total_closed += 1

  return total_closed

#
# Figure out of there have been changes in activity in the issues we've pinged
#

def check_issues(db, ping):
  final_data = []
  comment_delta = 0
  state_delta = False

  check_ping = check_pinged_status(db, ping["html_url"])

  if ping.get("comments"):
    if ping["comments"] - check_ping["comments"] > 1:
      comment_delta = ping["comments"] - check_ping["comments"]
    else:
      comment_delta = 0
  else:
    comment_delta = 0

  if check_ping["state"] == "closed":
    state_delta = True
  
  ping["comment_delta"] = comment_delta
  ping["state_delta"] = state_delta

  return ping


def check_pinged_status(db, html_url):
  q = '''SELECT html_url,state,comments FROM issues WHERE html_url = '%s' ''' % html_url

  db.execute(q)
  new_status = db.fetchone()
  return new_status