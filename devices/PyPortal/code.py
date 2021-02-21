import time
from adafruit_pyportal import PyPortal
from secrets import secrets
import os
import gc

# Set up where we'll be fetching data from
CONTEST_DATA_SOURCE = 'http://' + secrets['local_server'] + '/api/v1/contests'


class Contests:
    class Contest:
        def __init__(self):
            self.name = ''
            self.deadline = ''
            self.days_until = -1
            self.graphic = None

        def get_contest_string(self):
            if self.days_until > 0:
                if self.days_until > 1:
                    return f'Ends in {self.days_until} days'
                else:
                    return f'Ends in {self.days_until} day'
            else:
                return f'Ends today!'

        def get_contest_graphic_uri(self):
            return f'http://{secrets["local_server"]}/{self.graphic}'

    def __init__(self):
        self.index = -1
        self.contests = []

    def load_contests(self):
        try:
            all_data = ''
            retry = 0
            while all_data == '' and retry < 3:
                retry += 1
                response = network.fetch(CONTEST_DATA_SOURCE)
                all_data = response.json()
                print(f"Retry #{retry}:\nResponse is {all_data}")
            for entry in all_data:
                contest = self.Contest()
                contest.name = entry['name']
                contest.deadline = entry['date']
                contest.days_until = entry['days_until']
                contest.graphic = entry['contest_graphic_uri']
                self.contests.append(contest)
            all_data = None
            gc.collect()
        except RuntimeError as e:
            print("Some error occurred, retrying! -", e)
            return None

    def get_next_contest_string(self):
        self.index += 1
        if self.index >= len(self.contests):
            self.index = 0
        if self.index + 1 <= len(self.contests):
            return self.contests[self.index].get_contest_string()
        else:
            return None

    def get_contest_graphic_uri(self):
        return self.contests[self.index].get_contest_graphic_uri()


pyportal = PyPortal(debug=False)

display = pyportal.display
network = pyportal.network
graphics = pyportal.graphics

text_index = pyportal.add_text(text_position=(160, 220), text_anchor_point=(0.5, 0.5),
                               text_color=0xffffff, text_font="/fonts/Helvetica-Bold-16.bdf",
                               text_scale=2, is_data=False)

network.connect()

contests = Contests()
contests.load_contests()

counter = 0

while True:
    counter += 1
    text = contests.get_next_contest_string()
    graphic_url = contests.get_contest_graphic_uri()

    print(f'START: Loop #{counter}; Contest {contests.index}')
    try:
        os.remove('/sd/contest.bmp')
    except Exception as e:
        pass

    retry = 0
    while retry < 3:
        try:
            network.wget(contests.get_contest_graphic_uri(),
                         '/sd/contest.bmp',
                         chunk_size=512)
            break
        except Exception as e:
            print(f'Exception {e}, retrying ({retry}')
            retry += 1


    pyportal.set_text('', index=text_index)
    graphics.set_background('/sd/contest.bmp')
    time.sleep(1)
    pyportal.set_text(text, index=text_index)

    text = None
    graphic_url = None
    gc.collect()

    print(f'END: Loop #{counter}; Contest {contests.index}')

    time.sleep(15)
