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

  title_dict = {}
  label_dict = {}
  desc_dict = {}
  for key in activities.keys():
    title_array = []
    label_array = []
    desc_array = []
    for activity in activities[key]:
      # Write Test for these
      if get_title_info_db(db, activity):
        db_response = get_title_info_db(db, activity)
        title_array.append(db_response['title'])
        label_array.append(filter_labels(db_response['labels'])) # db_resp is json
        desc_array.append(db_response['body']) #db_resp is text
      else:
        print "\nThe url (%s) was not in our issues db!!!\n" % activity
    
    final_label_arr = []
    for array in label_array:
      if len(array) != 0:
        for tag in array:
          if tag not in final_label_arr:
            final_label_arr.append(tag)

    title_dict[key] = title_array
    label_dict[key] = final_label_arr
    desc_dict[key] = desc_array

  label_dict = get_frequencies(label_dict) 
  title_dict = get_frequencies(title_dict)
  #print "common labels"
  #print label_dict
    # print desc_dict

  # final_dict = [title_dict, label_dict, desc_dict] #add title, label, desc

  return title_dict, label_dict

def filter_labels(label_json):
  label_arr = []
  for label in label_json:
    for key,val in label.iteritems():
      if label['name'] != "help wanted" and label['name'] not in label_arr:
        label_arr.append(label['name'])

  
  return label_arr

def get_title_info_db(db, url):
  ''' Get title info based on url'''
  string = ''' SELECT title,labels,body FROM issues WHERE html_url=\'%s\'''' % (url)
  db.execute(string)
  result = db.fetchone()

  return result

# def comment info is next

def get_frequencies(db_dict):

  for key,val in db_dict.iteritems():
    string = ""
    for title in db_dict[key]:
      string += title + " "
    freq = freq_function(string)[:5]
    db_dict[key] = freq
  # print "Events With Top Title Frequencies"
  # print db_dict

  return db_dict

def freq_function(string):
  words_to_ignore = ["that","what","with","this","would","from","your","which","while","these", "the", "their", "those", "earch"]
  things_to_strip = [".",",","?",")","(","\"",":",";","'s","'"]
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
  # print sortedbyfrequency
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
