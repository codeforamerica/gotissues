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
  db.execute(''' SELECT activity_type,issue_url FROM activity ORDER BY activity_type ''')
  results = db.fetchall()

  activities = {}

  for row in results:
    if row["activity_type"] not in activities.keys():
      activities[row["activity_type"]] = []
      activities[row["activity_type"]].append(row["issue_url"])
    else:
      activities[row["activity_type"]].append(row["issue_url"])

  title_array = {}
  for key in activities.keys():
    key_array = []
    for activity in activities[key]:
      # Write Test
      if get_title_info_db(db, activity):
        key_array.append(get_title_info_db(db, activity)['title'])
      else:
        print "\nThe url (%s) was not in our issues db!!!\n" % activity
    title_array[key] = key_array


  title_array = get_frequencies(title_array)

  return title_array

def get_title_info_db(db, url):
  ''' Get title info based on url'''
  string = ''' SELECT title FROM issues WHERE html_url=\'%s\'''' % (url)
  db.execute(string)
  result = db.fetchone()

  return result

# def comment info is next

def get_frequencies(db_dict):

  for key,val in db_dict.iteritems():
    string = ""
    for title in db_dict[key]:
      string += title + " "
    freq = freq_function(string)
    db_dict[key] = freq
  print "Events With Top Title Frequencies"
  print db_dict

  return db_dict

def freq_function(string):
  words_to_ignore = ["that","what","with","this","would","from","your","which","while","these", "the"]
  things_to_strip = [".",",","?",")","(","\"",":",";","'s"]
  words_min_size = 3
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
  print sortedbyfrequency
  return sortedbyfrequency

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
