from apscheduler.schedulers.blocking import BlockingScheduler
import run

sched = BlockingScheduler()

@sched.scheduled_job('interval', days=1)
def timed_job():
  run.write_github_response()
  # In process of writing the dictionary response for number of comments in issue(after parsing)
sched.start()
