from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import requests

response = requests.get("https://example.com", timeout=120)
print(response)
