import requests
import json
import os

STATE_PATH = os.path.join('data', 'state.json')

def test_i_api():
    if not os.path.exists(STATE_PATH):
        return

    with open(STATE_PATH, 'r') as f:
        state = json.load(f)
    
    cookies = {c['name']: c['value'] for c in state['cookies']}
    vid = cookies.get('wr_vid')
    
    # Try the App API with vid in header
    # biz: Mzk4ODUyMTE4Ng==
    url = f"https://i.weread.qq.com/mp/history?mpId=Mzk4ODUyMTE4Ng=="
    
    headers = {
        'User-Agent': 'WeRead/7.3.0 (iPhone; iOS 16.0; Scale/3.00)',
        'vid': vid,
        'Accept': '*/*'
    }
    
    print(f"Calling i.weread API with vid: {vid}")
    r = requests.get(url, headers=headers, cookies=cookies)
    print(f"Status: {r.status_code}")
    print("Response:", r.text[:200])

if __name__ == "__main__":
    test_i_api()
