import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import concurrent.futures
import re

# TOR 네트워크를 활용하기 위한 프록시 설정 (다크웹 모드)
PROXIES = {
    'http': 'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050'
}

# 일반적인 브라우저 User-Agent 헤더
HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/110.0.0.0 Safari/537.36')
}

class MultiWebScanner:
    def __init__(self, target_url, dictionary, mode='normal'):
        """
        초기화 함수: 대상 URL, 딕셔너리 목록, 모드('normal' 또는 'darkweb')를 입력받습니다.
        모드가 'darkweb'이면 TOR 프록시를 적용합니다.
        """
        self.target_url = target_url.rstrip('/')
        self.dictionary = dictionary
        self.base_domain = urlparse(self.target_url).netloc
        self.found_directories = {}
        self.dictionary_scanned = set()  # 이미 딕셔너리 스캔을 수행한 URL 목록
        self.mode = mode
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        if self.mode == 'darkweb':
            self.session.proxies = PROXIES

    def fetch_url(self, url, timeout=10):
        """
        URL에 GET 요청을 보내고, 실패 시 None을 반환합니다.
        """
        try:
            response = self.session.get(url, timeout=timeout)
            return response
        except requests.RequestException as e:
            print(f"[!] {url} 접근 중 오류 발생: {e}")
            return None

    def analyze_framework(self, response):
        """
        HTTP 헤더와 HTML 내용을 분석하여 PHP 기반 여부를 추론합니다.
        """
        if not response:
            print("[-] 응답이 없으므로 프레임워크 분석 불가")
            return None

        server_header = response.headers.get('Server', '')
        x_powered_by = response.headers.get('X-Powered-By', '')
        print(f"[+] Server header: {server_header}")
        print(f"[+] X-Powered-By: {x_powered_by}")

        if 'PHP' in x_powered_by.upper():
            print("[+] 헤더 분석 결과 PHP 기반 사이트로 판단")
            return 'PHP'

        if re.search(r'\.php', response.text, re.IGNORECASE):
            print("[+] HTML 분석 결과 PHP 기반 사이트로 판단")
            return 'PHP'

        print("[-] 웹 프레임워크를 명확하게 판단하지 못했습니다.")
        return None

    def dictionary_scan_single(self, base_url, dir_name):
        """
        주어진 base_url과 딕셔너리 항목을 조합하여 URL을 요청한 후,
        디렉토리 리스팅 여부와 상태 코드를 확인합니다.
        """
        url = f"{base_url.rstrip('/')}/{dir_name.lstrip('/')}"
        response = self.fetch_url(url)
        if response:
            status_code = response.status_code
            content_length = len(response.content)
            directory_listing = False
            if status_code == 200 and re.search(r"Index of /", response.text, re.IGNORECASE):
                directory_listing = True
            return url, {
                'status_code': status_code,
                'content_length': content_length,
                'directory_listing': directory_listing
            }
        else:
            return url, None

    def dictionary_scan(self, base_url):
        """
        주어진 base_url에 대해 딕셔너리 목록으로 디렉토리 존재 여부를 멀티스레딩으로 스캔합니다.
        """
        print(f"[+] 딕셔너리 스캔 시작: {base_url}")
        results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_dir = {
                executor.submit(self.dictionary_scan_single, base_url, dir_name): dir_name
                for dir_name in self.dictionary
            }
            for future in concurrent.futures.as_completed(future_to_dir):
                dir_name = future_to_dir[future]
                try:
                    url, result = future.result()
                    results[url] = result
                except Exception as e:
                    print(f"[!] 디렉토리 {dir_name} 스캔 중 오류 발생: {e}")
                    results[dir_name] = None
        self.found_directories.update(results)

    def crawl_recursive(self, current_url, visited, depth, max_depth):
        """
        재귀적으로 내부 링크를 방문하며 각 페이지에서 PHP 여부를 분석하고,
        PHP 기반 페이지이면 딕셔너리 스캔을 진행합니다.
        """
        if depth > max_depth:
            return
        if current_url in visited:
            return

        print(f"[+] 크롤링 (Depth: {depth}) : {current_url}")
        visited.add(current_url)
        response = self.fetch_url(current_url)
        if not response:
            return

        framework = self.analyze_framework(response)
        if framework == 'PHP' and current_url not in self.dictionary_scanned:
            self.dictionary_scanned.add(current_url)
            self.dictionary_scan(current_url)

        soup = BeautifulSoup(response.text, 'html.parser')
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            full_url = urljoin(current_url, href)
            parsed = urlparse(full_url)
            if parsed.netloc == self.base_domain and parsed.scheme in ['http', 'https']:
                if full_url not in visited:
                    links.append(full_url)

        for link in links:
            if link not in visited:
                self.crawl_recursive(link, visited, depth + 1, max_depth)

    def report(self):
        """
        스캔된 딕셔너리 결과를 출력합니다.
        """
        print("\n[+] 스캔 결과 보고:")
        for url, info in self.found_directories.items():
            print(f"URL: {url}")
            if info:
                print(f"  Status: {info['status_code']}, Length: {info['content_length']}, Directory Listing: {info['directory_listing']}")
            else:
                print("  요청 실패")

def main():
    """
    실행 모드에 따라 다크웹과 일반 웹을 선택할 수 있습니다.
    
    1. **일반 웹 스캔 방법:**
       - mode를 'normal'로 설정합니다.
       - target_url에 예) "http://testphp.vulnweb.com" 등을 지정합니다.
       - TOR 프록시 없이 일반 네트워크로 접속합니다.
       
    2. **다크웹 스캔 방법:**
       - mode를 'darkweb'으로 설정합니다.
       - target_url에 .onion URL (예: "http://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion")을 지정합니다.
       - TOR 네트워크가 구동 중이어야 하며, 해당 환경에서 프록시 설정(PROXIES)이 적용됩니다.
    """
    # 실행 모드를 설정: 'normal' 또는 'darkweb'
    mode = 'darkweb'  # 다크웹 스캔을 원하면 'darkweb'으로 변경하세요.
    
    # 모드에 따라 대상 URL 설정
    if mode == 'darkweb':
        target_url = "http://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion"
    else:
        target_url = "http://testphp.vulnweb.com"

    # PHP 기반 사이트에서 자주 쓰이는 URL 경로를 포함하는 딕셔너리 목록
    directory_list = ["admin", "backup", "config", "logs", "test", "phpmyadmin", "wp-admin"]

    scanner = MultiWebScanner(target_url, directory_list, mode=mode)
    
    # 재귀 크롤링 실행 (최대 깊이 조절: 여기서는 2로 설정)
    visited = set()
    max_depth = 2
    scanner.crawl_recursive(scanner.target_url, visited, depth=0, max_depth=max_depth)
    
    # 스캔 결과 출력
    scanner.report()

if __name__ == "__main__":
    main()


'''
이 코드는 초기화 시 모드(mode) 매개변수로 'normal' 또는 'darkweb'를 지정할 수 있습니다.

모드를 'normal'로 설정하면 일반 웹 환경에서 동작하며, 프록시 없이 요청을 보냅니다.

모드를 'darkweb'으로 설정하면 TOR 프록시 설정을 적용하여 다크웹(.onion) URL이나 그 외 다크웹 환경에서 사용할 수 있습니다.


일반 웹 스캔:

위 코드에서 mode 변수를 'normal'로 설정합니다.

target_url에 일반 웹 사이트 URL (예: http://testphp.vulnweb.com)을 지정하고 실행하면, TOR 프록시 없이 기본 네트워크 환경에서 크롤링, PHP 감지 및 딕셔너리 스캔이 이루어집니다.

다크웹 스캔:

위 코드에서 mode 변수를 'darkweb'으로 설정합니다.

target_url에 .onion 주소 (예: http://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion)를 지정합니다.

이때, TOR 네트워크(예: Tor 서비스 또는 TOR 브라우저의 프록시)가 반드시 활성화되어 있어야 하며, 코드에서는 프로시 설정이 적용되어 다크웹 사이트에 접속할 수 있습니다.

1. 일반웹, 다크웹 둘 다에 대해서 크롤링 및 디렉토리 리스팅을 시도하는가?
2. 재귀적으로 링크를 추출해서 추출한 사이트들에도 동일하게 크롤링 및 디렉토리 리스팅을 시도하는가?
3. 재귀적인 작업의 depth가 지정되어 있는가?
4. html및  server header, x-powered-by 등을 분석해서 프레임워크를 파악하고, php인 경우에 디렉토리 리스팅을 시도하는가?

'''