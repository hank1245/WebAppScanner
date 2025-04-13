import requests
from bs4 import BeautifulSoup

proxies = {
    'http': 'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050'
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/110.0.0.0 Safari/537.36'
}

def crawl_onion(url):
    try:
        response = requests.get(url, headers=headers, proxies=proxies, timeout=10)
        if response.status_code == 200:
            print(f"[+] {url} 접속 성공")
            # HTML 내용 출력
            print(response.text[:10000])
            soup = BeautifulSoup(response.text, 'html.parser')
            links = [a['href'] for a in soup.find_all('a', href=True)]
            if links:
                print("발견된 링크들:")
                for link in links:
                    if link.startswith('/'): 
                        link = url + link
                    print(f"    - {link}")
            else:
                print("발견된 링크가 없습니다.")
        else:
            print(f"[-] {url} 접근 실패 (상태 코드: {response.status_code})")
    except requests.RequestException as e:
        print(f"[!] 오류 발생: {e}")

crawl_onion("http://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion/")
