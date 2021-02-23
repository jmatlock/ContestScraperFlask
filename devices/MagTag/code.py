"""
Instructables Contest Info Display for MagTag
by James Matlock
Feb 2021

This project is

In order to run this project you will need the
following hardware:
- Adafruit MagTag (https://www.adafruit.com/product/4800)
- 5V USB C Power Supply (https://www.adafruit.com/product/4298)

This project assumes CircuitPython is already installed on the MagTag.
More information about installing CircuitPython can be found here:

This project will also require CircuitPython libraries to be included in a
lib folder when the project is installed on the CIRCUITPY drive of
the MagTag:

Note that all these libraries may not be used in this particular project, but I'm
including them for potential future use.

See this page for more info about installing CircuitPython libraries:
    https://learn.adafruit.com/welcome-to-circuitpython/circuitpython-libraries

Currently the display has the following features:
- Shows the currently running Instructables contests
- Shows the number of days till the contest ends

The Instructables contest information feature requires a separate local web
server be installed that scrapes the Instructables web site and provides
a local API.

Tutorials and references used as input to this project include:

"""

from adafruit_magtag.magtag import MagTag
from secrets import secrets
import alarm

# Set up where we'll be fetching data from
CONTEST_DATA_SOURCE = 'http://' + secrets['local_server'] + '/api/v1/contests'
CONTEST_DATA_LOCATION = []


class Contests:
    class Contest:
        def __init__(self):
            self.name = ''
            self.deadline = ''
            self.days_until = -1

        def get_contest_string(self):
            return f'{self.name}'

        def get_contest_deadline_string(self):
            if self.days_until > 0:
                if self.days_until > 1:
                    return f'ends in {self.days_until} days.'
                else:
                    return f'ends in {self.days_until} day.'
            else:
                return f'ends today!'

    def __init__(self):
        if not alarm.sleep_memory:
            alarm.sleep_memory[0] = 0
        self.index = alarm.sleep_memory[0]
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
            if retry >= 3:
                print("Couldn't access web server")
        except RuntimeError as e:
            print("Some error occurred, retrying! -", e)

    def get_next_contest(self):
        if self.index + 1 <= len(self.contests):
            return self.contests[self.index].get_contest_string()
        else:
            return "Contest Data"

    def get_next_contest_deadline(self):
        if self.index + 1 <= len(self.contests):
            return self.contests[self.index].get_contest_deadline_string()
        else:
            return "Offline"

    def next_contest(self):
        self.index += 1
        if self.index >= len(self.contests):
            self.index = 0
        alarm.sleep_memory[0] = self.index  # Storing in non-volatile memory so we can cycle
                                            # through the different contests


magtag = MagTag()
display = magtag.display
network = magtag.network

network.connect()

contests = Contests()
contests.load_contests()

contest_str = contests.get_next_contest()
deadline_str = contests.get_next_contest_deadline()

text_font = '/fonts/Arial-18.bdf'
line_spacing = 14
if len(contest_str) > 23 or len(deadline_str) > 23:
    text_font = '/fonts/Arial-12.bdf'
    line_spacing = 12

# Text at index 0, contest name
magtag.add_text(
    text_position=(
        (magtag.graphics.display.width // 2) - 1,
        (magtag.graphics.display.height // 2) - 1 - line_spacing,
    ),
    text_font=text_font,
    text_anchor_point=(0.5, 0.5),
)

# Text at index 1, days till deadline
magtag.add_text(
    text_position=(
        (magtag.graphics.display.width // 2) - 1,
        (magtag.graphics.display.height // 2) - 1 + line_spacing,
    ),
    text_font=text_font,
    text_anchor_point=(0.5, 0.5),
)

contests.next_contest()
magtag.set_text(contest_str, auto_refresh=False)
magtag.set_text(deadline_str, 1)

magtag.exit_and_deep_sleep(10)
