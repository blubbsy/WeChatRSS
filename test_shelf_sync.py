import requests
import json
import os

STATE_PATH = os.path.join('data', 'state.json')

def test_shelf_sync():
    if not os.path.exists(STATE_PATH):
        print("No session.")
        return

    with open(STATE_PATH, 'r') as f:
        state = json.load(f)
    
    cookies = {c['name']: c['value'] for c in state['cookies']}
    
    # API: Sync shelf
    url = "https://i.weread.qq.com/shelf/sync"
    
    headers = {
        'User-Agent': 'WeRead/7.3.0 (iPhone; iOS 16.0; Scale/3.00)',
        'Host': 'i.weread.qq.com',
        'Accept': '*/*',
        'Accept-Language': 'zh-Hans-CN;q=1'
    }
    
    print(f"Calling Shelf Sync: {url}")
    r = requests.get(url, headers=headers, cookies=cookies)
    print(f"Status: {r.status_code}")
    try:
        data = r.json()
        print("Shelf Items:")
        books = data.get('books', [])
        for b in books:
            print(f"- {b.get('title')} ({b.get('bookId')})")
    except:
        print("Raw Response:", r.text[:200])

if __name__ == "__main__":
    test_shelf_sync()
