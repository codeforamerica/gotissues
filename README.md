# gotissues
Does the [civic issue finder](http://www.codeforamerica.org/geeks/civicissues) actually work? Lets explore the data to find out.

## About 
The civic issues finder is a widget that fetches open issues in projects included in the [Cfapi](http://www.codeforamerica.org/api/). More information about how the civic issue finder works is available in the project [Readme](https://github.com/codeforamerica/civic-issue-finder#civic-issue-finder). We want to ask questions around how these open issues become solved. We are looking at metrics like timestamps of activity and how frequently some issues get viewed or clicked. Hopefully this leads to a better understanding of how to have larger amounts of contribution on open source projects.

### How
1. Pull down all the acitivty from Google Analytics
2. Go explore those GitHub Issues
3. Perhaps visualize number of clicks, number of closed issues, number of commented on issues, relationships between people.

### Status
This project is currently in its exploration phase. You can see gotissues's progress and milestone activity [here](https://github.com/codeforamerica/gotissues/milestones?direction=asc&sort=due_date&state=open).

### Installation
#### Requirements
* `pip` and `virtualenv` - https://github.com/codeforamerica/howto/blob/master/Python-Virtualenv.md
* Google Analytics credentials for your `.env` file. Ping @ondrae to get the credentials, then fill in your `env.sample` file. Then `mv env.sample .env`

```
git clone https://github.com/codeforamerica/gotissues
cd gotissues
virtualenv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### To Run
Either use
```
source .env
python run.py
```
or to mimic Heroku use
```
foreman start
```

### To Test
In the top level, run

`python tests/tests.py`