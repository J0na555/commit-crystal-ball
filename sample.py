"""Sample file for testing crystal-ball scan."""

import requests

url = "https://example.com"
response = requests.get(url)

try:
    x = 1 / 0
except:
    pass
