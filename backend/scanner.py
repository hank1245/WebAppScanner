import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import concurrent.futures
import re
from typing import Optional, List

PROXIES = {
    'http': 'socks5h://torproxy:9050',
    'https': 'socks5h://torproxy:9050'
}

HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/110.0.0.0 Safari/537.36')
}

DEFAULT_API_DICTIONARY = [
    "",
    "users", "user", "items", "products", "orders", "cart", "auth", "login", "logout",
    "register", "profile", "settings", "config", "status", "health", "ping", "api-docs",
    "swagger", "openapi", "graphql", "v1", "v2", "v3", "test", "dev", "prod", "data",
    "metrics", "logs", "admin", "management", "payment", "search", "notifications"
]

class MultiWebScanner:
    def __init__(self, target_url, dictionary, mode='normal', exclusions=None, respect_robots_txt=True, session_cookies_string: Optional[str] = None):
        """초기화 함수: 대상 URL, 딕셔너리 목록, 모드, 제외 목록, 세션 쿠키 문자열을 입력받습니다."""
        self.target_url = target_url.rstrip('/')
        self.dictionary = dictionary
        self.api_dictionary = DEFAULT_API_DICTIONARY
        self.base_domain = urlparse(self.target_url).netloc
        self.found_directories = {}
        self.dictionary_scanned = set()
        self.mode = mode
        self.exclusions = set(exclusions) if exclusions else set()
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.respect_robots_txt = respect_robots_txt
        self.robots_disallowed_paths = set()
        
        self.server_info = {"Server": "Unknown", "X-Powered-By": "Unknown", "Framework_Hint": "Unknown"}
        self._headers_analyzed_for_target = False
        self.processed_js_files = set()
        self.js_discovered_api_endpoints = set()

        if session_cookies_string:
            try:
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
            self.session.timeout = 30
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0',
                'Accept-Language': 'en-US,en;q=0.5',
                'DNT': '1'
            })
            
        if self.respect_robots_txt:
            self._parse_robots_txt()

    def _analyze_response_headers(self, response):
        """응답 헤더를 분석하여 서버/프레임워크 정보를 수집합니다."""
        if not self._headers_analyzed_for_target and response:
            server_header = response.headers.get('Server')
            x_powered_by_header = response.headers.get('X-Powered-By')
            cookies = response.cookies

            if server_header:
                self.server_info['Server'] = server_header
            if x_powered_by_header:
                self.server_info['X-Powered-By'] = x_powered_by_header
            
            if 'ASP.NET' in (server_header or '') or 'ASP.NET' in (x_powered_by_header or ''):
                self.server_info['Framework_Hint'] = 'ASP.NET'
            elif 'PHP' in (x_powered_by_header or ''):
                self.server_info['Framework_Hint'] = 'PHP'
            elif any(cookie.name.upper() == 'PHPSESSID' for cookie in cookies):
                 self.server_info['Framework_Hint'] = 'PHP (Session)'
            elif 'Express' in (x_powered_by_header or ''):
                self.server_info['Framework_Hint'] = 'Express.js (Node.js)'
            elif 'Django' in (server_header or '') or any(cookie.name == 'csrftoken' for cookie in cookies):
                self.server_info['Framework_Hint'] = 'Django (Python)'
            elif 'Ruby' in (server_header or '') or 'Rails' in (x_powered_by_header or ''):
                self.server_info['Framework_Hint'] = 'Ruby on Rails'
            elif any(cookie.name.upper() == 'JSESSIONID' for cookie in cookies):
                self.server_info['Framework_Hint'] = 'Java (JSP/Servlets)'
            
            self._headers_analyzed_for_target = True
            print(f"[*] Server/Framework Info for {self.target_url}: {self.server_info}")

    def _parse_robots_txt(self):
        """대상 URL의 robots.txt 파일을 파싱하여 Disallow 경로를 추출."""
        parsed_url = urlparse(self.target_url)
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
        
        try:
            print(f"[+] robots.txt 확인: {robots_url}")
            timeout = 30 if self.mode == 'darkweb' else 10
            response = self.session.get(robots_url, timeout=timeout)
            if response.status_code != 200:
                print(f"[-] robots.txt가 없거나 접근할 수 없습니다: {response.status_code}")
                return
                
            lines = response.text.splitlines()
            current_user_agent = "*"
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                parts = line.split(':', 1)
                if len(parts) != 2:
                    continue
                    
                directive = parts[0].strip().lower()
                value = parts[1].strip()
                
                if directive == "user-agent":
                    current_user_agent = value
                elif directive == "disallow" and (current_user_agent == "*" or "mozilla" in current_user_agent.lower() or self.session.headers['User-Agent'] in current_user_agent):
                    if value:
                        path = value
                        disallowed_url = urljoin(f"{parsed_url.scheme}://{parsed_url.netloc}", path)
                        self.robots_disallowed_paths.add(disallowed_url)
                        print(f"[+] robots.txt Disallow 경로 추가: {disallowed_url}")
            
            print(f"[+] 총 {len(self.robots_disallowed_paths)}개의 Disallow 경로 확인됨")
        except Exception as e:
            print(f"[!] robots.txt 파싱 중 오류 발생: {e}")

    def is_disallowed_by_robots(self, url):
        """URL이 robots.txt의 Disallow 규칙에 해당하는지 확인합니다."""
        if not self.respect_robots_txt or not self.robots_disallowed_paths:
            return False
            
        for disallowed_path in self.robots_disallowed_paths:
            if url.startswith(disallowed_path):
                print(f"[robots.txt] 접근 제한된 URL: {url}")
                return True
        return False

    def is_excluded(self, url):
        """URL이 제외 목록에 있는지 또는 robots.txt에 의해 차단되는지 확인합니다."""
        parsed_url = urlparse(url)
        if url in self.exclusions:
            return True
        if parsed_url.netloc in self.exclusions:
            return True

        current_path = parsed_url.path
        if not current_path:
            current_path = "/" 
            
        for exclusion_pattern in self.exclusions:
            if exclusion_pattern.startswith('/') and current_path.startswith(exclusion_pattern):
                return True

        if self.is_disallowed_by_robots(url):
            return True
        return False

    def fetch_url(self, url, timeout=None):
        """URL에 GET 요청을 보내고, 실패 시 None을 반환합니다."""
        if self.is_excluded(url):
            print(f"[-] 제외된 URL: {url}")
            return None
        
        if timeout is None:
            timeout = 30 if self.mode == 'darkweb' else 10
            
        try:
            response = self.session.get(url, timeout=timeout)
            if urlparse(url).netloc == self.base_domain:
                self._analyze_response_headers(response)
            return response
        except requests.RequestException as e:
            print(f"[!] {url} 접근 중 오류 발생: {e}")
            return None

    def _extract_js_links(self, soup, page_url):
        """JavaScript 파일 URL을 스크립트 태그에서 추출합니다."""
        js_links = set()
        if not soup:
            return list(js_links)
        for script_tag in soup.find_all("script", src=True):
            js_src = script_tag.get("src")
            if js_src and js_src.lower().endswith('.js'):
                full_js_url = urljoin(page_url, js_src)
                if urlparse(full_js_url).netloc == self.base_domain:
                    js_links.add(full_js_url)
        return list(js_links)

    def _parse_js_for_endpoints(self, js_content, page_url_where_script_was_found):
        """정규식을 사용하여 JavaScript 내용에서 잠재적 API 엔드포인트 경로를 파싱합니다."""
        if not js_content:
            return []
        
        found_paths = set()
        patterns = [
            r"""fetch\s*\(\s*['"]((?:[^'"\s]|\\')+)['"]""",
            r"""axios\.(?:get|post|put|delete|request)\s*\(\s*['"]((?:[^'"\s]|\\')+)['"]""",
            r"""['"]((?:\/[a-zA-Z0-9_.-]+)*(?:\/(api|v\d+|rest|service|data|user|auth)\S*?))['"]""",
            r"""['"](\/[a-zA-Z0-9_.-]+\/[a-zA-Z0-9_.-]+(?:[?#]\S*)?)['"]"""
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, js_content):
                path = match.group(1)
                if path.startswith('http://') or path.startswith('https://') or path.startswith('//'):
                    parsed_path = urlparse(path)
                    if parsed_path.netloc and parsed_path.netloc == self.base_domain:
                        found_paths.add(urljoin(self.target_url, parsed_path.path))
                elif path.startswith('/'):
                    found_paths.add(urljoin(self.target_url, path))
                else:
                    if not any(c in path for c in ['<', '>', '{', '}']):
                        found_paths.add(urljoin(page_url_where_script_was_found, path))
                        
        filtered_endpoints = set()
        for p in found_paths:
            parsed_p = urlparse(p)
            base_p_path = parsed_p.path 
            if base_p_path and not any(base_p_path.lower().endswith(ext) for ext in ['.js', '.css', '.html', '.png', '.jpg', '.gif', '.svg', '.woff', '.ttf']) and len(base_p_path) > 3:
                full_endpoint_url = urljoin(self.target_url, base_p_path)
                if urlparse(full_endpoint_url).netloc == self.base_domain:
                    filtered_endpoints.add(full_endpoint_url)
        
        print(f"[*] JS Parsing: Found potential API paths: {filtered_endpoints}")
        return list(filtered_endpoints)

    def _check_directory_listing_patterns(self, text_content):
        """HTML 내용에서 디렉토리 리스팅 관련 패턴을 확인합니다."""
        patterns = [
            r"Index of /",
            r"<title>Index of .*?</title>",
            r"Parent Directory",
            r"\[To Parent Directory\]",
            r"Directory Listing For /",
            r"<h1>Index of .*?</h1>"
        ]
        for pattern in patterns:
            if re.search(pattern, text_content, re.IGNORECASE):
                return True
        return False

    def analyze_directory_listing(self, response):
        """응답을 분석하여 디렉토리 리스팅 여부를 판단합니다."""
        if not response:
            return False
        if response.status_code != 200: 
            return False

        content_type = response.headers.get('Content-Type', '').lower()
        
        if 'text/html' in content_type:
            if self._check_directory_listing_patterns(response.text):
                return True
        
        return False

    def dictionary_scan_single(self, base_url, dir_name, source='unknown'):
        """URL 요청 후 디렉토리 리스팅 여부와 상태 코드를 확인합니다."""
        url = f"{base_url.rstrip('/')}/{dir_name.lstrip('/')}"
        
        if self.is_excluded(url):
            print(f"[-] 딕셔 dictionaries_scan_single에서 제외된 URL (초기 확인, Source: {source}): {url}")
            return url, {
                'status_code': 'EXCLUDED',
                'content_length': 0,
                'directory_listing': False,
                'note': 'URL excluded by configuration or robots.txt.',
                'source': source 
            }

        response = self.fetch_url(url) 
        if response:
            status_code = response.status_code
            content_length = len(response.content)
            directory_listing = False
            note = f'Scan attempted. Status: {status_code}'

            if source == 'js_api':
                if status_code == 200:
                    note = 'API endpoint/path responded (200).'
                elif status_code == 403:
                    note = 'API endpoint/path access denied (403).'
                elif status_code == 404:
                    note = 'API endpoint/path not found (404).'
            elif source == 'js_api_base':
                if status_code == 200:
                    note = 'JS Discovered API Base found (200).'
                elif status_code == 403:
                    note = 'JS Discovered API Base access denied (403).'
                elif status_code == 401:
                    note = 'JS Discovered API Base requires authentication (401).'
                elif status_code == 405:
                    note = 'JS Discovered API Base - Method Not Allowed (405).'
                elif status_code == 404:
                    note = 'JS Discovered API Base - Not Found (404).'
            else:
                if status_code == 200:
                    directory_listing = self.analyze_directory_listing(response)
                    if directory_listing:
                        note = 'Directory listing found (200).'
                    else:
                        note = 'Path found (200).'
                elif status_code == 403:
                     note = 'Access denied (403).'
            
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

    def dictionary_scan(self, base_url, source='initial'):
        """딕셔너리 목록으로 디렉토리 존재 여부를 멀티스레딩으로 스캔합니다."""
        current_dictionary = self.api_dictionary if source == 'js_api' else self.dictionary
        if not current_dictionary:
            print(f"[-] {source} 스캔을 위한 사전이 비어있습니다: {base_url}")
            return

        print(f"[+] {'API' if source == 'js_api' else '일반'} 딕셔너리 스캔 시작 (Source: {source}): {base_url} (사전 크기: {len(current_dictionary)})")
        results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_dir = {
                executor.submit(self.dictionary_scan_single, base_url, dir_name, source): dir_name
                for dir_name in current_dictionary
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
        if source in ['initial', 'crawl']:
            self.dictionary_scanned.add(base_url)

    def crawl_recursive(self, current_url, visited, depth, max_depth):
        """재귀적으로 내부 링크를 방문하며 각 페이지에서 딕셔너리 스캔을 진행합니다."""
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
        
        response = self.fetch_url(current_url)
        if not response:
            return

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
        
        self.dictionary_scan(current_url, source='crawl')

        if urlparse(current_url).netloc == self.base_domain:
            self._analyze_response_headers(response)

        soup = BeautifulSoup(response.text, 'html.parser')
        
        if soup: 
            js_file_urls = self._extract_js_links(soup, current_url)
            for js_url in js_file_urls:
                if js_url not in self.processed_js_files:
                    self.processed_js_files.add(js_url) 
                    js_response = self.fetch_url(js_url) 
                    if js_response and js_response.text:
                        self.js_scan_and_evaluate_api_bases(js_response.text, js_url)
                    else:
                        print(f"[-] JS 파일 내용을 가져오지 못함: {js_url}")

        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            full_url = urljoin(current_url, href)
            parsed_full_url = urlparse(full_url)
            
            if parsed_full_url.netloc != self.base_domain or parsed_full_url.scheme not in ['http', 'https']:
                continue
            
            if full_url in visited or self.is_excluded(full_url):
                continue
                
            links.append(full_url)

        for link in links:
            if link not in visited: 
                self.crawl_recursive(link, visited, depth + 1, max_depth)

    def report(self):
        print("\n[+] 스캔 결과 보고:")
        if not self.found_directories:
            print("[-] 발견된 디렉토리 없음.")
            return
            
        for url, info in self.found_directories.items():
            if info:
                print(f"URL: {url}")
                print(f"  Status: {info['status_code']}, Length: {info['content_length']}")
                if info['directory_listing']:
                    print(f"  Directory Listing: Enabled (잠재적 노출)")
                else:
                    print(f"  Directory Listing: Disabled or Not Detected")

    def run(self, max_depth=2):
        """스캔 실행 함수."""
        initial_response = self.fetch_url(self.target_url)
        if initial_response:
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

        self.dictionary_scan(self.target_url, source='initial') 
        
        visited = set()
        print(f"[+] 재귀적 크롤링 시작: {self.target_url}")
        self.crawl_recursive(self.target_url, visited, depth=0, max_depth=max_depth)
        
        return {"directories": self.found_directories, "server_info": self.server_info}

    def js_scan_and_evaluate_api_bases(self, js_content, page_url):
        """JavaScript 내용에서 API 경로를 파싱하고 발견된 경로를 스캔합니다."""
        potential_api_paths = self._parse_js_for_endpoints(js_content, page_url)

        if potential_api_paths:
            for api_base_url in potential_api_paths:
                if api_base_url in self.js_discovered_api_endpoints:
                    continue
                if self.is_excluded(api_base_url):
                    print(f"[-] JS API Base {api_base_url} is excluded.")
                    self.js_discovered_api_endpoints.add(api_base_url)
                    continue
                
                self.js_discovered_api_endpoints.add(api_base_url)

                print(f"[+] JS에서 API 엔드포인트 발견, 직접 확인 및 딕셔너리 스캔 시도: {api_base_url}")

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
                
                self.dictionary_scan(api_base_url, source='js_api')
