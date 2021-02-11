from flask import Flask, render_template, jsonify
import requests
import threading
import time
from bs4 import BeautifulSoup
from datetime import datetime
from PIL import Image, ImageFilter
import io
from dataclasses import dataclass

URL = "https://www.instructables.com/contest/"
contests = []

app = Flask(__name__)
pyportal_clip_upper_left = (260, 7)
pyportal_clip_lower_right = (740, 367)
pyportal_size = (320, 240)


@dataclass
class Contest:
    name: str
    date: datetime
    contest_uri: str
    contest_graphic_uri: str
    entry_count: str


def convert_image_url_to_small(url):
    r = requests.get(url)
    if r.status_code == 200:
        image_file = io.BytesIO(r.content)
        im = Image.open(image_file)
        im_reduced = im.crop((*pyportal_clip_upper_left, *pyportal_clip_lower_right))\
            .resize(pyportal_size)
        im.close()
        return im_reduced
    return None


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
        if deadline < datetime.now():
            continue
        deadline_formatted = deadline.strftime('%B %d')
        contest_uri = 'https://www.instructables.com' + contest.find('a')['href']
        contest_graphic_uri = contest.find('img')['src']
        image = convert_image_url_to_small(contest_graphic_uri)
        image_fname = 'static/contestImg/' + contest_name.replace(" ", "") + '.png'
        image.save(image_fname, 'PNG')
        entry_count = contest.find_all('span', class_='contest-meta-count')[1].text
        contest_entry = Contest(contest_name, deadline, contest_uri, image_fname, entry_count)
        contests.append(contest_entry)
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
    app.run(host='0.0.0.0', port=5000)
