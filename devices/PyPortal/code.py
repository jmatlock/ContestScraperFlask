"""
Instructables Contest Info Display for PyPortal
by James Matlock
Feb 2021

This project is

In order to run this project you will need the
following hardware:
- Adafruit PyPortal (https://www.adafruit.com/product/4116)
- 5V USB Micro Power Supply (https://www.adafruit.com/product/1995)
- MicroSD Card, 4GB or greater


This project assumes CircuitPython is already installed on the PyPortal.
More information about installing CircuitPython can be found here:

This project will also require CircuitPython libraries to be included in a
lib folder when the project is installed on the CIRCUITPY drive of
the PyPortal:

Note that all these libraries may not be used in this particular project, but I'm
including them for potential future use.

See this page for more info about installing CircuitPython libraries:
    https://learn.adafruit.com/welcome-to-circuitpython/circuitpython-libraries

Currently the display has the following features:
- Shows the currently running Instructables contests
- Shows the number of days till the contest ends
- Shows the Instructable web site graphic appropriately sized for the display

The Instructables contest information feature requires a separate local web
server be installed that scrapes the Instructables web site and provides
a local API.

Tutorials and references used as input to this project include:

"""
import time
from adafruit_pyportal import PyPortal
from secrets import secrets
import os
import gc

DEBUG = False

# Set up where we'll be fetching data from
CONTEST_DATA_SOURCE = 'http://' + secrets['local_server'] + '/api/v1/contests'
CONTEST_SERVER_META = ("http://" + secrets["local_server"] + "/api/v1/meta")


class Contests:
    class Contest:
        def __init__(self,
                     name='',
                     deadline='',
                     days_until=-1,
                     graphic=None):
            self.name = name
            self.deadline = deadline
            self.days_until = days_until
            self.graphic = graphic
            self.graphic_file = None

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

        def get_contest_graphic(self):
            if self.graphic_file:
                return self.graphic_file
            file_parts = self.graphic.split('/')
            filename = file_parts[-1]
            try:
                t = os.stat(f'/sd/{filename}')  # testing for existence
            except OSError as e:  # file doesn't exist, get from URI
                retry = 0
                while retry < 3:
                    try:
                        network.wget(f'http://{secrets["local_server"]}/{self.graphic}',
                                     f'/sd/{filename}',
                                     chunk_size=512)
                        self.graphic_file = f'/sd/{filename}'
                        break
                    except Exception as e:
                        print(f'Exception {e}, retrying ({retry}')
                        retry += 1
                if retry >= 3:
                    return None
            return f'/sd/{filename}'

    def __init__(self):
        self.index = -1
        self.contests = []
        self.update_minutes = None
        self.contest_refresh = None

    def load_contests(self):
        try:
            all_data = ''
            meta = ''
            retry = 0
            while all_data == '' and retry < 3:
                retry += 1
                response = network.fetch(CONTEST_DATA_SOURCE)
                all_data = response.json()
                response = network.fetch(CONTEST_SERVER_META)
                meta = response.json()
                if DEBUG:
                    print(f"Retry #{retry}:\nResponse is {all_data}")
                    print(f'Meta is {meta}')
            for entry in all_data:
                contest = self.Contest(name=entry['name'],
                                       deadline=entry['date'],
                                       days_until=int(entry['days_until']),
                                       graphic=entry['contest_graphic_uri']
                                       )
                self.contests.append(contest)
            self.update_minutes = meta['next_update_minutes'] + 1  # update 1 minutes after web server
            self.contest_refresh = time.monotonic()
            all_data = None
            gc.collect()
        except RuntimeError as e:
            print("Some error occurred, retrying! -", e)
            return None

    def get_next_contest_string_and_graphic(self):
        self.index += 1
        if self.index >= len(self.contests):
            self.index = 0
        if self.index + 1 <= len(self.contests):
            return self.contests[self.index].get_contest_string(), self.contests[self.index].get_contest_graphic()
        else:
            return None, None

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
    if contests:
        if not contests.contest_refresh or \
                (time.monotonic() - contests.contest_refresh) > (contests.update_minutes * 60):
            # TODO: Wipe cached graphics
            contests.load_contests()
    counter += 1
    text, graphic = contests.get_next_contest_string_and_graphic()
    # graphic_url = contests.get_contest_graphic_uri()

    print(f'START: Loop #{counter}; Contest {contests.index}')
    # try:
    #     os.remove('/sd/contest.bmp')
    # except Exception as e:
    #     pass
    #
    # retry = 0
    # while retry < 3:
    #     try:
    #         network.wget(contests.get_contest_graphic_uri(),
    #                      '/sd/contest.bmp',
    #                      chunk_size=512)
    #         break
    #     except Exception as e:
    #         print(f'Exception {e}, retrying ({retry}')
    #         retry += 1

    pyportal.set_text('', index=text_index)
    # graphics.set_background('/sd/contest.bmp')
    graphics.set_background(graphic)

    time.sleep(1)
    pyportal.set_text(text, index=text_index)

    text = None
    graphic_url = None
    gc.collect()

    print(f'END: Loop #{counter}; Contest {contests.index}')

    time.sleep(15)
