import json
from data_helpers import *

def github_html_url_to_api(url):
    """ Convert https://github.com links to https://api.gitub.com """
    if url.startswith('https://github.com/'):
        return "https://api.github.com/repos/" + url[19:]
    else:
        return url


def get_clicked_issue_github_data(clicked_issues, limit=None):
    """ Get all the github data about all the clicked issues """
    github_issues = []
    for github_issue in clicked_issues[0:limit]:
        # Convert to api url
        github_api_url = github_html_url_to_api(github_issue["url"])
        got = get_github_with_auth(github_api_url)
        issue = got.json()
        issue["clicks"] = github_issue["clicks"]
        # print json.dumps(issue, indent=4, sort_keys=True)
        github_issues.append(issue)

    return github_issues


def trim_github_issues(github_issues):
    """ Trim the github issues down to only the attributes we want """
    trimmed_issues = []
    for issue in github_issues:
        for key in issue.keys():
            github_attr = ["id", "html_url", "title", "labels",
                           "state", "comments", "created_at",
                           "body", "closed_at", "closed_by", "clicks"]
            if key not in github_attr:
                del issue[key]
        trimmed_issues.append(issue)

    return trimmed_issues


def add_views_to_issues(trimmed_issues, viewed_issues):
    ''' Add the number of views and sources to each issue '''
    issues = []
    for issue in trimmed_issues:
        found = find(viewed_issues,"url",issue["html_url"])
        if found:
            issue["views"] = viewed_issues[found]["views"]
            issue["view_sources"] = viewed_issues[found]["view_sources"]

    return trimmed_issues

def github_issue_url_to_project(url):
    ''' Convert https://api.github.com/repos/:org/:repo/issues/:no
    to https://api.github.com/repos/:org/:repo/events '''
    issue_var = url.split("/")[7]
    url = url.replace("issues/" + str(issue_var), 'events')
    return url

def get_timestamp_issue_github_data(clicked_issues, limit=None):
    """ Get all the github data about all the clicked issues """
    """ This has gotten pretty hairy. Please break into smaller pieces"""
    github_issues = []
    good_timestamps = []
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
                if result < datetime.timedelta(days=2):
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


        if timestamp_dict["nearby_events"]:
            good_timestamps.append(timestamp_dict)
        #   print json.dumps(issue, indent=4, sort_keys=True)
        # github_issues.append(timestamp_dict)




# Get the Github data for those clicked issues
# Set the limit to 1 for testing
# github_issues = get_timestamp_issue_github_data(recent_issues, limit=100)

def write_issue_to_db(issue, db):
    """ Write the issue to the database """
    # Check if the issue already exists
    query = ''' SELECT * FROM issues WHERE id = %s '''
    db.execute(query, (issue["id"],))

    if db.fetchone():
        # UPDATE
        q = ''' UPDATE issues SET (id, html_url, title, body, labels, state,
                      comments, created_at, closed_at, closed_by, clicks,
                      views, view_sources)
                = ( %s, %s, %s, %s, %s::json, %s, %s, %s, %s, %s::json, %s, %s, %s)
            '''
    else:
        # INSERT
        q = ''' INSERT INTO issues (id, html_url, title, body, labels, state,
                      comments, created_at, closed_at, closed_by, clicks,
                      views, view_sources)
                VALUES ( %s, %s, %s, %s, %s::json, %s, %s, %s, %s, %s::json, %s, %s, %s)
            '''

    db.execute(q, (issue["id"], issue["html_url"], issue["title"], issue["body"],
                       json.dumps(issue["labels"]), issue["state"],
                       issue["comments"], issue["created_at"],issue["closed_at"],
                       json.dumps(issue["closed_by"]), issue["clicks"],
                       issue["views"], issue["view_sources"]))


if __name__ == '__main__':
    # Get all the clicked issues from Google Analytics
    clicked_issues = get_analytics_query("clicked_issues")
    # Get the viewed issues from GA
    viewed_issues = get_analytics_query("viewed_issues")

    # Get the Github data for those clicked issues
    # Set the limit to 1 for testing
    github_issues = get_clicked_issue_github_data(clicked_issues, limit=None)
    trimmed_issues = trim_github_issues(github_issues)
    issues = add_views_to_issues(github_issues, viewed_issues)
    # recent_issues = get_analytics_query("recently_clicked")

    # print json.dumps(issues, indent=4, sort_keys=True)

    # Add each issue to the db
    with connect(os.environ['DATABASE_URL']) as conn:
        with db_cursor(conn) as db:
            for issue in issues:
                write_issue_to_db(issue, db)
