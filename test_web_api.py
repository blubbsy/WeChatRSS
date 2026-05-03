import requests
import json
import os

STATE_PATH = os.path.join('data', 'state.json')

def test_web_api():
    if not os.path.exists(STATE_PATH):
        print("No session.")
        return

    with open(STATE_PATH, 'r') as f:
        state = json.load(f)
    
    cookies = {c['name']: c['value'] for c in state['cookies']}
    
    # Try the web-based chapter info API
    # biz: Mzk4ODUyMTE4Ng== -> 3988521186
    mp_id = 'MP_WXS_3988521186'
    url = f"https://weread.qq.com/web/book/chapterInfos?bookIds={mp_id}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://weread.qq.com/',
        'Accept': 'application/json, text/plain, */*'
    }
    
    print(f"Calling Web API: {url}")
    r = requests.get(url, headers=headers, cookies=cookies)
    print(f"Status: {r.status_code}")
    print("Response:", r.text[:500])

if __name__ == "__main__":
    test_web_api()
