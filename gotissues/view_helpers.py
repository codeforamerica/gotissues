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
  q = ''' SELECT html_url,clicks,views,title,labels,created_at,view_sources FROM issues WHERE views IS NOT NULL ORDER BY clicks DESC'''
  db.execute(q)
  most_count = db.fetchmany(size=N)
  for dic in most_count:
    dic["click-ratio"] = int(100*dic["clicks"]/float(dic["views"]))
    dic["created_at"] = dic["created_at"].strftime('%B %Y')
  return most_count

#
# data["least_clicks"]
#
def get_least_clicked(db, N):
  ''' Pull out the bottom N issues from our database '''
  q = ''' SELECT html_url,clicks,views,title,labels,created_at,view_sources FROM issues WHERE views IS NOT NULL ORDER BY clicks ASC'''
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
# db_results in admin
#
def get_all_activity(db):
  ''' Get all the activity '''
  db.execute(''' SELECT * FROM activity ORDER BY activity_type''')
  results = db.fetchall()

  return results

#
# changing db_results in admin
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