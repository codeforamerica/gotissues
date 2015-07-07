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
