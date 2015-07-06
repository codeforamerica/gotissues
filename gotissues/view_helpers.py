''' view_helpers.py: This file includes helper functions for the views
    redirects, logic for multiple views
'''

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
      # source = source.replace("https://","").replace("http://","")
      if source not in sources.keys():
        sources[source] = 1
      else:
        sources[source] += 1
  return sources


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