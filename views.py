''' views.py: This file contains all of the routes '''
from data_helpers import *
from gotissues import app
from flask import render_template, request

@app.route("/", methods=["GET", "POST"])
def index():
    choice_dict = {
        "clicked_issues":"",
        "top_cities":"",
        "least_clicked":"",
        "most_clicked":"",
        "recently_clicked":"",
        "total_page_views":"",
        "total_clicks":"",
        "viewed_issues":""
    }

    for k in choice_dict.iterkeys():
        choice_dict[k] = get_analytics_query(k)

    choice_dict["no_cities"] = len(choice_dict["top_cities"])
    choice_dict["clicks_per_view"] = int(100 * int(choice_dict["total_clicks"])/float(int(choice_dict["total_page_views"])))
    choice_dict["access_token"]=login_to_google_analytics()[1]
    choice_dict["total_recently_clicked"] = len(choice_dict["recently_clicked"])
    
    # view helpers
    if request.method == "POST":
        choice_dict["check_clicked_github"] = get_github_data(request.form["issue"])
    else:
        choice_dict["check_clicked_github"] = []

    # to do: get total number of closed issues differently

    return render_template("index.html", choice_dict=choice_dict)