''' view_helpers.py: This file includes helper functions for the views
    redirects, logic for multiple views
'''
import operator

#
# Index
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


def get_top_acivity(db):
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

def get_info_activity(db):
  '''Get top activity types and their urls'''
  db.execute(''' SELECT activity_type,issue_url FROM activity ''')
  results = db.fetchall()

  activities = {}

  for row in results:
    if row["activity_type"] not in activities.keys():
      activities[row["activity_type"]] = []
      activities[row["activity_type"]].append(row["issue_url"])
    else:
      activities[row["activity_type"]].append(row["issue_url"])
  return activities

def get_title_info(db, activities):
  title_dict = {}
  for key,val in activities.iteritems():
    for url in activities[key]:
      if key in title_dict:
        title_dict[key].append(get_title_info_db(db, url))
      else:
        title_dict[key] = []
        title_dict[key].append(get_title_info_db(db, url))
  print str(title_dict) + "\n\n"
  return title_dict

def get_title_info_db(db, url):
  ''' Get title info based on url'''
  string = ''' SELECT title FROM issues WHERE html_url=\'%s\'''' % (url)
  db.execute(string)
  result = db.fetchone()

  return result

def get_all_activity(db):
  ''' Get all the activity '''
  db.execute(''' SELECT * FROM activity ORDER BY activity_type''')
  results = db.fetchall()

  return results

def get_edited_activity(db, order, category):
  ''' Get edited activity '''
  categories = ["Activity Type", "Issue Url"]
  category = str(category)
  if category == categories[0]:
    category = "activity_type"
  elif category == categories[1]:
    category = "issue_url"

  string = '''SELECT * FROM activity ORDER BY %s %s''' % (category, order)
  print string
  db.execute(string)
  results = db.fetchall()

  return results
