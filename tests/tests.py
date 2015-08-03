import os, unittest, sys, inspect, json
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 
from psycopg2 import connect, extras
import datetime

from gotissues import app, daily_update, data_helpers, view_helpers, github_bot
import testdata

class GotIssuesTestCase(unittest.TestCase):

    def setUp(self):
        # Runs before every tests
        # Build DB
        with connect(testdata.DATABASE_URL) as conn:
            with conn.cursor() as db:
                # Runs all the scripts to create tables
                for filename in os.listdir("scripts"):
                    with open("scripts/"+filename) as file:
                        db.execute(file.read())

        self.app = app.test_client()


    def tearDown(self):
        # Runs after every test
        pass


    def test_trim_github_issues(self):
        ''' Test that only the github attributes we want are left '''
        trimmed_issues = daily_update.trim_github_issues([testdata.full_issue])
        result = json.dumps(trimmed_issues[0], sort_keys=True, indent=4)
        control = json.dumps(testdata.trimmed_issue, sort_keys=True, indent=4)

        self.assertEqual(result,control)


    def test_writing_bad_GA_request(self):
        ''' Test for writing a bad key to GA'''
        error = {
        "Error":"Bad query request, not added to our dictionary"
        }

        for k in testdata.bad_sample_dict.iterkeys():
            testdata.bad_sample_dict[k] = data_helpers.get_analytics_query(k)
            self.assertEqual(testdata.bad_sample_dict[k], error)
    

    def test_write_timestamp(self):
        ''' Test for taking a sample GA response for issues + date info
            and writing the timestamp to '''
        timestamp_response = data_helpers.return_timestamp_dict(testdata.ga_timestamp_row)
        control = json.dumps(testdata.timestamp_entry, sort_keys=True, indent=4)
        results = json.dumps(timestamp_response, sort_keys=True, indent=4)

        self.assertEqual(control, results)


    '''def test_writing_good_GA_request(self):
        Test that fetching from GA is working

        for k in good_sample_dict.iterkeys():
            good_sample_dict[k] = get_analytics_query(k)
            self.assertEqual(good_sample_dict[k], error)'''


    #
    # daily_update tests
    #
    def test_write_issue_to_db(self):
        ''' Test that writing to the db works '''
        with connect(testdata.DATABASE_URL) as conn:
            with data_helpers.dict_cursor(conn) as db:
                daily_update.write_issue_to_db(testdata.db_issue, db)

                q = ''' SELECT * FROM issues '''
                db.execute(q)
                issue = db.fetchone()
                self.assertEqual(issue["id"],87136867)
                self.assertEqual(issue["clicks"],10000000)
                self.assertEqual(issue["views"],777)


    def test_write_click_to_db(self):
        ''' Test that writing to the db works '''
        with connect(testdata.DATABASE_URL) as conn:
            with data_helpers.dict_cursor(conn) as db:
                daily_update.write_click_to_db(testdata.fake_click, db)

                q = ''' SELECT * FROM clicks '''
                db.execute(q)
                issue = db.fetchone()
                self.assertEqual(issue["id"],1)
                self.assertEqual(issue["readable_date"],"Sunday, December 27 2015 07:30AM")
    

    def test_write_activity_to_db(self):
        with connect(testdata.DATABASE_URL) as conn:
            with data_helpers.dict_cursor(conn) as db:
                daily_update.write_activities_to_db(testdata.fake_activity, db)

                q = ''' SELECT * FROM activity '''
                db.execute(q)
                activity = db.fetchone()
                self.assertEqual(activity["issue_url"],"https://github.com/codeforamerica/gotissues/issues/8")

    # Test for valid timestamps
    # Capture datetime.datetime.now() and the month year day 
    # version of now() and assertEqual?


    def test_get_top_sources(self):
        ''' Test counting of view sources '''
        # Add a few issues with different sources
        # Test the output of get_top_sources
        with connect(testdata.DATABASE_URL) as conn:
            with data_helpers.dict_cursor(conn) as db:
                daily_update.write_issue_to_db(testdata.db_issue, db)
                daily_update.write_issue_to_db(testdata.test_issue, db)

                sources = view_helpers.get_top_sources(db)
                self.assertEqual(sources, testdata.test_sources_result)


    #
    # github_bot.py tests
    #
    def test_label_filter(self):
        ''' Test that array that's returned after filtering through methods is okay '''
        expected_final = []
        expected_final.append(testdata.fake_issue_good)

        issues_array = []
        issues_array.append(testdata.fake_issue_good)
        issues_array.append(testdata.fake_issue_bad)

        # test w/ a non 'help wanted' filter
        returned_array = github_bot.filter_issues(issues_array)
        self.assertEqual(len(returned_array), 1)
        self.assertEqual(expected_final, returned_array)

        # test w/ sample issue from a gov repo
        issues_array.append(testdata.fake_issue_bad_gov)
        returned_array = github_bot.filter_issues(issues_array)
        self.assertEqual(len(returned_array), 1)
        self.assertEqual(expected_final, returned_array)

    def test_post_body_to_github(self):
        issues_array = []
        issues_array.append(testdata.fake_issue_good)
        issues_array.append(testdata.fake_issue_bad)
        issues_array.append(testdata.fake_issue_bad_gov)

        for issue in issues_array:
            print str(github_bot.get_github_post(issue)) + "\n"


if __name__ == '__main__':
    unittest.main()
