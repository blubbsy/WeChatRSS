import requests
import re

def test_extract():
    url = 'https://mp.weixin.qq.com/s/AD2OAFCf0JaKsEzmof3ASg'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {r.status_code}")
        biz = re.search(r'var biz = "([^"]+)"', r.text)
        name = re.search(r'var nickname = "([^"]+)"', r.text)
        print(f"Biz: {biz.group(1) if biz else 'None'}")
        print(f"Name: {name.group(1) if name else 'None'}")
        
        # Check for another common pattern
        if not biz:
            # Sometimes it's in the meta tags or other script vars
            biz = re.search(r'__biz=([^&"]+)', r.text)
            print(f"Biz (Alt): {biz.group(1) if biz else 'None'}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_extract()
