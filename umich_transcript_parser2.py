import requests
from bs4 import BeautifulSoup

# Requires manual cookie authentication first
SESSION_COOKIE = 'vhovi5ct6mu9512pqfum84fnuq'

url = 'https://leccap.engin.umich.edu/leccap/player/r/eygmQB'

headers = {
    'Cookie': f'leccap_session={SESSION_COOKIE}',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')
print(soup)
# Extract transcript
transcript = []
for row in soup.select('div.transcript-row'):
    time = row.select_one('.transcript-time').get_text(strip=True)
    text = row.select_one('.transcript-text span').get_text(strip=True)
    transcript.append(f"{time}: {text}")

print('\n'.join(transcript))