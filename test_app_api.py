import requests
import json
import os

STATE_PATH = os.path.join('data', 'state.json')

def test_api():
    if not os.path.exists(STATE_PATH):
        print("No state file.")
        return

    with open(STATE_PATH, 'r') as f:
        state = json.load(f)
    
    cookies = {c['name']: c['value'] for c in state['cookies']}
    
    # API: Get history for a specific account
    # We use the numeric ID (3988521186) or try with biz
    mp_id = '3988521186'
    url = f"https://i.weread.qq.com/mp/history?mpId={mp_id}"
    
    headers = {
        'User-Agent': 'WeRead/7.3.0 (iPhone; iOS 16.0; Scale/3.00)',
        'Host': 'i.weread.qq.com',
        'Connection': 'keep-alive',
        'Accept': '*/*',
        'Accept-Language': 'zh-Hans-CN;q=1'
    }
    
    print(f"Calling API: {url}")
    r = requests.get(url, headers=headers, cookies=cookies, timeout=10)
    print(f"Status: {r.status_code}")
    try:
        data = r.json()
        print("Response Data Snippet:", json.dumps(data, indent=2, ensure_ascii=False)[:500])
    except:
        print("Raw Response:", r.text[:200])

if __name__ == "__main__":
    test_api()
