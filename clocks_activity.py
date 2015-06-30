import json
from data_helpers import *

def github_html_url_to_api(url):
    """ Convert https://github.com links to https://api.gitub.com """
    if url.startswith('https://github.com/'):
        return "https://api.github.com/repos/" + url[19:]
    else:
        return url

def github_issue_url_to_project(url):
	''' Convert https://api.github.com/repos/:org/:repo/issues/:no
	to https://api.github.com/repos/:org/:repo/events '''
	issue_var = url.split("/")[7]
	url = url.replace("issues/" + str(issue_var), 'events')
	return url

def get_timestamp_issue_github_data(clicked_issues, limit=None):
    """ Get all the github data about all the clicked issues """
    github_issues = []
    for github_issue in clicked_issues[0:limit]:
        # Convert to api url
        github_api_url = github_html_url_to_api(github_issue["url"])
        got = get_github_with_auth(github_api_url)
        issue = got.json() #response for issue call
        github_project_api_url = github_issue_url_to_project(github_api_url)
        project = get_github_with_auth(github_project_api_url) 
        all_project_events = project.json() # response for project call
        project_event_array = []
        for project_event in all_project_events:
        	for key in project_event.iterkeys():
        		action_time = project_event["created_at"]
        		click_time = github_issue["timestamp"]

        		action_time = datetime.datetime.strptime(action_time, '%Y-%m-%dT%H:%M:%SZ')
	        	click_time = datetime.datetime.strptime(click_time, '%Y-%m-%dT%H:%M:%S')

	        	result = click_time - action_time
	        	if result < datetime.timedelta(days=1):
	        		print click_time
	        		print action_time
	        		nearby_dict = {
        		    "type":project_event["type"],
        		    "created_at":project_event["created_at"]
        			}
	        		project_event_array.append(nearby_dict)
				
        timestamp_dict = {
            "timestamp":github_issue["timestamp"],
            "issue_id":issue["id"],
            "nearby_events":project_event_array
        }
        print timestamp_dict
        # print json.dumps(issue, indent=4, sort_keys=True)
        # github_issues.append(timestamp_dict)



recent_issues = get_analytics_query("recently_clicked")

# Get the Github data for those clicked issues
# Set the limit to 1 for testing
github_issues = get_timestamp_issue_github_data(recent_issues, limit=None)
