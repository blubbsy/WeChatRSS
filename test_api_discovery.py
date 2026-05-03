import requests
import json
import os

STATE_PATH = os.path.join('data', 'state.json')

def test_discovery_logic():
    if not os.path.exists(STATE_PATH):
        print("No session.")
        return

    with open(STATE_PATH, 'r') as f:
        state = json.load(f)
    
    cookies = {c['name']: c['value'] for c in state['cookies']}
    vid = cookies.get('wr_vid')
    
    # Discovery Step 1: List followed accounts from Shelf API
    # This is the most reliable way to get IDs
    shelf_url = "https://i.weread.qq.com/shelf/sync"
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 WeRead/7.3.0',
        'Accept': 'application/json',
        'vid': vid
    }
    
    print(f"Checking Shelf API for followed accounts...")
    r = requests.get(shelf_url, headers=headers, cookies=cookies, timeout=10)
    print(f"  Status: {r.status_code}")
    
    try:
        data = r.json()
        print("  Successfully fetched shelf.")
        books = data.get('books', [])
        followed_ids = []
        for b in books:
            if b.get('bookId', '').startswith('MP_WXS_'):
                print(f"  Found: {b.get('title')} -> {b.get('bookId')}")
                followed_ids.append(b.get('bookId'))
        
        if followed_ids:
            # Step 2: Try to get articles for the first found account
            target = followed_ids[0]
            articles_url = f"https://i.weread.qq.com/book/articles?bookId={target}&count=5"
            print(f"\nFetching articles for {target}...")
            ar = requests.get(articles_url, headers=headers, cookies=cookies, timeout=10)
            print(f"  Status: {ar.status_code}")
            if ar.status_code == 200:
                articles = ar.json().get('reviews', [])
                print(f"  Found {len(articles)} articles via API!")
            else:
                print("  Failed to fetch articles via API.")
    except Exception as e:
        print(f"  Error parsing API: {e}")
        print("  Raw Response:", r.text[:200])

if __name__ == "__main__":
    test_discovery_logic()
