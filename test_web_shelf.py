import requests
import json
import os

STATE_PATH = os.path.join('data', 'state.json')

def test_web_shelf():
    if not os.path.exists(STATE_PATH):
        print("No session.")
        return

    with open(STATE_PATH, 'r') as f:
        state = json.load(f)
    
    cookies = {c['name']: c['value'] for c in state['cookies']}
    
    # Web API: Shelf
    url = "https://weread.qq.com/web/shelf/sync"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://weread.qq.com/web/shelf',
        'Accept': 'application/json, text/plain, */*'
    }
    
    print(f"Calling Web Shelf: {url}")
    r = requests.get(url, headers=headers, cookies=cookies)
    print(f"Status: {r.status_code}")
    try:
        data = r.json()
        print("Shelf Items:")
        for item in data.get('books', []):
            print(f"- {item.get('title')} ({item.get('bookId')})")
    except:
        print("Response:", r.text[:500])

if __name__ == "__main__":
    test_web_shelf()
