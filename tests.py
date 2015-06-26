import os, unittest
from psycopg2 import connect, extras

from gotissues import *
from clock import *
from testdata import *
from data_helpers import *


class GotIssuesTestCase(unittest.TestCase):

    def setUp(self):
        # Runs before every tests
        # Build DB
        with connect(DATABASE_URL) as conn:
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
        trimmed_issues = trim_github_issues([full_issue])
        result = json.dumps(trimmed_issues[0], sort_keys=True, indent=4)
        control = json.dumps(trimmed_issue, sort_keys=True, indent=4)

        self.assertEqual(result,control)

    def test_writing_bad_GA_request(self):
        ''' Test that fetching from GA is working '''
        error = {
        "Error":"Bad query request, not added to our dictionary"
        }

        for k in bad_sample_dict.iterkeys():
            bad_sample_dict[k] = get_analytics_query(k)
            self.assertEqual(bad_sample_dict[k], error)

    '''def test_writing_good_GA_request(self):
        Test that fetching from GA is working

        for k in bad_sample_dict.iterkeys():
            bad_sample_dict[k] = get_analytics_query(k)
            self.assertEqual(bad_sample_dict[k], error)'''

    def test_write_issue_to_db(self):
        ''' Test that writing to the db works '''
        with connect(DATABASE_URL) as conn:
            with db_cursor(conn) as db:
                write_issue_to_db(db_issue, db)

                q = ''' SELECT * FROM issues '''
                db.execute(q)
                issue = db.fetchone()
                self.assertEqual(issue["id"],87136867)
                self.assertEqual(issue["clicks"],10000000)
                self.assertEqual(issue["views"],777)


if __name__ == '__main__':
    unittest.main()
