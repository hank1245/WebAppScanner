import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import concurrent.futures
import re
from typing import Optional, List # Optional과 List를 typing 모듈에서 가져옵니다.

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

# API 경로 스캔을 위한 특화 사전 (예시)
DEFAULT_API_DICTIONARY = [
    "", # Ensures the base API path itself is tested
    "users", "user", "items", "products", "orders", "cart", "auth", "login", "logout",
    "register", "profile", "settings", "config", "status", "health", "ping", "api-docs",
    "swagger", "openapi", "graphql", "v1", "v2", "v3", "test", "dev", "prod", "data",
    "metrics", "logs", "admin", "management", "payment", "search", "notifications"
]

class MultiWebScanner:
    def __init__(self, target_url, dictionary, mode='normal', exclusions=None, respect_robots_txt=True, session_cookies_string: Optional[str] = None):
        """
        초기화 함수: 대상 URL, 딕셔너리 목록, 모드('normal' 또는 'darkweb'), 제외 목록, 세션 쿠키 문자열을 입력받습니다.
        모드가 'darkweb'이면 TOR 프록시를 적용합니다.
        respect_robots_txt: robots.txt의 Disallow 규칙을 따를지 여부
        """
        self.target_url = target_url.rstrip('/')
        self.dictionary = dictionary # 일반 경로용 사전
        self.api_dictionary = DEFAULT_API_DICTIONARY # API 경로용 사전
        self.base_domain = urlparse(self.target_url).netloc
        self.found_directories = {}
        self.dictionary_scanned = set()
        self.mode = mode
        self.exclusions = set(exclusions) if exclusions else set()
        self.session = requests.Session() # requests.Session() will manage cookies
        self.session.headers.update(HEADERS)
        self.respect_robots_txt = respect_robots_txt
        self.robots_disallowed_paths = set()
        
        self.server_info = {"Server": "Unknown", "X-Powered-By": "Unknown", "Framework_Hint": "Unknown"}
        self._headers_analyzed_for_target = False
        self.processed_js_files = set()
        self.js_discovered_api_endpoints = set()

        if session_cookies_string:
            try:
                # Parse cookie string like "name1=value1; name2=value2"
                cookies_dict = {}
                for cookie_pair in session_cookies_string.split(';'):
                    cookie_pair = cookie_pair.strip()
                    if '=' in cookie_pair:
                        name, value = cookie_pair.split('=', 1)
                        cookies_dict[name.strip()] = value.strip()
                if cookies_dict:
                    self.session.cookies.update(cookies_dict)
                    print(f"[*] 세션 쿠키 적용됨: {cookies_dict.keys()}")
            except Exception as e:
                print(f"[!] 제공된 세션 쿠키 문자열 파싱 중 오류 발생: {e}")
        
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

    def _analyze_response_headers(self, response):
        """Analyzes response headers to gather server/framework information."""
        if not self._headers_analyzed_for_target and response:
            server_header = response.headers.get('Server')
            x_powered_by_header = response.headers.get('X-Powered-By')
            cookies = response.cookies

            if server_header:
                self.server_info['Server'] = server_header
            if x_powered_by_header:
                self.server_info['X-Powered-By'] = x_powered_by_header
            
            # Basic framework hinting from headers/cookies
            if 'ASP.NET' in (server_header or '') or 'ASP.NET' in (x_powered_by_header or ''):
                self.server_info['Framework_Hint'] = 'ASP.NET'
            elif 'PHP' in (x_powered_by_header or ''):
                self.server_info['Framework_Hint'] = 'PHP'
            elif any(cookie.name.upper() == 'PHPSESSID' for cookie in cookies):
                 self.server_info['Framework_Hint'] = 'PHP (Session)'
            elif 'Express' in (x_powered_by_header or ''):
                self.server_info['Framework_Hint'] = 'Express.js (Node.js)'
            elif 'Django' in (server_header or '') or any(cookie.name == 'csrftoken' for cookie in cookies): # Django often sets csrftoken
                self.server_info['Framework_Hint'] = 'Django (Python)'
            elif 'Ruby' in (server_header or '') or 'Rails' in (x_powered_by_header or ''):
                self.server_info['Framework_Hint'] = 'Ruby on Rails'
            elif any(cookie.name.upper() == 'JSESSIONID' for cookie in cookies):
                self.server_info['Framework_Hint'] = 'Java (JSP/Servlets)'
            
            self._headers_analyzed_for_target = True
            print(f"[*] Server/Framework Info for {self.target_url}: {self.server_info}")

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
        # Check full URL (사용자가 전체 URL을 제외 목록에 넣었을 경우)
        if url in self.exclusions:
            return True
        # Check domain/IP (사용자가 도메인 자체를 제외 목록에 넣었을 경우)
        if parsed_url.netloc in self.exclusions:
            return True

        # Check for path-based exclusions from user-defined list
        # self.exclusions는 "/admin", "/user/settings"와 같은 경로 접두사를 포함할 수 있음
        current_path = parsed_url.path
        if not current_path: # 경로가 없는 경우 (예: http://example.com)
            current_path = "/" 
            
        for exclusion_pattern in self.exclusions:
            # exclusion_pattern이 '/'로 시작하는 경로 패턴인지 확인하고,
            # 현재 URL의 경로가 해당 패턴으로 시작하는지 확인
            if exclusion_pattern.startswith('/') and current_path.startswith(exclusion_pattern):
                return True
            # 만약 exclusion_pattern이 '/'로 시작하지 않는다면 (예: 'admin'),
            # 이는 의도되지 않은 사용일 수 있으므로, 여기서는 '/'로 시작하는 명확한 경로 패턴만 처리합니다.
            # 또는, 사용자가 "some/path" (슬래시로 시작하지 않음)를 입력하여
            # URL 경로 내 어디든 해당 문자열이 포함되면 제외하도록 확장할 수도 있습니다.
            # 현재는 접두사 일치만 지원합니다.

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
            # Analyze headers for the main target domain responses
            if urlparse(url).netloc == self.base_domain:
                self._analyze_response_headers(response)
            return response
        except requests.RequestException as e:
            print(f"[!] {url} 접근 중 오류 발생: {e}")
            return None

    def _extract_js_links(self, soup, page_url):
        """Extracts JavaScript file URLs from script tags."""
        js_links = set()
        if not soup:
            return list(js_links)
        for script_tag in soup.find_all("script", src=True):
            js_src = script_tag.get("src")
            if js_src and js_src.lower().endswith('.js'):
                full_js_url = urljoin(page_url, js_src)
                # Ensure it's within the same base domain and not already processed
                if urlparse(full_js_url).netloc == self.base_domain:
                    js_links.add(full_js_url)
        return list(js_links)

    def _parse_js_for_endpoints(self, js_content, page_url_where_script_was_found):
        """Parses JavaScript content for potential API endpoint paths using regex."""
        if not js_content:
            return []
        
        found_paths = set()
        # Regex patterns to find API-like paths in strings or fetch/axios calls
        # These are examples and might need refinement
        patterns = [
            r"""fetch\s*\(\s*['"]((?:[^'"\s]|\\')+)['"]""",  # fetch('/api/users')
            r"""axios\.(?:get|post|put|delete|request)\s*\(\s*['"]((?:[^'"\s]|\\')+)['"]""", # axios.get('/api/data')
            r"""['"]((?:\/[a-zA-Z0-9_.-]+)*(?:\/(api|v\d+|rest|service|data|user|auth)\S*?))['"]""", # '/api/v1/items', '/data/config'
            r"""['"](\/[a-zA-Z0-9_.-]+\/[a-zA-Z0-9_.-]+(?:[?#]\S*)?)['"]""" # General relative paths like '/path/subpath'
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, js_content):
                path = match.group(1)
                if path.startswith('http://') or path.startswith('https://') or path.startswith('//'):
                    # If it's an absolute or protocol-relative URL, check domain
                    parsed_path = urlparse(path)
                    if parsed_path.netloc and parsed_path.netloc == self.base_domain:
                        found_paths.add(urljoin(self.target_url, parsed_path.path)) # Normalize
                elif path.startswith('/'):
                    # Root-relative path
                    found_paths.add(urljoin(self.target_url, path))
                else:
                    # Potentially relative path, resolve against the page URL where script was found
                    # This is a simplification; true relative path resolution in JS can be complex
                    if not any(c in path for c in ['<', '>', '{', '}']): # Basic check to avoid HTML/template snippets
                        found_paths.add(urljoin(page_url_where_script_was_found, path))
                        
        # Filter out common non-API file extensions and very short paths
        filtered_endpoints = set()
        for p in found_paths:
            parsed_p = urlparse(p)
            # Remove query params and fragments for base endpoint scanning
            base_p_path = parsed_p.path 
            if base_p_path and not any(base_p_path.lower().endswith(ext) for ext in ['.js', '.css', '.html', '.png', '.jpg', '.gif', '.svg', '.woff', '.ttf']) and len(base_p_path) > 3:
                 # Construct full URL with scheme and netloc from target_url
                full_endpoint_url = urljoin(self.target_url, base_p_path)
                if urlparse(full_endpoint_url).netloc == self.base_domain: # Final check
                    filtered_endpoints.add(full_endpoint_url)
        
        print(f"[*] JS Parsing: Found potential API paths: {filtered_endpoints}")
        return list(filtered_endpoints)

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

    def dictionary_scan_single(self, base_url, dir_name, source='unknown'): # source 파라미터 추가
        """
        주어진 base_url과 딕셔너리 항목을 조합하여 URL을 요청한 후,
        디렉토리 리스팅 여부와 상태 코드를 확인.
        제외된 URL은 스캔하지 않음.
        API 경로는 디렉토리 리스팅 분석을 수행하지 않음.
        """
        url = f"{base_url.rstrip('/')}/{dir_name.lstrip('/')}"
        
        if self.is_excluded(url):
            print(f"[-] 딕셔 dictionaries_scan_single에서 제외된 URL (초기 확인, Source: {source}): {url}")
            return url, {
                'status_code': 'EXCLUDED',
                'content_length': 0,
                'directory_listing': False, # API 경로의 경우 항상 False
                'note': 'URL excluded by configuration or robots.txt.',
                'source': source 
            }

        response = self.fetch_url(url) 
        if response:
            status_code = response.status_code
            content_length = len(response.content)
            directory_listing = False # 기본값 False
            note = f'Scan attempted. Status: {status_code}' # 기본 노트

            if source == 'js_api':
                # API 경로는 디렉토리 리스팅 분석을 수행하지 않음
                if status_code == 200:
                    note = 'API endpoint/path responded (200).'
                elif status_code == 403:
                    note = 'API endpoint/path access denied (403).'
                elif status_code == 404:
                    note = 'API endpoint/path not found (404).'
                # 다른 상태 코드에 대한 노트는 기본값 사용
            else: # 일반 경로 스캔
                if status_code == 200:
                    directory_listing = self.analyze_directory_listing(response)
                    if directory_listing:
                        note = 'Directory listing found (200).'
                    else:
                        note = 'Path found (200).'
                elif status_code == 403:
                     note = 'Access denied (403).'
                # 다른 상태 코드에 대한 노트는 기본값 사용
            
            return url, {
                'status_code': status_code,
                'content_length': content_length,
                'directory_listing': directory_listing,
                'note': note,
                'source': source 
            }
        else:
            return url, {
                'status_code': 'NO_RESPONSE_OR_ERROR',
                'content_length': 0,
                'directory_listing': False,
                'note': 'Failed to fetch URL (request error or excluded by fetch_url).',
                'source': source 
            }

    def dictionary_scan(self, base_url, source='initial'): # source 기본값을 'initial'로 변경
        """
        주어진 base_url에 대해 딕셔너리 목록으로 디렉토리 존재 여부를 멀티스레딩으로 스캔.
        source에 따라 일반 사전 또는 API 특화 사전을 사용.
        """
        # ... (기존 dictionary_scanned 검사 로직은 유지하거나 source에 따라 조정 가능)
            
        current_dictionary = self.api_dictionary if source == 'js_api' else self.dictionary
        if not current_dictionary:
            print(f"[-] {source} 스캔을 위한 사전이 비어있습니다: {base_url}")
            return

        print(f"[+] {'API' if source == 'js_api' else '일반'} 딕셔너리 스캔 시작 (Source: {source}): {base_url} (사전 크기: {len(current_dictionary)})")
        results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_dir = {
                executor.submit(self.dictionary_scan_single, base_url, dir_name, source): dir_name
                for dir_name in current_dictionary # 현재 source에 맞는 사전 사용
            }
            for future in concurrent.futures.as_completed(future_to_dir):
                original_dir_name = future_to_dir[future]
                attempted_url = f"{base_url.rstrip('/')}/{original_dir_name.lstrip('/')}"
                try:
                    _, scan_info = future.result() 
                    results[attempted_url] = scan_info 
                except Exception as e:
                    print(f"[!] {'API ' if source == 'js_api' else ''}딕셔너리 항목 {original_dir_name} 스캔 작업 중 예외 발생 (Source: {source}): {e}")
                    results[attempted_url] = {
                        'status_code': 'SCANNER_TASK_ERROR',
                        'content_length': 0,
                        'directory_listing': False,
                        'note': f'Internal error during scan attempt for {original_dir_name}: {str(e)}',
                        'source': source 
                    }
        self.found_directories.update(results)
        if source in ['initial', 'crawl']: # API 스캔은 dictionary_scanned에 추가하지 않음 (API 베이스 경로는 여러번 스캔될 수 있음)
            self.dictionary_scanned.add(base_url)

    def crawl_recursive(self, current_url, visited, depth, max_depth):
        """
        재귀적으로 내부 링크를 방문하며 각 페이지에서 딕셔리 스캔을 진행합니다.
        제외된 URL은 크롤링하지 않습니다. 또한 JS 파일에서 API 엔드포인트를 찾아 스캔합니다.
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
        
        # 먼저 현재 크롤링된 URL 자체를 fetch하고 기록 시도
        response = self.fetch_url(current_url)
        if not response:
            # 크롤링 대상 URL 자체에 접근할 수 없으면 더 이상 진행하지 않음
            # (단, dictionary_scan은 시도해볼 수 있으나, 여기서는 접근 가능한 페이지만 추가 분석)
            # NO_RESPONSE_OR_ERROR를 기록할 수도 있지만, 일단은 반환
            return

        # 현재 크롤링된 URL 자체를 결과에 추가 (이미 다른 방식으로 발견되지 않았다면)
        if current_url not in self.found_directories:
            status_code = response.status_code
            content_length = len(response.content)
            directory_listing = False
            note = f'Crawled path. Status: {status_code}'

            if 'text/html' in response.headers.get('Content-Type', '').lower():
                directory_listing = self.analyze_directory_listing(response)

            if status_code == 200:
                note = 'Crawled path found (200).'
                if directory_listing:
                    note = 'Crawled path with directory listing found (200).'
            elif status_code == 403:
                note = 'Crawled path access denied (403).'
            
            self.found_directories[current_url] = {
                'status_code': status_code,
                'content_length': content_length,
                'directory_listing': directory_listing,
                'note': note,
                'source': 'crawl'
            }
        
        # 현재 크롤링된 URL에 대해 딕셔너리 스캔 수행
        self.dictionary_scan(current_url, source='crawl')

        # response 가 유효하므로 헤더 분석 및 내부 링크/JS 파싱 진행
        if urlparse(current_url).netloc == self.base_domain:
            self._analyze_response_headers(response)

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # --- JavaScript Link Extraction and API Endpoint Scanning ---
        if soup: 
            js_file_urls = self._extract_js_links(soup, current_url)
            for js_url in js_file_urls:
                if js_url not in self.processed_js_files: # Check if JS file itself was already processed
                    print(f"[+] JS 파일 발견 및 파싱 시도: {js_url}")
                    # Add to processed_js_files here to avoid re-fetching/re-parsing the same JS file
                    self.processed_js_files.add(js_url) 
                    js_response = self.fetch_url(js_url) 
                    if js_response and js_response.text:
                        # Call js_scan_and_evaluate_api_bases to handle API endpoints found in this JS file.
                        # js_url is the URL of the JS file itself, which acts as the 'page_url_where_script_was_found'
                        # for resolving relative paths within that JS content.
                        self.js_scan_and_evaluate_api_bases(js_response.text, js_url)
                    else:
                        print(f"[-] JS 파일 내용을 가져오지 못함: {js_url}")
        # --- End JavaScript Link Extraction ---

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
        1. 초기 target_url에 대해 딕셔너리 스캔 수행.
        2. target_url부터 재귀적 크롤링 시작.
        """
        # if self.username and self.password: # REMOVED
        #     self._attempt_login() # REMOVED

        # Attempt to fetch the main target URL to analyze its headers early
        initial_response = self.fetch_url(self.target_url)
        if initial_response:
            # 초기 타겟 URL 자체를 결과에 추가 (이미 발견되지 않았다면)
            if self.target_url not in self.found_directories:
                status_code = initial_response.status_code
                content_length = len(initial_response.content)
                directory_listing = False
                note = f'Initial target. Status: {status_code}'

                if 'text/html' in initial_response.headers.get('Content-Type', '').lower():
                    directory_listing = self.analyze_directory_listing(initial_response)

                if status_code == 200:
                    note = 'Initial target found (200).'
                    if directory_listing:
                        note = 'Initial target with directory listing found (200).'
                elif status_code == 403:
                    note = 'Initial target access denied (403).'
                
                self.found_directories[self.target_url] = {
                    'status_code': status_code,
                    'content_length': content_length,
                    'directory_listing': directory_listing,
                    'note': note,
                    'source': 'target_base' 
                }

            if not self._headers_analyzed_for_target:
                 self._analyze_response_headers(initial_response)

        # 1. 초기 target_url에 대해 딕셔너리 스캔 수행 (source='initial'은 dictionary_scan의 기본값)
        self.dictionary_scan(self.target_url, source='initial') 
        
        visited = set()
        print(f"[+] 재귀적 크롤링 시작: {self.target_url}")
        self.crawl_recursive(self.target_url, visited, depth=0, max_depth=max_depth)
        
        return {"directories": self.found_directories, "server_info": self.server_info}

    def js_scan_and_evaluate_api_bases(self, js_content, page_url):
        """
        Parses JS content for potential API paths, records the base paths if responsive,
        and then performs a dictionary scan on them.
        Uses self.js_discovered_api_endpoints to avoid redundant processing.
        page_url is the URL of the page/script where the js_content was found.
        """
        potential_api_paths = self._parse_js_for_endpoints(js_content, page_url) # Use _parse_js_for_endpoints

        if potential_api_paths:
            # This print might be redundant if _parse_js_for_endpoints already prints it.
            # Consider removing if _parse_js_for_endpoints's print is sufficient.
            # print(f"[*] js_scan_and_evaluate_api_bases: Found potential API paths: {potential_api_paths}") 
            for api_base_url in potential_api_paths:
                # Check if this api_base_url has already been processed or is excluded
                if api_base_url in self.js_discovered_api_endpoints:
                    # print(f"[*] JS API Base {api_base_url} already processed via js_discovered_api_endpoints.") # Optional log
                    continue
                if self.is_excluded(api_base_url):
                    print(f"[-] JS API Base {api_base_url} is excluded.")
                    self.js_discovered_api_endpoints.add(api_base_url) # Add to set to prevent re-check
                    continue
                
                # Add to set before processing to handle concurrent/re-entrant scenarios if any (though current model is sequential for this part)
                self.js_discovered_api_endpoints.add(api_base_url)

                print(f"[+] JS에서 API 엔드포인트 발견, 직접 확인 및 딕셔너리 스캔 시도: {api_base_url}")

                # 1. Directly fetch and record the discovered api_base_url itself
                needs_direct_check = True # Retained for clarity, though always true now after initial checks
                
                # The check `if api_base_url in self.found_directories:` and its inner logic 
                # for 'js_api_base' source can be simplified as we now control flow with js_discovered_api_endpoints.
                # We will always attempt to fetch and record if it's a new endpoint.
                # If it was already in found_directories from another source (e.g. 'crawl'), 
                # this will update/overwrite it with 'js_api_base' if found via JS.

                if needs_direct_check:
                    response = self.fetch_url(api_base_url)
                    if response:
                        status_code = response.status_code
                        if status_code in [200, 403, 401, 405, 400, 404, 500]:
                            content_length = len(response.content)
                            directory_listing = self.analyze_directory_listing(response) if 'text/html' in response.headers.get('Content-Type','').lower() else False
                            
                            note = f"JS Discovered API Base. Status: {status_code}"
                            if status_code == 200:
                                note = f"JS Discovered API Base found (200)."
                            elif status_code == 403:
                                note = f"JS Discovered API Base access denied (403)."
                            elif status_code == 401:
                                note = f"JS Discovered API Base requires authentication (401)."
                            elif status_code == 405:
                                note = f"JS Discovered API Base - Method Not Allowed (405)."
                            elif status_code == 404:
                                note = f"JS Discovered API Base - Not Found (404)."

                            self.found_directories[api_base_url] = {
                                'status_code': status_code,
                                'content_length': content_length,
                                'directory_listing': directory_listing,
                                'note': note,
                                'source': 'js_api_base'
                            }
                            print(f"[+] JS API Base Path Recorded: {api_base_url} (Status: {status_code}, Source: js_api_base)")
                
                # 2. Then, proceed with dictionary scanning against this base_url using API dictionary
                # Ensure dictionary_scan itself doesn't re-add to js_discovered_api_endpoints or have redundant checks for the base.
                # The `dictionary_scanned` set in `dictionary_scan` is for 'initial' and 'crawl' sources, so it's fine.
                self.dictionary_scan(api_base_url, source='js_api')
