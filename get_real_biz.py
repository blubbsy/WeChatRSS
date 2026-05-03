import requests
import re

def get_biz(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers)
    # Search for __biz=... or biz=...
    match = re.search(r'__biz=([^&"]+)', r.text)
    if match:
        return match.group(1)
    match = re.search(r'var biz = "([^"]+)"', r.text)
    if match:
        return match.group(1)
    return None

if __name__ == "__main__":
    url1 = "https://mp.weixin.qq.com/s/zkiNHp8cfsojGcOwWpI5Ng"
    url2 = "https://mp.weixin.qq.com/s/AD2OAFCfJaKsEzmof3ASg"
    print(f"URL 1 Biz: {get_biz(url1)}")
    print(f"URL 2 Biz: {get_biz(url2)}")
