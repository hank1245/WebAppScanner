import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import concurrent.futures
import re
from urllib.parse import urljoin, urlparse
# https://p53lf57qovyuvwsc6xnrppddxpr23otqjafmtmcstail6x7cq2qcyd.onion
# https://facebookwkhpilnemxj7asaniu7vnjjbiltxjqhye3mhbshg7kx5tfyd.onion
# https://3g2upl4pq6kufc4m.onion

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
    def __init__(self, target_url, dictionary, mode='normal', exclusions=None, respect_robots_txt=True, username=None, password=None):
        """
        초기화 함수: 대상 URL, 딕셔너리 목록, 모드('normal' 또는 'darkweb'), 제외 목록, 로그인 자격 증명을 입력받습니다.
        모드가 'darkweb'이면 TOR 프록시를 적용합니다.
        respect_robots_txt: robots.txt의 Disallow 규칙을 따를지 여부
        """
        self.target_url = target_url.rstrip('/')
        self.dictionary = dictionary
        self.base_domain = urlparse(self.target_url).netloc
        self.found_directories = {}
        self.dictionary_scanned = set()
        self.mode = mode
        self.exclusions = set(exclusions) if exclusions else set()
        self.session = requests.Session() # requests.Session() will manage cookies
        self.session.headers.update(HEADERS)
        self.respect_robots_txt = respect_robots_txt
        self.robots_disallowed_paths = set()
        self.username = username
        self.password = password
        self.logged_in_target = None # Track which target URL login was attempted for
        
        if self.mode == 'darkweb':
            self.session.proxies = PROXIES
            self.session.timeout = 30  # 다크웹 모드에서는 더 긴 타임아웃
            self.session.headers.update({ # 다크웹 특화 헤더
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0',
                'Accept-Language': 'en-US,en;q=0.5',
                'DNT': '1'
            })
            
        if self.respect_robots_txt:
            # 생성자에서 robots.txt 파싱 실행
            self._parse_robots_txt()

    def _attempt_login(self):
        """
        제공된 자격 증명을 사용하여 대상 URL에 로그인을 시도합니다.
        매우 기본적인 로그인 시도이며, 모든 사이트에서 작동하지 않을 수 있습니다.
        """
        if not self.username or not self.password:
            return False

        if self.logged_in_target == self.target_url: # 이미 이 타겟에 대해 로그인 시도/성공
            print(f"[*] 이미 {self.target_url}에 로그인 시도/성공함.")
            return True # 혹은 저장된 로그인 상태 반환

        print(f"[+] {self.target_url}에 로그인 시도 중 (사용자: {self.username})...")
        
        # 일반적인 로그인 경로 시도
        login_paths = ["login", "signin", "wp-login.php", "admin/login", "user/login", "auth/login"] 
        # 시도해볼 기본 URL (타겟 URL 자체도 로그인 페이지일 수 있음)
        base_login_urls = [self.target_url]
        for path in login_paths:
            base_login_urls.append(f"{self.target_url}/{path.lstrip('/')}")

        # 일반적인 폼 필드 이름
        username_fields = ["username", "user", "email", "log", "user_login"]
        password_fields = ["password", "pass", "pwd", "user_pass"]

        initial_cookies_count = len(self.session.cookies)

        for login_url_candidate in base_login_urls:
            try:
                print(f"  -> 로그인 URL 시도: {login_url_candidate}")
                # 간단한 POST 요청 시도, CSRF 등 복잡한 케이스는 처리하지 않음
                # 다양한 필드명 조합 시도
                for u_field in username_fields:
                    for p_field in password_fields:
                        login_data = {
                            u_field: self.username,
                            p_field: self.password,
                            # 일부 사이트는 추가 필드 요구 가능 (예: 'remember_me', 'submit')
                        }
                        
                        # POST 요청 전 GET 요청으로 쿠키나 CSRF 토큰을 얻는 것이 더 좋지만, 단순화
                        response = self.session.post(login_url_candidate, data=login_data, timeout=15, allow_redirects=True)
                        
                        # 로그인 성공 추론:
                        # 1. 상태 코드가 200 OK이고, 응답 내용에 "logout", "dashboard", username 등이 포함되는 경우
                        # 2. 리다이렉션(302) 후 다른 페이지로 이동하고 쿠키가 설정된 경우
                        # 3. 로그인 실패 메시지가 없는 경우
                        
                        current_cookies_count = len(self.session.cookies)
                        
                        # 매우 기본적인 성공 확인: 쿠키가 새로 설정되었거나, 특정 성공 키워드가 있거나, 에러 메시지가 없는 경우
                        login_error_patterns = ["invalid username", "incorrect password", "login failed", "authentication failed"]
                        login_success_patterns = ["logout", "dashboard", "my account", self.username]

                        response_text_lower = response.text.lower()
                        
                        has_error = any(err_pattern in response_text_lower for err_pattern in login_error_patterns)
                        has_success_keyword = any(succ_pattern in response_text_lower for succ_pattern in login_success_patterns)

                        if response.status_code == 200 and not has_error and (has_success_keyword or current_cookies_count > initial_cookies_count):
                            print(f"[+] {login_url_candidate} 에서 로그인 성공한 것으로 보임 (사용자: {self.username}).")
                            self.logged_in_target = self.target_url
                            return True
                        elif response.history and current_cookies_count > initial_cookies_count and not has_error: # 리다이렉션 발생 및 쿠키 변경
                             print(f"[+] {login_url_candidate} 에서 리다이렉션 후 로그인 성공한 것으로 보임 (사용자: {self.username}).")
                             self.logged_in_target = self.target_url
                             return True
                print(f"  [-] {login_url_candidate} 에서 자동 로그인 필드명 조합 실패.")
            except requests.RequestException as e:
                print(f"  [!] {login_url_candidate} 로그인 시도 중 오류: {e}")
            except Exception as e:
                print(f"  [!] {login_url_candidate} 로그인 시도 중 예기치 않은 오류: {e}")
        
        print(f"[-] {self.target_url} 에 대한 자동 로그인 시도 실패.")
        return False

    def _parse_robots_txt(self):
        """
        대상 URL의 robots.txt 파일을 파싱하여 Disallow 경로를 추출.
        """
        parsed_url = urlparse(self.target_url)
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
        
        try:
            print(f"[+] robots.txt 확인: {robots_url}")
            # robots.txt 요청 시 타임아웃은 모드에 따라 다르게 설정
            timeout = 30 if self.mode == 'darkweb' else 10
            response = self.session.get(robots_url, timeout=timeout)
            if response.status_code != 200:
                print(f"[-] robots.txt가 없거나 접근할 수 없습니다: {response.status_code}")
                return
                
            lines = response.text.splitlines()
            current_user_agent = "*"  # 기본은 와일드카드 유저 에이전트
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):  # 주석 또는 빈 줄 무시
                    continue
                    
                parts = line.split(':', 1)
                if len(parts) != 2:
                    continue
                    
                directive = parts[0].strip().lower()
                value = parts[1].strip()
                
                if directive == "user-agent":
                    current_user_agent = value
                elif directive == "disallow" and (current_user_agent == "*" or "mozilla" in current_user_agent.lower() or self.session.headers['User-Agent'] in current_user_agent):
                    if value:  # 빈 Disallow는 모든 접근 허용이므로 무시
                        path = value
                        # 절대 경로로 변환
                        disallowed_url = urljoin(f"{parsed_url.scheme}://{parsed_url.netloc}", path)
                        self.robots_disallowed_paths.add(disallowed_url)
                        print(f"[+] robots.txt Disallow 경로 추가: {disallowed_url}")
            
            print(f"[+] 총 {len(self.robots_disallowed_paths)}개의 Disallow 경로 확인됨")
        except Exception as e:
            print(f"[!] robots.txt 파싱 중 오류 발생: {e}")

    def is_disallowed_by_robots(self, url):
        """
        URL이 robots.txt의 Disallow 규칙에 해당하는지 확인합니다.
        """
        if not self.respect_robots_txt or not self.robots_disallowed_paths:
            return False
            
        for disallowed_path in self.robots_disallowed_paths:
            if url.startswith(disallowed_path):
                print(f"[robots.txt] 접근 제한된 URL: {url}")
                return True
        return False

    def is_excluded(self, url):
        """
        주어진 URL 또는 도메인이 제외 목록에 있는지 확인합니다.
        또는 robots.txt에 의해 차단되는지 확인합니다.
        """
        parsed_url = urlparse(url)
        # Check full URL
        if url in self.exclusions:
            return True
        # Check domain/IP
        if parsed_url.netloc in self.exclusions:
            return True
        # Check robots.txt rules
        if self.is_disallowed_by_robots(url):
            return True
        return False

    def fetch_url(self, url, timeout=None):
        """
        URL에 GET 요청을 보내고, 실패 시 None을 반환합니다.
        제외 목록에 있는 URL은 요청하지 않습니다.
        다크웹 모드에서는 더 긴 타임아웃 사용
        """
        if self.is_excluded(url):
            print(f"[-] 제외된 URL: {url}")
            return None
        
        # 모드에 따라 기본 타임아웃 설정
        if timeout is None:
            timeout = 30 if self.mode == 'darkweb' else 10
            
        try:
            response = self.session.get(url, timeout=timeout)
            return response
        except requests.RequestException as e:
            print(f"[!] {url} 접근 중 오류 발생: {e}")
            return None

    def _check_directory_listing_patterns(self, text_content):
        """
        HTML 내용에서 디렉토리 리스팅 관련 패턴을 확인합니다.
        """
        patterns = [
            r"Index of /",
            r"<title>Index of .*?</title>", # Apache, Nginx 등
            r"Parent Directory", # Apache 등
            r"\[To Parent Directory\]", # 일부 오래된 서버
            r"Directory Listing For /", # IIS 등
            r"<h1>Index of .*?</h1>" # 일반적인 패턴
        ]
        for pattern in patterns:
            if re.search(pattern, text_content, re.IGNORECASE):
                return True
        return False

    def analyze_directory_listing(self, response):
        """
        응답을 분석하여 디렉토리 리스팅 여부를 판단합니다.
        Apache, Nginx 등의 서버 설정 및 인덱스 파일 부재로 인한 노출을 감지합니다.
        """
        if not response: # 응답이 없는 경우 (예: 요청 실패) False 반환
            return False
        # 디렉토리 리스팅은 주로 200 OK 응답에서 확인되지만, 
        # 경우에 따라 403 Forbidden 에서도 리스팅 패턴이 나타날 수 있으므로 status_code != 200 조건 완화 고려.
        # 여기서는 일단 200을 기준으로 하되, 필요시 확장 가능.
        if response.status_code != 200: 
            return False

        content_type = response.headers.get('Content-Type', '').lower()
        
        # HTML 응답인 경우, 특정 패턴으로 디렉토리 리스팅 확인
        if 'text/html' in content_type:
            if self._check_directory_listing_patterns(response.text):
                return True
        
        # Content-Type이 text/plain 이면서 내용이 디렉토리 구조와 유사한 경우 (일부 서버)
        # 이 부분은 오탐 가능성이 있어 매우 신중하게 패턴을 정의해야 함.
        # 예: 파일명과 크기, 날짜 등이 반복되는 패턴
        # 현재는 HTML 기반 패턴에 집중

        # 서버 헤더를 통한 추론 (Apache, Nginx의 autoindex on 등)
        # Server 헤더는 위조될 수 있으므로 참고용으로만 사용
        server_header = response.headers.get('Server', '').lower()
        if 'apache' in server_header:
            # Apache의 경우 Options Indexes 또는 Options +Indexes 설정 시 노출
            # 직접적인 헤더 확인은 어려우므로 HTML 내용 분석에 의존
            pass
        elif 'nginx' in server_header:
            # Nginx의 경우 autoindex on; 설정 시 노출
            # 직접적인 헤더 확인은 어려우므로 HTML 내용 분석에 의존
            pass
            
        # 인덱스 파일(index.html, index.php 등) 부재로 인한 노출은
        # 서버가 디렉토리 리스팅을 보여줄 때 위 패턴들로 감지됨.

        return False

    def dictionary_scan_single(self, base_url, dir_name):
        """
        주어진 base_url과 딕셔너리 항목을 조합하여 URL을 요청한 후,
        디렉토리 리스팅 여부와 상태 코드를 확인.
        제외된 URL은 스캔하지 않음.
        """
        url = f"{base_url.rstrip('/')}/{dir_name.lstrip('/')}"
        
        if self.is_excluded(url):
            print(f"[-] 딕셔너리 스캔에서 제외된 URL (초기 확인): {url}")
            return url, {
                'status_code': 'EXCLUDED',
                'content_length': 0,
                'directory_listing': False,
                'note': 'URL excluded by configuration or robots.txt.'
            }

        response = self.fetch_url(url) 
        if response:
            status_code = response.status_code
            content_length = len(response.content)
            # 디렉토리 리스팅 분석은 성공적인 응답(주로 200)에 대해 수행
            directory_listing = self.analyze_directory_listing(response) if status_code == 200 else False
            
            return url, {
                'status_code': status_code,
                'content_length': content_length,
                'directory_listing': directory_listing,
                'note': f'Scan attempted. Status: {status_code}' if status_code != 200 else 'Scan successful.'
            }
        else:
            # fetch_url이 None을 반환한 경우 (요청 실패 또는 fetch_url 내부에서 제외됨)
            return url, {
                'status_code': 'NO_RESPONSE_OR_ERROR',
                'content_length': 0,
                'directory_listing': False,
                'note': 'Failed to fetch URL (request error or excluded by fetch_url).'
            }

    def dictionary_scan(self, base_url):
        """
        주어진 base_url에 대해 딕셔너리 목록으로 디렉토리 존재 여부를 멀티스레딩으로 스캔.
        """
        if base_url in self.dictionary_scanned:
            print(f"[*] 이미 딕셔너리 스캔 완료: {base_url}")
            return
            
        print(f"[+] 딕셔 dictionary_scan 시작: {base_url}")
        results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_dir = {
                executor.submit(self.dictionary_scan_single, base_url, dir_name): dir_name
                for dir_name in self.dictionary
            }
            for future in concurrent.futures.as_completed(future_to_dir):
                original_dir_name = future_to_dir[future]
                attempted_url = f"{base_url.rstrip('/')}/{original_dir_name.lstrip('/')}"
                try:
                    _, scan_info = future.result() 
                    results[attempted_url] = scan_info 
                except Exception as e:
                    print(f"[!] 딕셔너리 항목 {original_dir_name} 스캔 작업 중 예외 발생: {e}")
                    results[attempted_url] = {
                        'status_code': 'SCANNER_TASK_ERROR',
                        'content_length': 0,
                        'directory_listing': False,
                        'note': f'Internal error during scan attempt for {original_dir_name}: {str(e)}'
                    }
        self.found_directories.update(results)
        self.dictionary_scanned.add(base_url)

    def crawl_recursive(self, current_url, visited, depth, max_depth):
        """
        재귀적으로 내부 링크를 방문하며 각 페이지에서 딕셔너리 스캔을 진행합니다.
        제외된 URL은 크롤링하지 않습니다.
        """
        if depth > max_depth:
            print(f"[*] 최대 깊이 도달: {current_url} (Depth: {depth})")
            return
        if current_url in visited:
            return
        
        if self.is_excluded(current_url):
            print(f"[-] 크롤링에서 제외된 URL: {current_url}")
            return

        print(f"[+] 크롤링 (Depth: {depth}) : {current_url}")
        visited.add(current_url)
        
        # 현재 URL에 대해 항상 딕셔너리 스캔 시도
        # (단, 이미 해당 URL 루트로 스캔한 적이 없다면)
        # current_url 자체가 디렉토리일 수 있으므로, 해당 URL을 base로 스캔
        parsed_current_url = urlparse(current_url)
        # URL이 '/'로 끝나지 않으면, 마지막 세그먼트를 제거하여 부모 디렉토리를 base로 사용하거나,
        # 현재 URL 자체를 base로 사용할지 결정 필요.
        # 여기서는 현재 URL을 base로 하여 딕셔너리 스캔을 시도.
        # 예를 들어 example.com/path1/ 에 대해 딕셔너리 스캔
        # example.com/path1/file.html 에 대해서도 example.com/path1/file.html/admin/ 등을 시도하게 됨.
        # 이는 의도와 다를 수 있으므로, URL이 디렉토리 형태일 때만 스캔하도록 조정 가능.
        # 현재는 모든 발견된 URL에 대해 딕셔너리 스캔을 시도.
        self.dictionary_scan(current_url)

        response = self.fetch_url(current_url)
        if not response:
            return

        # 프레임워크 분석은 참고용으로 남겨둘 수 있으나, 딕셔너리 스캔 결정에는 사용하지 않음
        # self.analyze_framework(response) 

        soup = BeautifulSoup(response.text, 'html.parser')
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            full_url = urljoin(current_url, href)
            parsed_full_url = urlparse(full_url)
            
            # 외부 도메인 및 javascript:, mailto: 등 스킵
            if parsed_full_url.netloc != self.base_domain or parsed_full_url.scheme not in ['http', 'https']:
                continue
            
            # 이미 방문했거나 제외된 URL 스킵
            if full_url in visited or self.is_excluded(full_url):
                continue
                
            links.append(full_url)

        for link in links:
            # 재귀 호출 전 중복 방문 확인 (이미 links 리스트에 추가할 때 했지만 안전장치)
            if link not in visited: 
                self.crawl_recursive(link, visited, depth + 1, max_depth)

    def report(self):
        print("\n[+] 스캔 결과 보고:")
        if not self.found_directories:
            print("[-] 발견된 디렉토리 없음.")
            return
            
        for url, info in self.found_directories.items():
            if info: # 요청 성공 및 분석 정보가 있는 경우
                print(f"URL: {url}")
                print(f"  Status: {info['status_code']}, Length: {info['content_length']}")
                if info['directory_listing']:
                    print(f"  Directory Listing: Enabled (잠재적 노출)")
                else:
                    print(f"  Directory Listing: Disabled or Not Detected")
            # else: # 요청 실패 또는 분석 정보가 없는 경우 (dictionary_scan_single에서 None 반환 시)
            #     print(f"URL: {url}")
            #     print("  요청 실패 또는 분석 정보 없음")

    def run(self, max_depth=2):
        """
        스캔 실행 함수.
        1. (선택적) 로그인 시도.
        2. 초기 target_url에 대해 딕셔너리 스캔 수행.
        3. target_url부터 재귀적 크롤링 시작.
        """
        if self.username and self.password:
            self._attempt_login() # 세션 쿠키가 설정될 수 있음

        visited = set()
        
        # 1. 초기 target_url에 대해 딕셔너리 스캔 수행
        print(f"[+] 초기 대상 URL에 대한 딕셔너리 스캔 시작: {self.target_url}")
        self.dictionary_scan(self.target_url)
        
        # 2. target_url부터 재귀적 크롤링 시작
        # 크롤링 시작 시 visited에 target_url을 추가하여 중복 크롤링 방지
        # (dictionary_scan 내부에서 visited를 사용하지 않으므로, crawl_recursive의 visited와 별개로 관리)
        print(f"[+] 재귀적 크롤링 시작: {self.target_url}")
        self.crawl_recursive(self.target_url, visited, depth=0, max_depth=max_depth)
        
        return self.found_directories
