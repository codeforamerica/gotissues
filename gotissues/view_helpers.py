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
# data["activity_summary"]
#
def get_activity_summaries_array(db):
  ''' Get label/title/count summary info from db '''
  activity_summary_array = []
  activity_summary = get_activity_summary(db) #Multiple functions defined below
  counts = get_activity_types(db)
  titles = activity_summary["titles"]
  labels = activity_summary["labels"]

  for key,value in titles.iteritems():
      new_dict = {
          "activity_type": key,
          "common_titles": value
          }
      activity_summary_array.append(new_dict)

  for key,value in labels.iteritems():
      for entry in activity_summary_array:
          if key == entry["activity_type"]:
              entry["common_labels"] = value

  for key,value in counts.iteritems():
      for entry in activity_summary_array:
          if key == entry["activity_type"]:
              entry["count"] = value
  return activity_summary_array

def get_activity_types(db):
  ''' Get frequency of activity types in our activity db'''
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

  return results

def get_activity_summary(db):
  results = get_info_activity(db)
  activities = {}

  for row in results:
    if row["activity_type"] not in activities.keys():
      activities[row["activity_type"]] = []
      activities[row["activity_type"]].append(row["issue_url"])
    else:
      activities[row["activity_type"]].append(row["issue_url"])

  final_dict = {
        "titles": {},
        "labels": {},
  }

  title_dict = {}
  label_dict = {}
  
  for key in activities.keys():
    title_array = []
    label_array = []

    for activity in activities[key]:
      db_response = get_title_info_db(db, activity)
      if db_response:
        title_array.append(db_response['title'])
        label_array.append(filter_labels(db_response['labels'])) # db_resp is json
      else:
        print "The url (%s) was not in our issues db!" % activity
    
    final_label_arr = []
    for array in label_array:
      if len(array) != 0:
        for tag in array:
          final_label_arr.append(tag)

    title_dict[key] = title_array
    label_dict[key] = final_label_arr


    label_temp = {"frequencies" : get_frequencies(label_dict[key])}
    title_temp = {"frequencies" : get_frequencies(title_dict[key])}

    label_dict[key] = []
    title_dict[key] = []

    label_dict[key].append(label_temp)
    title_dict[key].append(title_temp)

  final_dict["titles"] = title_dict
  final_dict["labels"] = label_dict

  return final_dict

def filter_labels(label_json):
  ''' We can't have help-wanted as a top label since it's required to add usually '''
  label_arr = []
  for label in label_json:
    for key,val in label.iteritems():
      if label['name'] != "help wanted" and label['name'] not in label_arr:
        label_arr.append(label['name'])

  
  return label_arr

def get_title_info_db(db, url):
  ''' Get title/label info based on url'''
  string = ''' SELECT title,labels FROM issues WHERE html_url=\'%s\'''' % (url)
  db.execute(string)
  result = db.fetchone()

  return result


def get_frequencies(db_array):
  ''' Takes an array of words and creates a string and returns a Tuple of frequencies'''
  string = ""

  for query in db_array:
    string += query + " "
    freq = freq_function(string)
    db_array = freq

  return db_array

def freq_function(string):
  ''' Takes in a string of words and returns a Tuple:
  1) A dictionary that has the word and it's frequency within the string, not sorted
  2) An array of words, sorted by frequency '''
  words_to_ignore = ["that","what","with","this","would","from","your","which","while","these", "the", "their", "those", "earch"]
  things_to_strip = [".",",","?",")","(","\"",":",";","'s","'","\\"]
  words_min_size = 4
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

  return wordcount, sortedbyfrequency


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
  print string
  db.execute(string)
  results = db.fetchall()

  return results