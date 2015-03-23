# gotissues
Does the [civic issue finder](http://www.codeforamerica.org/geeks/civicissues) actually work? Lets explore the data to find out.

### How
1. Pull down all the acitivty from Google Analytics
2. Go explore those GitHub Issues
3. Perhaps visualize number of clicks, number of closed issues, number of commented on issues, relationships between people.

### Status
This project is just starting out. We're still figuring out the best way to get analytics on the issues being clicked on.

### Installation
#### Requirements
* `pip` and `virtualenv` - https://github.com/codeforamerica/howto/blob/master/Python-Virtualenv.md

```
git clone https://github.com/codeforamerica/gotissues
cd gotissues
virtualenv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### To Run
```
env `cat .env` python app.py
```
