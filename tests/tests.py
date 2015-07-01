import os, unittest, sys, inspect, json
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 
from psycopg2 import connect, extras

from gotissues import app, daily_update
import testdata
from data_helpers import *


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


    # def test_main_view(self):
    #     ''' Test the main gotissues view '''
    #     response = self.app.get("/")
    #     self.assertEqual(response.status_code, 200)


    # def test_test_view(self):
    #     ''' Test the test gotissues view '''
    #     response = self.app.get("/test")
    #     self.assertEqual(response.status_code, 200)


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
            testdata.bad_sample_dict[k] = get_analytics_query(k)
            self.assertEqual(testdata.bad_sample_dict[k], error)
    
    def test_write_timestamp(self):
        ''' Test for taking a sample GA response for issues + date info
            and writing the timestamp to '''
        timestamp_response = return_timestamp_dict(testdata.ga_timestamp_row)
        control = json.dumps(testdata.timestamp_entry, sort_keys=True, indent=4)
        results = json.dumps(timestamp_response, sort_keys=True, indent=4)

        self.assertEqual(control, results)

    '''def test_writing_good_GA_request(self):
        Test that fetching from GA is working

        for k in good_sample_dict.iterkeys():
            good_sample_dict[k] = get_analytics_query(k)
            self.assertEqual(good_sample_dict[k], error)'''

    def test_write_issue_to_db(self):
        ''' Test that writing to the db works '''
        with connect(testdata.DATABASE_URL) as conn:
            with db_cursor(conn) as db:
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
            with db_cursor(conn) as db:
                daily_update.write_click_to_db(testdata.fake_click, db)

                q = ''' SELECT * FROM clicks '''
                db.execute(q)
                issue = db.fetchone()
                self.assertEqual(issue["id"],1)
                self.assertEqual(issue["readable_date"],"Sunday, December 27 2015 07:30AM")

    # Test for valid timestamps
    # Capture datetime.datetime.now() and the month year day 
    # version of now() and assertEqual?


if __name__ == '__main__':
    unittest.main()
