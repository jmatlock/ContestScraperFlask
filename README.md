# ContestScraperFlask
Flask Server and REST API for Instructables Contest info

Related Instructable:  [Instructables Contest Notifier](https://www.instructables.com/Instructables-Contest-Notifier-3-Ways/)

This project scrapes the Instructables Contest web page for information on the current contests. This data is then made available to local devices 
via a locally run Flask Server which provides a JSON Web API appropriate for CircuitPython devices.

Data provided includes:
- Contest name
- Contest deadline
- Days till contest deadline
- URI for the specific contest
- URI/Graphic for the specific contest sized down as appropriate for small screens
- Count of entries
- Timestamp of last pull of Instructables data
- Number of minutes until next data pull from Instructables

Additionally, reference projects for clients are provided using the following devices:
- Adafruit MagTag
- Adafruit Matrix Portal M4
- Adafruit PyPortal
- (TBD) Mobile phone via IFTTT
- (TBD) Discord Chatbot
