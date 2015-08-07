''' views.py: This file contains all of the routes '''
from data_helpers import *
from view_helpers import *
from gotissues import app
from flask import render_template, request, Markup
from datetime import timedelta

import markdown

@app.route("/", methods=["GET", "POST"])
def index():
    # View data that we don't need to access the db for
    data = {
    "total_page_views":"",
    "total_clicks":"",
    }

    for k in data.iterkeys():
        data[k] = get_analytics_query(k)

    data["clicks_per_view"] = ("%.0f" % round(100 * int(data["total_clicks"])/float(int(data["total_page_views"])), 2))
    data["access_token"] = access_token

    no_results = 9

    # View data that we need to access the db for
    with connect(os.environ['DATABASE_URL']) as conn:
        with dict_cursor(conn) as db:
            data["sources"] = get_top_sources(db)
            data["activities"] = get_activity_types(db)
            data["issue_count"] = get_total_count(db)
            data["closed_count"] = get_closed_count(db)
            data["open_count"] = get_open_count(db)
            data["closed_percent"] = int(100*float(data["closed_count"])/int(data["issue_count"]))
            data["top_clicks"] = get_most_clicked(db, 100)[:no_results]
            data["least_clicks"] = get_least_clicked(db, 12)[:no_results]
            data["closed_clicks"] = get_closed_clicked(db, 1000)
            data["activity_summary"] = get_activity_summary(db)
            #print data["activity_summary"]
            data["pinged_issues"] = get_pinged_issues(db)


            total_time = timedelta(seconds=0)
            for time in data["closed_clicks"]:
                delta = time["closed"] - time["created"]
                total_time += delta

            data["average_to_close"] = (total_time/len(data["closed_clicks"])).days


    return render_template("index.html", data=data)

@app.route("/analytics", methods=["GET", "POST"])
def analytics():
    db_results = {}

    data = {}

    if request.method == "POST":
        with connect(os.environ['DATABASE_URL']) as conn:
            with dict_cursor(conn) as db:
                data["sources"] = get_top_sources(db)
                data["activities"] = get_activity_types(db)
                data["issue_count"] = get_total_count(db)
                data["closed_count"] = get_closed_count(db)
                data["open_count"] = get_open_count(db)
                data["closed_percent"] = int(100*float(data["closed_count"])/int(data["issue_count"]))
                data["top_clicks"] = get_most_clicked(db, 100)[:no_results]
                data["least_clicks"] = get_least_clicked(db, 12)[:no_results]
                data["closed_clicks"] = get_closed_clicked(db, 1000)
                data["activity_summary"] = get_activity_summary(db)
                #print data["activity_summary"]
                data["pinged_issues"] = get_pinged_issues(db)


                total_time = timedelta(seconds=0)
                for time in data["closed_clicks"]:
                    delta = time["closed"] - time["created"]
                    total_time += delta

                data["average_to_close"] = (total_time/len(data["closed_clicks"])).days

                for date in data["pinged_issues"]:
                    date["date_pinged"] = date["date_pinged"].strftime('%B %d %Y')
                    #date["state"] = get_issue_status(date["html_url"])
                
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
                data["pinged_issues"] = get_pinged_issues(db)
                data["total_pinged"] = get_total_pinged(db)

                for ping in data["pinged_issues"]:
                    check_issues(db, ping)

                data["closed_pinged"] = count_closed(db, data["pinged_issues"])
                data["percentage_pinged"] = 100 * int(float(data["closed_pinged"])/data["total_pinged"])
                db_results = get_all_activity(db)
        
        for result in db_results:
            result['time_after'] = int((result['activity_timestamp'] - result['click_timestamp']).total_seconds()/60)
            result['activity_timestamp'] = str(result['activity_timestamp'])
            result['click_timestamp'] = str(result['click_timestamp'])

        for date in data["pinged_issues"]:
            date["date_pinged"] = date["date_pinged"].strftime('%B %d %Y')
            #date["state"] = get_issue_status(date["html_url"])


    return render_template("analytics.html", db_results=db_results, data=data)

@app.route("/cheatsheet", methods=["GET", "POST"])
def cheatsheet():
    data = {}
    if request.method == "POST":
        data['title'] = request.form.get("title", None)
        data['description'] = request.form.get("description", "This is a Markdown rendering of what you're submitting")
        data["content"] = Markup(markdown.markdown(data['description']))
        print data
    
    else:
        data['title'] = request.form.get("title", None)
        data['description'] = request.form.get("description", "This is a Markdown rendering of what you're submitting")
        data["content"] = Markup(markdown.markdown(data['description']))
        print data
    

    return render_template("cheatsheet.html", **locals())