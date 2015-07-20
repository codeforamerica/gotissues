''' views.py: This file contains all of the routes '''
from data_helpers import *
from view_helpers import *
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

    with connect(os.environ['DATABASE_URL']) as conn:
        with dict_cursor(conn) as db:
            data["sources"] = get_top_sources(db)
            data["activities"] = get_top_activity(db)
            data["activity_summary"] = get_activity_summary(db)
            print data["activity_summary"]
            data["issue_summary"] = get_compare_activity_summary(db)
            data["issue_count"] = get_total_count(db)
            data["closed_count"] = get_closed_count(db)
            data["open_count"] = get_open_count(db)
            data["closed_percent"] = int(100*float(data["closed_count"])/int(data["issue_count"]))

    return render_template("index.html", data=data)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    db_results = {}

    if request.method == "POST":
        with connect(os.environ['DATABASE_URL']) as conn:
            with dict_cursor(conn) as db:
                category = request.form['category']
                order = request.form['radio']
                db_results = get_edited_activity(db, order, category)
                for result in db_results:
                    result['time_after'] = int((result['activity_timestamp'] - result['click_timestamp']).total_seconds()/60)
                    result['activity_timestamp'] = str(result['activity_timestamp'])
                    result['click_timestamp'] = str(result['click_timestamp'])

    else:
        with connect(os.environ['DATABASE_URL']) as conn:
            with dict_cursor(conn) as db:
                db_results = get_all_activity(db)
        for result in db_results:
            result['time_after'] = int((result['activity_timestamp'] - result['click_timestamp']).total_seconds()/60)
            result['activity_timestamp'] = str(result['activity_timestamp'])
            result['click_timestamp'] = str(result['click_timestamp'])


    return render_template("admin.html", db_results=db_results)