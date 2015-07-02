''' views.py: This file contains all of the routes '''
from data_helpers import *
from gotissues import app
from flask import render_template, request

@app.route("/", methods=["GET", "POST"])
def index():
    choice_dict = {
        "total_page_views":"",
        "total_clicks":""
    }

    for k in choice_dict.iterkeys():
        choice_dict[k] = get_analytics_query(k)

    choice_dict["clicks_per_view"] = int(100 * int(choice_dict["total_clicks"])/float(int(choice_dict["total_page_views"])))
    choice_dict["access_token"] = access_token

    return render_template("index.html", choice_dict=choice_dict)