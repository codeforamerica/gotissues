import json
from data_helpers import *
from github_bot import *

def get_clicked_issue_github_data(clicked_issues, limit=None):
    """ Get all the github data about all the clicked issues """
    github_issues = []
    for github_issue in clicked_issues[0:limit]:
        # Convert to api url
        github_api_url = github_html_url_to_api(github_issue["url"])
        got = get_github_with_auth(github_api_url)
        if got:
            issue = got.json()
            issue["clicks"] = github_issue["clicks"]
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
        issue["views"] = None
        issue["view_sources"] = None

    found = find(viewed_issues,"url",issue["html_url"])
    if found:
        issue["views"] = viewed_issues[found]["views"]
        issue["view_sources"] = viewed_issues[found]["view_sources"]

    return trimmed_issues

def write_issue_to_db(issue, db):
    """ Write the issue to the database """
    # Check if the issue already exists
    query = ''' SELECT * FROM issues WHERE id = %s '''
    db.execute(query, (issue["id"],))

    if db.fetchone():
        # UPDATE
        q = ''' UPDATE issues SET (html_url, title, body, labels, state,
            comments, created_at, closed_at, closed_by, clicks,
            views, view_sources)
            = ( %(html_url)s, %(title)s, %(body)s, %(labels)s::json, %(state)s, %(comments)s, %(created_at)s, %(closed_at)s, %(closed_by)s::json, %(clicks)s, %(views)s, %(view_sources)s)
            WHERE id = %(id)s
            '''
    else:
        # INSERT
        q = ''' INSERT INTO issues (id, html_url, title, body, labels, state,
            comments, created_at, closed_at, closed_by, clicks,
            views, view_sources)
            VALUES ( %(id)s, %(html_url)s, %(title)s, %(body)s, %(labels)s::json, %(state)s, %(comments)s, %(created_at)s, %(closed_at)s, %(closed_by)s::json, %(clicks)s, %(views)s, %(view_sources)s)
            '''

    db.execute(q, {"id":issue["id"], "html_url":issue["html_url"], "title":issue["title"],
            "body":issue["body"], "labels":json.dumps(issue["labels"]), "state":issue["state"],
            "comments":issue["comments"], "created_at": issue["created_at"], "closed_at": issue["closed_at"],
            "closed_by":json.dumps(issue["closed_by"]), "clicks":issue["clicks"], "views":issue["views"],
            "view_sources":issue["view_sources"]})


def write_click_to_db(click, db):
    """ Write the click to the database """
    # Check if the click already exists
    query = ''' SELECT * FROM "clicks" WHERE issue_url = %(issue_url)s AND timestamp = %(timestamp)s '''
    db.execute(query, {"issue_url" : click["issue_url"], "timestamp": click["timestamp"]})

    if not db.fetchone():
        # INSERT
        q = ''' INSERT INTO clicks (issue_url, timestamp, readable_date)
            VALUES ( %(issue_url)s, %(timestamp)s, %(readable_date)s)
            '''

        db.execute(q, {"issue_url": click["issue_url"], "timestamp": click["timestamp"],
            "readable_date": click["readable_date"]})


def get_top_activity(db):
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

def write_activities_to_db(activity, db):
    # Check if the activity already exists
    q = ''' SELECT * FROM activity WHERE activity_type = %(activity_type)s AND activity_timestamp = %(activity_timestamp)s AND click_timestamp = %(click_timestamp)s'''
    db.execute(q, {"activity_type": activity["activity_type"],
        "activity_timestamp": activity["activity_timestamp"],
        "click_timestamp": activity["click_timestamp"]})

    if not db.fetchone():
        q = ''' INSERT INTO activity (issue_url, click_timestamp, activity_type, activity_timestamp)
            VALUES ( %(issue_url)s, %(click_timestamp)s, %(activity_type)s, %(activity_timestamp)s)
            '''
        db.execute(q, {"issue_url": activity["issue_url"],
            "click_timestamp": activity["click_timestamp"], "activity_type": activity["activity_type"],
            "activity_timestamp": activity["activity_timestamp"]})

def write_activity_summary_to_db(activity_info, db):
    # Check if the activity already exists
    q = ''' SELECT * FROM activity_summary WHERE activity_type = %(activity_type)s '''
    db.execute(q, {"activity_type": activity_info["activity_type"]})
    exists = db.fetchone()

    if exists:
        # Update
        q = ''' UPDATE activity_summary SET (common_titles, common_labels, count)
            = ( %(common_titles)s, %(common_labels)s, %(count)s )
                WHERE activity_type = %(activity_type)s
            '''
        db.execute(q, {"activity_type":activity_info["activity_type"], "common_titles":activity_info["common_titles"], 
            "common_labels":activity_info["common_labels"], "count":activity_info["count"]})


    if not exists:
        # Insert
        q = ''' INSERT INTO activity_summary (activity_type, common_titles, common_labels, count)
            VALUES ( %(activity_type)s, %(common_titles)s, %(common_labels)s, %(count)s)
            '''
        db.execute(q, {"activity_type":activity_info["activity_type"], "common_titles":activity_info["common_titles"], 
            "common_labels":activity_info["common_labels"], "count":activity_info["count"]})


if __name__ == '__main__':

    # Get todays clicked issues from Google Analytics
    clicked_issues = get_analytics_query("clicked_issues")
    # Get todays viewed issues from Google Analytics
    viewed_issues = get_analytics_query("viewed_issues")

    # Get the Github data for todays clicked issues, clicks, and views
    # Set the limit to 1 for testing
    github_issues = get_clicked_issue_github_data(clicked_issues, limit=None)
    trimmed_issues = trim_github_issues(github_issues)
    issues = add_views_to_issues(github_issues, viewed_issues)

    # Get all of todays clicks
    clicks = get_analytics_query("all_clicks")

    # Get all of todays clicks activity
    activities = get_click_activity(clicks)


    #Add each issue to the db
    with connect(os.environ['DATABASE_URL']) as conn:
        with dict_cursor(conn) as db:
            for issue in issues:
                write_issue_to_db(issue, db)

            for click in clicks:
                write_click_to_db(click,db)

            for activity in activities:
                write_activities_to_db(activity, db)

            activity_summary = get_activity_summaries_array(db)

            for summary in activity_summary:
                # Labels
                if summary["common_labels"][0]["frequencies"]:
                    labels = summary["common_labels"][0]["frequencies"][1][:5]
                else:
                    labels = None

                # Titles
                if summary["common_titles"][0]["frequencies"]:
                    titles = summary["common_titles"][0]["frequencies"][1][:5]
                else:
                    titles = None
                
                new_dict = {
                    "activity_type": summary["activity_type"],
                    "common_labels": labels,
                    "common_titles": titles,
                    "count": summary["count"]
                }

                write_activity_summary_to_db(new_dict, db)

