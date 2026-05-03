import requests
import json
import os

STATE_PATH = os.path.join('data', 'state.json')

def force_follow():
    if not os.path.exists(STATE_PATH):
        print("No session.")
        return

    with open(STATE_PATH, 'r') as f:
        state = json.load(f)
    
    cookies = {c['name']: c['value'] for c in state['cookies']}
    
    # We use the Base64 ID (Mzk4ODUyMTE4Ng==) for mpId
    biz = 'Mzk4ODUyMTE4Ng=='
    url = "https://weread.qq.com/web/mp/follow"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': f'https://weread.qq.com/web/reader/mp/{biz}',
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/plain, */*'
    }
    
    data = {
        "mpId": biz,
        "follow": 1
    }
    
    print(f"Force Following: {biz}")
    r = requests.post(url, headers=headers, cookies=cookies, json=data)
    print(f"Status: {r.status_code}")
    print("Response:", r.text)

if __name__ == "__main__":
    force_follow()
