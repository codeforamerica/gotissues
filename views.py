''' views.py: This file contains all of the routes '''
from gotissues import app
from data_helpers import *

@app.route("/", methods=["GET", "POST"])
def index():
    total_clicks = get_total_clicks()
    total_page_views = get_total_page_views()
    top_clicked_issues = get_top_clicked_issues()
    least_clicked_issues = get_least_clicked_issues()
    most_recent_clicked_issue = get_most_recent_clicked_issue()
    clicks_per_view = get_percentage_of_views_with_clicks(total_clicks, total_page_views)
    issue_list = get_clicked_issues()
    total_issues = len(issue_list)
    top_cities = get_top_city_clicks()
    no_cities = len(top_cities)

    if request.method == "POST":
        check_clicked_github = get_github_data(request.form["issue"])
    else:
        check_clicked_github = []

    #get total number of closed issues differently

    return render_template("index.html",total_clicks=total_clicks,
        total_page_views=total_page_views,
        top_clicked_issues=top_clicked_issues,
        least_clicked_issues=least_clicked_issues, 
        most_recent_clicked_issue=most_recent_clicked_issue,
        clicks_per_view=clicks_per_view,
        access_token=access_token,
        total_issues=total_issues,
        issue_list=issue_list,
        top_cities = top_cities,
        no_cities=no_cities,
        check_clicked_github = check_clicked_github)