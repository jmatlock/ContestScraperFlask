from flask import Flask, render_template, jsonify
import requests
import threading
import time
from bs4 import BeautifulSoup
from datetime import datetime

URL = "https://www.instructables.com/contest/"
contests = []

app = Flask(__name__)

def update_contests():
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, 'html.parser')
    results = soup.find(id='cur-contests')
    contest_banners = results.find_all('div', class_='contest-banner')

    contests = []
    for contest in contest_banners:
        contest_name = contest.find('img')['alt']
        contest_deadline = contest.find('span', class_='contest-meta-deadline')['data-deadline']
        deadline = datetime.fromisoformat(contest_deadline)
        # TODO: filter out expired contests
        contests.append({"name": contest_name, "date": deadline.strftime('%B %d')})
        # print(contest_name + ": " + deadline.strftime('%B %d'))
    return contests

@app.before_first_request
def setup_server():
    def contest_update():
        global contests
        print('Updating contest data')
        contests = update_contests()
        print('Contest data loaded')

    def contest_update_job():
        print('Waiting a day for next contest update')
        time.sleep(24 * 60 * 60)  # sleep for a day
        contest_update()

    contest_update()
    thread = threading.Thread(target=contest_update_job)
    thread.start()


@app.route('/')
def index():
    return render_template('index.html', contests=contests)

@app.route('/api/v1/contests', methods=['GET'])
def get_contests():
    return jsonify(contests)

if __name__ == '__main__':
    app.run()
