''' views.py: This file contains all of the routes '''
from gotissues import app
from data_helpers import *
from flask import Flask, render_template, request

@app.route("/", methods=["GET", "POST"])
def index():
    choice_list = ["total_page_views", "most_clicked"]
    choice_dict_test = {
        "clicked_issues":"",
        "top_cities":"",
        "least_clicked":"",
        "most_clicked":"",
        "recently_clicked":"",
        "total_page_views":"",
        "total_clicks":""
    }
    final_response = []
    for choice in choice_list:
        final_response.append(get_analytics_query(choice))

    if request.method == "POST":
        check_clicked_github = get_github_data(request.form["issue"])
    else:
        check_clicked_github = []

    #get total number of closed issues differently

    return render_template("index.html", final_response=final_response)