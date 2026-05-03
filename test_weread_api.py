import requests
import json
import os

STATE_PATH = os.path.join('data', 'state.json')

def get_session():
    if not os.path.exists(STATE_PATH):
        return None, None
    with open(STATE_PATH, 'r') as f:
        state = json.load(f)
    cookies = {c['name']: c['value'] for c in state['cookies']}
    vid = cookies.get('wr_vid')
    return cookies, vid

def run_test():
    cookies, vid = get_session()
    if not cookies:
        print("No session.")
        return

    headers = {
        'User-Agent': 'WeRead/7.3.0 (iPhone; iOS 16.0; Scale/3.00)',
        'Host': 'i.weread.qq.com',
        'Accept': '*/*',
        'Accept-Language': 'zh-Hans-CN;q=1'
    }

    # Step 1: Search for Account
    name = "小木易仿真"
    search_url = f"https://i.weread.qq.com/store/search?keyword={name}&count=10"
    print(f"Step 1: Searching for '{name}'...")
    r = requests.get(search_url, headers=headers, cookies=cookies)
    print(f"  Status: {r.status_code}")
    
    try:
        search_data = r.json()
        mp_id = None
        for record in search_data.get('records', []):
            book = record.get('book', {})
            book_id = book.get('bookId', '')
            if book_id.startswith('MP_WXS_'):
                print(f"  ✅ Found Account ID: {book_id}")
                mp_id = book_id
                break
        
        if not mp_id:
            print("  ❌ No Official Account found in search results.")
            return

        # Step 2: Get Articles
        articles_url = f"https://i.weread.qq.com/book/articles?bookId={mp_id}&count=10"
        print(f"\nStep 2: Fetching articles for {mp_id}...")
        r = requests.get(articles_url, headers=headers, cookies=cookies)
        print(f"  Status: {r.status_code}")
        
        articles_data = r.json()
        articles = articles_data.get('reviews', []) # WeRead uses 'reviews' for MP articles in some versions
        if not articles:
            # Try 'articles' key
            articles = articles_data.get('articles', [])
            
        print(f"  Found {len(articles)} articles.")
        for art in articles[:3]:
            # The structure depends on the version, usually has 'review' or 'article'
            item = art.get('review', art)
            print(f"  - {item.get('title')} -> {item.get('url')}")

    except Exception as e:
        print(f"  Error: {e}")
        print("Raw Response snippet:", r.text[:500])

if __name__ == "__main__":
    run_test()
