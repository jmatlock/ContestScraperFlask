"""
Matrix Clock Plus
by James Matlock
Feb 2021

This project is a mashup and extension of example projects for the
Adafruit Matrix Portal. In order to run this project you will need the
following hardware:

- Adafruit Matrix Portal (https://www.adafruit.com/product/4745)
- 64 x 32 RGB LED Matrix (https://www.adafruit.com/product/2277)
- 5V USB C Power Supply (https://www.adafruit.com/product/4298)

This project assumes CircuitPython is already installed on the Matrix Portal.
More information about installing CircuitPython can be found here:
    https://learn.adafruit.com/adafruit-matrixportal-m4/install-circuitpython

This project will also require CircuitPython libraries to be included in a
lib folder when the project is installed on the CIRCUITPY drive of
the Matrix Portal:
    adafruit_bitmap_font
    adafruit_bus_device
    adafruit_display_text
    adafruit_esp32spi
    adafruit_io
    adafruit_lis3dh.mpy
    adafruit_matrixportal
    adafruit_requests.mpy
    neopixel.mpy

Note that all these libraries may not be used in this particular project, but I'm
including them for potential future use.

See this page for more info about installing CircuitPython libraries:
    https://learn.adafruit.com/welcome-to-circuitpython/circuitpython-libraries

Currently the clock has the following features:
- Tells time
- Shows date and day of the week
- Shows the temperature from openweathermap.org
- Show Instructables contest information
- Change display colors via the Up/Down buttons on the Matrix Portal card

The Instructables contest information feature requires a separate local web
server be installed that scrapes the Instructables web site and provides
a local API.

Tutorials and references used as input to this project include:
- https://learn.adafruit.com/network-connected-metro-rgb-matrix-clock
- https://learn.adafruit.com/weather-display-matrix
- https://learn.adafruit.com/creating-projects-with-the-circuitpython-matrixportal-library
"""

import time
import board
from digitalio import DigitalInOut, Direction, Pull
import displayio
import terminalio
from adafruit_display_text.label import Label
from adafruit_bitmap_font import bitmap_font
from adafruit_matrixportal.network import Network
from adafruit_matrixportal.matrix import Matrix

DEBUG = False

months = ['na', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
wkdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
color_codes = {'Red': 0x660000,
               'Orange': 0x882200,
               'Yellow': 0x666600,
               'Green': 0x006600,
               'Blue': 0x000066,
               'Violet': 0x663666,
               'White': 0x444444,
               }

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise
print("Matrix Clock Plus")

# --- Display setup ---
matrix = Matrix()
display = matrix.display
network = Network(status_neopixel=board.NEOPIXEL, debug=True)
button_down = DigitalInOut(board.BUTTON_DOWN)
button_down.switch_to_input(pull=Pull.UP)
button_up = DigitalInOut(board.BUTTON_UP)
button_up.switch_to_input(pull=Pull.UP)

# --- Weather data setup ---
UNITS = "imperial"
DATA_LOCATION = []
DATA_SOURCE = (
        "http://api.openweathermap.org/data/2.5/weather?q=" + secrets["openweather_loc"] + "&units=" + UNITS
)
DATA_SOURCE += "&appid=" + secrets["openweather_token"]

# --- Instructables contest data setup ---
CONTEST_DATA_LOCATION = []
CONTEST_DATA_SOURCE = ("http://" + secrets["local_server"] + "/api/v1/contests")
CONTEST_SERVER_META = ("http://" + secrets["local_server"] + "/api/v1/meta")

# --- Drawing setup ---
group = displayio.Group(max_size=4)  # Create a Group
bitmap = displayio.Bitmap(64, 32, len(color_codes) + 1)  # Create a bitmap object,width, height, bit depth
color = displayio.Palette(len(color_codes) + 1)  # Create a color palette
color[0] = 0x000000  # black background
for idx, val in enumerate(color_codes.values()):
    color[idx + 1] = val

# Create a TileGrid using the Bitmap and Palette
tile_grid = displayio.TileGrid(bitmap, pixel_shader=color)
group.append(tile_grid)  # Add the TileGrid to the Group
display.show(group)

if not DEBUG:
    font = bitmap_font.load_font("fonts/Arial-12.bdf")
    font2 = bitmap_font.load_font("fonts/helvR10.bdf")
    small_font = bitmap_font.load_font("fonts/helvR10.bdf")
else:
    font = terminalio.FONT
    font2 = terminalio.FONT
    small_font = terminalio.FONT

clock_label = Label(font, max_glyphs=8)
clock_label.color_idx = 1
clock_label.color = color[clock_label.color_idx]
clock_label.text = 'Matrix'
clock_label.x = 0
clock_label.y = display.height // 4
clock_label.normal = True
event_label = Label(font2, max_glyphs=64)
event_label.color_idx = 2
event_label.color = color[event_label.color_idx]
event_label.text = 'Clock'
event_label.x = 0
event_label.y = display.height // 4 * 3

DATA_LOCATION = []


class Weather:
    weather_refresh = None
    weather_data = None


class Contests:

    class Contest:
        def __init__(self, name='', deadline='', days_until=-1):
            self.name = name
            self.deadline = deadline
            self.days_until = days_until

        def get_contest_string(self):
            if self.days_until > 1:
                return f'{self.name} ends in {self.days_until} days.'
            elif self.days_until == 1:
                return f'{self.name} ends in {self.days_until} day.'
            elif self.days_until == 0:
                return f'{self.name} ends today!'
            else:  # This case happens if there is a connection error
                return f'{self.name}'

    def __init__(self):
        self.index = 0
        self.contests = []
        self.update_minutes = None
        self.contest_refresh = None

    def load_contests(self):
        try:
            clock_label.text = 'Contest'
            clock_label.x = 0
            event_label.text = 'Update'
            event_label.x = 0
            all_data = ''
            meta = ''
            retry = 0
            self.contests.clear()
            while all_data == '' and retry < 3:
                retry += 1
                all_data = network.fetch_data(CONTEST_DATA_SOURCE, json_path=(CONTEST_DATA_LOCATION,))
                meta = network.fetch_data(CONTEST_SERVER_META, json_path=(CONTEST_DATA_LOCATION,))
                if DEBUG:
                    print(f"Retry #{retry}:\nResponse is {all_data}")
                    print(f'Meta is {meta}')
            for entry in all_data:
                contest = self.Contest(name=entry['name'],
                                       deadline=entry['date'],
                                       days_until=entry['days_until'])
                self.contests.append(contest)
            if retry >= 3:
                contest = self.Contest(name='Web Server unreachable.',
                                       days_until=-1)
                self.contests.append(contest)
                self.update_minutes = 5  # Try again in 5 minutes
            else:
                self.update_minutes = meta['next_update_minutes'] + 1  # update 1 minutes after web server
        except RuntimeError as e:
            print("Some error occurred, retrying! -", e)
            contest = self.Contest(name='Web Server unreachable.',
                                   days_until=-1)
            self.contests.append(contest)
            self.update_minutes = 5  # Try again in 5 minutes
        self.contest_refresh = time.monotonic()
        clock_label.text = ''
        event_label.text = ''
        print(f'Contest data collected. Refresh in {self.update_minutes} minutes.')

    def get_next_contest_string(self):
        self.index += 1
        if self.index >= len(self.contests):
            self.index = 0
        if self.index + 1 <= len(self.contests):
            return self.contests[self.index].get_contest_string()
        else:
            return None


def get_weather_info():
    try:
        clock_label.text = 'Weather'
        clock_label.x = 0
        event_label.text = 'Update'
        event_label.x = 0
        value = network.fetch_data(DATA_SOURCE, json_path=(DATA_LOCATION,))
        print("Response is", value)
        clock_label.text = ''
        event_label.text = ''
        return value
    except RuntimeError as e:
        print("Some error occurred, retrying! -", e)
        return None


def update_time(*, hours=None, minutes=None, weather=None, contests=None):
    now = time.localtime()  # Get the time values we need
    # Update weather data every 10 minutes
    if weather:
        if (not weather.weather_refresh) or (time.monotonic() - weather.weather_refresh) > 600:
            weather.weather_data = get_weather_info()
            if weather.weather_data:
                weather.weather_refresh = time.monotonic()

    if contests:
        if not contests.contest_refresh or (time.monotonic() - contests.contest_refresh) > (contests.update_minutes * 60):
            contests.load_contests()

    if hours is None:
        hours = now[3]
    if hours > 12:  # Handle times later than 12:59
        hours -= 12
    elif not hours:  # Handle times between 0:00 and 0:59
        hours = 12

    if minutes is None:
        minutes = now[4]

    if now[5] % 30 < 12:
        clock_label.text = f"{hours}:{minutes:02d}"
        if not clock_label.normal:
            clock_label.normal = True
            clock_label.font = font
    elif now[5] % 30 < 15:
        clock_label.text = f"{wkdays[now[6]]}"
    elif now[5] % 30 < 20:
        clock_label.text = f"{months[now[1]]} {now[2]}"
    elif now[5] % 30 < 25:
        try:
            temperature = int(weather.weather_data["main"]["temp"])
        except Exception as e:
            temperature = "??"
        clock_label.text = f"{temperature}°F"
    else:
        try:
            weather_description = weather.weather_data["weather"][0]["main"]
            if weather_description == 'Thunderstorm':
                weather_description = 'T-Storm'
        except Exception as e:
            weather_description = "??"
        if len(weather_description) > 6:
            if clock_label.normal:
                clock_label.normal = False
                clock_label.font = font2
        clock_label.text = f"{weather_description}"

    bbx, bby, bbwidth, bbh = clock_label.bounding_box
    # Center the label
    clock_label.x = round(display.width / 2 - bbwidth / 2)
    clock_label.y = display.height // 4
    if DEBUG:
        print("Label bounding box: {},{},{},{}".format(bbx, bby, bbwidth, bbh))
        print("Label x: {} y: {}".format(clock_label.x, clock_label.y))


def scroll_second_line():
    if event_label.text is None or event_label.x < -event_label.bounding_box[2]:
        event_label.text = ''
        event_label.x = display.width
        event_label.y = display.height // 4 * 3
        event_label.text = contests.get_next_contest_string()
    else:
        event_label.x -= 1


weather = Weather()
contests = Contests()
last_check = None
update_time(weather=weather, contests=contests)  # Display whatever time is on the board
group.append(clock_label)  # add the clock label to the group
group.append(event_label)


def check_button_press():
    if not button_up.value:
        print('up button pushed')
        clock_label.color_idx += 1
        if clock_label.color_idx >= len(color_codes) + 1:
            clock_label.color_idx = 1
        clock_label.color = color[clock_label.color_idx]
        time.sleep(0.5)
    elif not button_down.value:
        print('down button pushed')
        event_label.color_idx += 1
        if event_label.color_idx >= len(color_codes) + 1:
            event_label.color_idx = 1
        event_label.color = color[event_label.color_idx]
        time.sleep(0.5)


while True:
    check_button_press()
    if last_check is None or time.monotonic() > last_check + 3600:  # Once an hour
        try:
            clock_label.text = 'Time'
            clock_label.x = 0
            event_label.text = 'Sync'
            event_label.x = 0
            network.get_local_time()  # Synchronize Board's clock to Internet
            last_check = time.monotonic()
        except RuntimeError as e:
            print("Some error occured, retrying! -", e)

    update_time(weather=weather, contests=contests)
    scroll_second_line()

    time.sleep(0.03)
