from flask import Flask, request, abort
import os
import requests
from datetime import datetime
from dateutil.relativedelta import relativedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

API_KEY = os.environ.get('API_KEY')
WEBHOOK_URL = os.environ.get('API_KEY')
port = int(os.environ.get("PORT", 5000))

def sign_to_comments():
    webhook_url = 'https://api.tjournal.ru/v1.8/webhooks/add'
    data = {
        "url": WEBHOOK_URL,
        "event": "new_comment",
    }
    requests.post(webhook_url, data=data,
                  headers={'X-Device-Token': API_KEY})

jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///jobs')
}

sched = BackgroundScheduler(jobstores=jobstores)
sched.start()
app = Flask(__name__)

api_url = 'https://api.tjournal.ru/v1.9/comment/add'

def send_reminder(post_data):
    requests.post(api_url, data=post_data, headers={'X-Device-Token': API_KEY})


def error_logs(comment_url):
    with open('errors.txt', 'a') as f:
        f.write(f'{comment_url}\n')


dates_dict = {
    'day': 'days',
    'days': 'days',
    'month': 'months',
    'months': 'months',
    'year': 'years',
    'years': 'years',
    'hour': 'hours',
    'hours': 'hours'
}

@app.route('/', methods=['GET'])
def welcome_message():
    return '<h1>You are not welcome here</h1>'

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        data = request.json
        if data['data']['text'].startswith('@remindme '):
            comment = data['data']['text'].split()
            date_time = datetime.now()
            comment_id = int(data['data']['id'])
            url = data['data']['url']
            content_id = int(data['data']['content']['id'])
            post_data = {
                    "id": content_id,
                    "text": "Время пришло",
                    "reply_to": comment_id
                }
            try:
                if len(comment) == 2 and datetime.strptime(comment[1], '%d/%m/%Y') > date_time:
                    time_delta = datetime.strptime(comment[1], '%d/%m/%Y')
                    sched.add_job(send_reminder, 'date', run_date=time_delta, args=[post_data])

                if len(comment) == 3 and comment[1].isdigit() and comment[2] in dates_dict:
                    time_delta = date_time + relativedelta(**{dates_dict[comment[2]]: +int(comment[1])})
                    sched.add_job(send_reminder, 'date', run_date=time_delta, args=[post_data])
            except TypeError:
                error_logs(url)

        return 'success', 200
    else:
        abort(400)




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=True)
    sign_to_comments()
