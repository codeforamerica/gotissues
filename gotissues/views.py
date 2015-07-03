''' views.py: This file contains all of the routes '''
from data_helpers import *
from gotissues import app
from flask import render_template, request

@app.route("/", methods=["GET", "POST"])
def index():
    data = {
        "total_page_views":"",
        "total_clicks":"",
    }

    for k in data.iterkeys():
        data[k] = get_analytics_query(k)

    data["clicks_per_view"] = int(100 * int(data["total_clicks"])/float(int(data["total_page_views"])))
    data["access_token"] = access_token

    # Get list of top view sources
    with connect(DATABASE_URL) as conn:
        with dict_cursor(conn) as db:
            data["top_sources"] = get_top_sources(db)


    return render_template("index.html", data=data)