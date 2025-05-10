import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import concurrent.futures
import re
from urllib.parse import urljoin, urlparse

# TOR 네트워크를 활용하기 위한 프록시 설정 (다크웹 모드)
PROXIES = {
    'http': 'socks5h://torproxy:9050',  # 127.0.0.1 -> torproxy
    'https': 'socks5h://torproxy:9050' # 127.0.0.1 -> torproxy
}

# 일반적인 브라우저 User-Agent 헤더
HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/110.0.0.0 Safari/537.36')
}

class MultiWebScanner:
    def __init__(self, target_url, dictionary, mode='normal', exclusions=None): # Add exclusions parameter
        """
        초기화 함수: 대상 URL, 딕셔너리 목록, 모드('normal' 또는 'darkweb'), 제외 목록을 입력받습니다.
        모드가 'darkweb'이면 TOR 프록시를 적용합니다.
        """
        self.target_url = target_url.rstrip('/')
        self.dictionary = dictionary
        self.base_domain = urlparse(self.target_url).netloc
        self.found_directories = {}
        self.dictionary_scanned = set()  # 이미 딕셔너리 스캔을 수행한 URL 목록
        self.mode = mode
        self.exclusions = set(exclusions) if exclusions else set() # Store exclusions as a set for efficient lookup
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        if self.mode == 'darkweb':
            self.session.proxies = PROXIES

    def is_excluded(self, url):
        """
        주어진 URL 또는 도메인이 제외 목록에 있는지 확인합니다.
        """
        parsed_url = urlparse(url)
        # Check full URL
        if url in self.exclusions:
            return True
        # Check domain/IP
        if parsed_url.netloc in self.exclusions:
            return True
        return False

    def fetch_url(self, url, timeout=10):
        """
        URL에 GET 요청을 보내고, 실패 시 None을 반환합니다.
        제외 목록에 있는 URL은 요청하지 않습니다.
        """
        if self.is_excluded(url):
            print(f"[-] 제외된 URL: {url}")
            return None
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
        디렉토리 리스팅 여부와 상태 코드를 확인.
        제외된 URL은 스캔하지 않음.
        """
        url = f"{base_url.rstrip('/')}/{dir_name.lstrip('/')}"
        if self.is_excluded(url):
            print(f"[-] 딕셔너리 스캔에서 제외된 URL: {url}")
            return url, None

        response = self.fetch_url(url) # fetch_url will also check exclusion
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
        주어진 base_url에 대해 딕셔너리 목록으로 디렉토리 존재 여부를 멀티스레딩으로 스캔.
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
        제외된 URL은 크롤링하지 않습니다.
        """
        if depth > max_depth:
            return
        if current_url in visited:
            return
        
        if self.is_excluded(current_url):
            print(f"[-] 크롤링에서 제외된 URL: {current_url}")
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
                if full_url not in visited and not self.is_excluded(full_url): # Check exclusion before adding to links
                    links.append(full_url)

        for link in links:
            if link not in visited: # Redundant check if already done above, but safe
                self.crawl_recursive(link, visited, depth + 1, max_depth)

    def report(self):
        print("\n[+] 스캔 결과 보고:")
        for url, info in self.found_directories.items():
            print(f"URL: {url}")
            if info:
                print(f"  Status: {info['status_code']}, Length: {info['content_length']}, Directory Listing: {info['directory_listing']}")
            else:
                print("  요청 실패")

    def run(self, max_depth=2):
        visited = set()
        self.crawl_recursive(self.target_url, visited, depth=0, max_depth=max_depth)
        return self.found_directories
