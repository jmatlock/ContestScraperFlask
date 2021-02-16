from adafruit_pyportal import PyPortal
from secrets import secrets
import time

# Set up where we'll be fetching data from
CONTEST_DATA_SOURCE = 'http://' + secrets['local_server'] + '/api/v1/contests'
CONTEST_DATA_LOCATION = []


def text_transform(val):
    print(val)
    return f'{val}'

class Contests:

    class Contest:
        def __init__(self):
            self.name = ''
            self.deadline = ''
            self.days_until = -1

        def get_contest_string(self):
            if self.days_until > 0:
                if self.days_until > 1:
                    return f'{self.name}\nends in {self.days_until} days.'
                else:
                    return f'{self.name}\nends in {self.days_until} day.'
            else:
                return f'{self.name}\nends today!'

    def __init__(self):
        self.index = 0
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
                self.contests.append(contest)
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

pyportal = PyPortal()
display = pyportal.display
network = pyportal.network

network.connect()

contests = Contests()
contests.load_contests()


# pyportal.add_text(
#     text_position=(
#         (pyportal.graphics.display.width // 2) - 1,
#         (pyportal.graphics.display.height // 2) - 1,
#     ),
#     text_scale=2,
#     text_anchor_point=(0.5, 0.5),
# )

pyportal.add_text(
    text_position=(
        20,
        20,
    ),
    text_scale=4,
    text_anchor_point=(0.5, 0.5),
)

while True:
    pyportal.set_text(contests.get_next_contest_string())
    time.sleep(10)

