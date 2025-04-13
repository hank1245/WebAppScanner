import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import concurrent.futures
import re
import logging
import argparse
import sys
from typing import List, Dict, Optional, Tuple, Set
from collections import deque # 재귀 대신 큐를 사용한 반복적 BFS 방식 사용

# --- 로깅 설정 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- TOR 프록시 및 헤더 ---
PROXIES = {
    'http': 'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050'
}
HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/110.0.0.0 Safari/537.36')
}

class WebScanner:
    """
    웹사이트(일반 웹 또는 다크웹)를 스캔하여 정보를 수집하고 디렉토리 리스팅 취약점을 찾는 클래스.
    재귀적 크롤링과 깊이 제한 기능을 지원합니다.
    """
    def __init__(self, target_url: str, max_depth: int = 1, use_tor: bool = False, dictionary_path: Optional[str] = None, max_workers: int = 10, timeout: int = 15):
        """
        스캐너 초기화

        Args:
            target_url (str): 스캔 시작 URL (http/https).
            max_depth (int): 크롤링 최대 깊이 (0: 시작 URL만, 1: 시작 URL + 링크된 페이지 등).
            use_tor (bool): Tor 프록시 사용 여부.
            dictionary_path (Optional[str]): 디렉토리 목록 파일 경로.
            max_workers (int): 동시 스캔 스레드 수 (딕셔너리 스캔용).
            timeout (int): 개별 요청 타임아웃 (초).
        """
        self.use_tor = use_tor
        if not self._is_valid_url(target_url):
            logging.error(f"잘못된 URL 형식입니다: {target_url}")
            raise ValueError("유효한 URL (http:// 또는 https://)을 입력해주세요.")

        if target_url.endswith('.onion') and not self.use_tor:
            logging.warning(".onion 주소는 Tor 사용이 필요합니다. --use-tor 옵션을 활성화합니다.")
            self.use_tor = True

        self.target_url = target_url.rstrip('/')
        self.max_depth = max_depth
        self.dictionary = self._load_dictionary(dictionary_path)
        self.base_domain = urlparse(self.target_url).netloc
        self.session = self._create_session()
        self.max_workers = max_workers
        self.timeout = timeout

        # 크롤링 상태 관리
        self.visited_urls: Set[str] = set()
        self.crawl_results: Dict[str, Dict] = {} # 크롤링으로 발견된 유효 페이지 정보 저장 {'url': {'status': ..., 'content_type': ...}}

        # 딕셔너리 스캔 결과
        self.found_directories: Dict[str, Optional[Dict]] = {}

        # 프레임워크 정보 (초기 페이지 기준)
        self.framework: Optional[str] = None

        logging.info(f"대상 URL: {self.target_url}")
        logging.info(f"최대 크롤링 깊이: {self.max_depth}")
        logging.info(f"Tor 사용: {'활성화' if self.use_tor else '비활성화'}")
        logging.info(f"딕셔너리 크기: {len(self.dictionary)} 개")
        logging.info(f"최대 워커 수: {self.max_workers}")
        logging.info(f"타임아웃: {self.timeout} 초")

    # --- 초기화 및 헬퍼 메서드들 (_is_valid_url, _create_session, _load_dictionary) ---
    # (이전 코드와 동일 - 생략)
    def _is_valid_url(self, url: str) -> bool:
        """ URL 형식이 유효한지 (http/https 스키마, netloc 존재) 확인 """
        try:
            parsed = urlparse(url)
            is_standard_url = parsed.scheme in ('http', 'https') and bool(parsed.netloc)
            is_onion = parsed.netloc.endswith('.onion')

            if self.use_tor:
                 return is_standard_url
            else:
                 return is_standard_url and not is_onion
        except Exception:
            return False

    def _create_session(self) -> requests.Session:
        """ requests 세션 생성. use_tor 설정에 따라 프록시를 적용. """
        session = requests.Session()
        session.headers.update(HEADERS)
        if self.use_tor:
            session.proxies = PROXIES
            try:
                logging.debug("Tor 프록시 연결 테스트 중...")
                test_url = "https://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion"
                response = session.get(test_url, timeout=self.timeout)
                response.raise_for_status()
                logging.info("Tor 프록시 연결 확인 완료.")
            except requests.exceptions.RequestException as e:
                logging.error(f"Tor 프록시 연결 실패: {e}")
                raise ConnectionError("Tor 프록시 연결 실패") from e
        else:
            try:
                logging.debug("일반 웹 연결 테스트 중 (google.com)...")
                response = session.get("https://www.google.com", timeout=self.timeout / 2)
                response.raise_for_status()
                logging.info("일반 웹 연결 확인 완료.")
            except requests.exceptions.RequestException as e:
                logging.warning(f"기본 웹 연결 테스트 실패: {e}")
        return session

    def _load_dictionary(self, dictionary_path: Optional[str]) -> List[str]:
        """ 파일 또는 기본 목록에서 디렉토리 딕셔너리를 로드 """
        if dictionary_path:
            try:
                with open(dictionary_path, 'r', encoding='utf-8', errors='ignore') as f:
                    items = {line.strip() for line in f if line.strip() and not line.startswith('#')}
                    logging.info(f"'{dictionary_path}' 에서 {len(items)}개의 항목 로드 완료.")
                    return sorted(list(items))
            except FileNotFoundError:
                logging.error(f"딕셔너리 파일을 찾을 수 없습니다: {dictionary_path}")
                sys.exit(1)
            except Exception as e:
                logging.error(f"딕셔너리 파일 로드 중 오류 발생: {e}")
                sys.exit(1)
        else:
            logging.warning("딕셔너리 파일 경로가 제공되지 않아 기본 목록을 사용합니다.")
            return ["admin", "backup", "config", "logs", "test", "phpmyadmin", "wp-admin", "wp-content", "uploads", ".git", ".env"] # 기본 목록 축소


    def fetch_url(self, url: str) -> Optional[requests.Response]:
        """ 주어진 URL에 GET 요청. 실패 시 None 반환. (이전 코드와 동일) """
        try:
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            logging.debug(f"요청: {url} -> 상태: {response.status_code}, 최종 URL: {response.url}")
            return response
        except requests.exceptions.Timeout:
            logging.warning(f"[!] 타임아웃 ({self.timeout}초 초과): {url}")
            return None
        except requests.exceptions.TooManyRedirects:
            logging.warning(f"[!] 리다이렉션 너무 많음: {url}")
            return None
        except requests.exceptions.SSLError as e:
            logging.warning(f"[!] SSL 오류: {url} ({e})")
            return None
        except requests.exceptions.ConnectionError as e:
            net_type = "Tor" if self.use_tor else "네트워크"
            logging.warning(f"[!] {net_type} 연결 오류: {url} ({e})")
            return None
        except requests.exceptions.RequestException as e:
            logging.warning(f"[!] 요청 오류: {url} ({e})")
            return None

    def _process_page(self, url: str) -> Tuple[List[str], Optional[requests.Response]]:
        """
        단일 URL을 처리(fetch, parse)하고 내부 링크 목록과 응답 객체를 반환합니다.
        (기존 crawl 메서드의 역할 수행)
        """
        logging.debug(f"페이지 처리 중: {url}")
        response = self.fetch_url(url)
        internal_links_found: Set[str] = set()

        if response:
             # 크롤링 결과 저장 (성공/실패 여부와 관계없이 상태 기록)
             self.crawl_results[url] = {
                 'status_code': response.status_code,
                 'content_type': response.headers.get('Content-Type', 'N/A'),
                 'final_url': response.url
             }

             # 성공적이고 HTML 콘텐츠인 경우만 링크 추출
             if response.status_code == 200 and 'text/html' in response.headers.get('Content-Type', '').lower():
                 html = response.text
                 soup = BeautifulSoup(html, 'html.parser')
                 current_url = response.url # 리다이렉션 고려

                 for tag in soup.find_all(['a', 'link', 'script', 'img'], href=True) + soup.find_all(['script', 'img'], src=True):
                     attr = 'href' if tag.has_attr('href') else 'src'
                     raw_link = tag[attr].strip()

                     if not raw_link or raw_link.startswith('#') or raw_link.lower().startswith(('javascript:', 'mailto:', 'tel:')):
                         continue

                     try:
                         full_url = urljoin(current_url, raw_link)
                         parsed_full_url = urlparse(full_url)

                         # 유효한 스키마이고 동일 base 도메인인 링크만 추출
                         if (parsed_full_url.scheme in ('http', 'https') and
                             parsed_full_url.netloc == self.base_domain):
                             # URL 정규화 (fragment 제거 등)
                             normalized_url = urljoin(full_url, urlparse(full_url).path) # path까지만 사용
                             if '?' in full_url: # 쿼리 스트링 포함 시 추가 (선택적)
                                 normalized_url += '?' + urlparse(full_url).query
                             internal_links_found.add(normalized_url)

                     except ValueError as e:
                         logging.debug(f"잘못된 링크 형식 ({raw_link}): {e}")
                         continue

                 logging.debug(f"{url} 에서 {len(internal_links_found)}개의 내부 링크 추출.")
                 return sorted(list(internal_links_found)), response
             else:
                 # HTML 아니거나 상태 코드 200 아닌 경우
                 return [], response # 링크 목록은 비어있지만 응답 객체는 반환
        else:
             # Fetch 실패 시
             self.crawl_results[url] = {'status_code': None, 'content_type': None, 'final_url': url} # 실패 기록
             return [], None # 링크와 응답 모두 없음

    def start_recursive_crawl(self):
        """
        시작 URL부터 최대 깊이까지 재귀적(반복적 BFS)으로 웹사이트를 크롤링합니다.
        """
        logging.info(f"[+] 최대 깊이 {self.max_depth}까지 재귀적 크롤링 시작...")
        if self.max_depth < 0:
            logging.warning("최대 깊이는 0 이상이어야 합니다. 크롤링을 수행하지 않습니다.")
            return

        # (URL, 현재 깊이) 를 저장하는 큐
        queue = deque([(self.target_url, 0)])
        self.visited_urls.clear() # 새 크롤링 시작 시 초기화
        self.crawl_results.clear()

        # 초기 페이지 프레임워크 분석용 응답 저장 변수
        initial_response = None

        while queue:
            current_url, current_depth = queue.popleft()

            # 이미 방문했으면 건너뛰기
            if current_url in self.visited_urls:
                logging.debug(f"이미 방문: {current_url}")
                continue

            # 최대 깊이 도달 시 건너뛰기 (링크 추출 안 함)
            if current_depth > self.max_depth:
                logging.debug(f"최대 깊이 도달 ({current_depth} > {self.max_depth}): {current_url}")
                continue

            # 방문 처리
            self.visited_urls.add(current_url)
            logging.info(f"크롤링 중 (깊이 {current_depth}): {current_url}")

            # 페이지 처리 및 링크 추출
            extracted_links, response = self._process_page(current_url)

            # 시작 URL의 응답 저장 (프레임워크 분석용)
            if current_depth == 0:
                 initial_response = response

            # 추출된 링크들을 큐에 추가 (다음 깊이로)
            if extracted_links and current_depth < self.max_depth:
                 next_depth = current_depth + 1
                 for link in extracted_links:
                     if link not in self.visited_urls: # 아직 방문 안 했고 큐에도 없는 링크만 추가
                         # 큐에 추가 전 최대 깊이 한 번 더 체크 (불필요할 수 있으나 안전장치)
                         if next_depth <= self.max_depth:
                              queue.append((link, next_depth))
                         else:
                              logging.debug(f"다음 깊이({next_depth})가 최대 깊이({self.max_depth}) 초과, 큐 추가 안함: {link}")

            # 부하 감소를 위한 짧은 지연 (선택적)
            # import time
            # time.sleep(0.1)

        logging.info(f"[+] 재귀적 크롤링 완료. 총 {len(self.visited_urls)}개의 URL 방문.")

        # 초기 페이지 응답 기반으로 프레임워크 분석 수행
        if initial_response:
             # _process_page에서 반환된 링크는 현재 사용 안함 (필요시 활용)
             # initial_links, _ = self._process_page(self.target_url) # 다시 호출할 필요 없음
             # 최초 크롤링 시 추출된 링크는 이미 큐 처리됨
             self.analyze_framework(initial_response, list(self.crawl_results.keys())) # 전체 방문 URL 목록 전달? 또는 초기 링크만?
        else:
             logging.error("시작 URL을 처리하지 못해 프레임워크 분석 불가.")


    # --- 분석 및 스캔 메서드들 (analyze_framework, _check_directory_listing, dictionary_scan_single, dictionary_scan) ---
    # (이전 코드와 거의 동일, analyze_framework의 links 인자 활용 부분만 약간 수정 가능성 있음)
    def analyze_framework(self, response: Optional[requests.Response], links: List[str]) -> Optional[str]:
        """ HTTP 헤더, HTML 내용, 발견된 링크를 분석하여 웹 기술 추론. (이전 코드와 유사) """
        if not response:
            logging.warning("[-] 응답 객체가 없어 프레임워크 분석 불가")
            return None

        frameworks_hints: Dict[str, int] = {'PHP': 0, 'ASP.NET': 0, 'JSP/Java': 0, 'Python': 0, 'Ruby': 0, 'Node.js': 0, 'CMS': 0}
        detected_by: Dict[str, Set[str]] = {fw: set() for fw in frameworks_hints}
        headers = response.headers
        server = headers.get('Server', '').lower()
        x_powered_by = headers.get('X-Powered-By', '').lower()
        cookies = headers.get('Set-Cookie', '').lower()
        content = response.text.lower() if response.text and isinstance(response.text, str) else ''
        # links 인자는 크롤링된 전체 URL 목록이나 초기 링크 목록 사용 가능
        all_urls = " ".join(links).lower()
        all_text = content + all_urls

        def add_hint(fw, score, reason):
            frameworks_hints[fw] += score
            detected_by[fw].add(reason)

        # 헤더 분석
        if 'php' in x_powered_by or 'php' in server: add_hint('PHP', 2, "Header(X-Powered-By/Server)")
        if 'asp.net' in x_powered_by or 'asp.net' in server or 'iis' in server: add_hint('ASP.NET', 2, "Header(X-Powered-By/Server/IIS)")
        if 'jsp' in x_powered_by or 'servlet' in server or any(s in server for s in ['tomcat', 'jboss', 'jetty', 'websphere', 'weblogic']): add_hint('JSP/Java', 2, "Header(X-Powered-By/Server/Java EE)")
        if 'python' in server: add_hint('Python', 1, "Header(Server: Python)")
        if 'passenger' in server or 'rails' in x_powered_by or 'rack' in x_powered_by: add_hint('Ruby', 2, "Header(Server/X-Powered-By: Ruby)")
        if 'express' in x_powered_by or 'node.js' in server: add_hint('Node.js', 2, "Header(X-Powered-By/Server: Node)")
        # 쿠키 분석
        if 'phpsessid' in cookies: add_hint('PHP', 1, "Cookie(PHPSESSID)")
        if 'asp.net_sessionid' in cookies: add_hint('ASP.NET', 1, "Cookie(ASP.NET_SESSIONID)")
        if 'jsessionid' in cookies: add_hint('JSP/Java', 1, "Cookie(JSESSIONID)")
        # 링크 및 내용 분석
        if '.php' in all_text: add_hint('PHP', 1, "URL/Content(.php)")
        if '.asp' in all_text or '.aspx' in all_text: add_hint('ASP.NET', 1, "URL/Content(.asp/.aspx)")
        if '.jsp' in all_text or '.do' in all_text or '.action' in all_text: add_hint('JSP/Java', 1, "URL/Content(.jsp/.do/.action)")
        # CMS/프레임워크 특정 요소
        if '<meta name="generator" content="WordPress' in content: add_hint('CMS', 3, "Meta(WordPress Generator)")
        if '<meta name="generator" content="Joomla!' in content: add_hint('CMS', 3, "Meta(Joomla Generator)")
        if 'Drupal.settings' in content: add_hint('CMS', 3, "JS(Drupal Settings)")
        if '/wp-content/' in all_urls or '/wp-includes/' in all_urls: add_hint('CMS', 2, "URL(WordPress Path)")

        # 결과 결정
        positive_hints = {fw: score for fw, score in frameworks_hints.items() if score > 0}
        if not positive_hints:
             logging.info("[-] 웹 기술 추정 불가 (단서 부족)")
             return None
        likely_framework = max(positive_hints, key=positive_hints.get)
        top_score = positive_hints[likely_framework]
        if frameworks_hints['CMS'] == top_score and top_score > 0: likely_framework = 'CMS'
        reasons = ', '.join(sorted(list(detected_by[likely_framework])))
        logging.info(f"[+] 웹 기술 추정 (초기 페이지 기준): {likely_framework} (점수: {top_score}, 근거: {reasons})")
        self.framework = likely_framework
        return likely_framework

    def _check_directory_listing(self, response: requests.Response) -> bool:
        """ 응답 내용에서 디렉토리 리스팅 패턴 확인. (이전 코드와 동일) """
        if response.status_code != 200 or not response.text or 'text/html' not in response.headers.get('Content-Type', '').lower():
            return False
        content = response.text.lower()
        patterns = [r"<title>index of /.*?</title>", r"<h1>index of /.*?</h1>", r"\bparent directory\b", r"\[to parent directory\]", r"directory listing for /"]
        for pattern in patterns:
            if re.search(pattern, content): return True
        return False

    def dictionary_scan_single(self, dir_name: str) -> Tuple[str, Optional[Dict]]:
        """ 단일 디렉토리/파일 경로 스캔. (이전 코드와 동일) """
        url = f"{self.target_url}/{dir_name.lstrip('/')}"
        response = self.fetch_url(url)
        if response:
            status_code = response.status_code
            content_length_header = response.headers.get('Content-Length')
            content_length = int(content_length_header) if content_length_header and content_length_header.isdigit() else len(response.content)
            directory_listing = self._check_directory_listing(response)
            log_level = logging.DEBUG; msg_prefix = ""
            if status_code == 200:
                log_level = logging.INFO
                if directory_listing: log_level = logging.WARNING; msg_prefix = "[리스팅 발견!] "
            elif 300 <= status_code < 400: log_level = logging.INFO
            elif status_code == 403: log_level = logging.WARNING; msg_prefix = "[접근 금지] "
            elif status_code in [401, 407]: log_level = logging.WARNING; msg_prefix = "[인증 필요] "
            elif status_code == 404: log_level = logging.DEBUG
            elif status_code >= 500: log_level = logging.ERROR; msg_prefix = "[서버 오류] "
            else: log_level = logging.WARNING
            logging.log(log_level, f"  -> {msg_prefix}딕셔너리 스캔: {url} - 상태: {status_code}, 길이: {content_length}")
            # 404 제외하고 결과 반환 (요청 성공 건)
            if status_code != 404:
                return url, {'status_code': status_code, 'content_length': content_length, 'directory_listing': directory_listing, 'final_url': response.url}
            else:
                return url, None # 404는 None 반환
        else:
            logging.debug(f"  -> 딕셔너리 스캔 실패: {url} (응답 없음 또는 오류)")
            return url, None

    def dictionary_scan(self):
        """ 딕셔너리 기반 병렬 스캔. (이전 코드와 동일, 진행률 표시 부분 수정) """
        if not self.dictionary:
            logging.warning("[-] 스캔할 딕셔너리 목록이 비어 있습니다.")
            return
        logging.info(f"[+] {len(self.dictionary)}개 항목 딕셔너리 스캔 시작 (워커: {self.max_workers})...")
        self.found_directories = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_dir = {executor.submit(self.dictionary_scan_single, dir_name): dir_name for dir_name in self.dictionary}
            processed_count = 0
            total_count = len(self.dictionary)
            for future in concurrent.futures.as_completed(future_to_dir):
                dir_name = future_to_dir[future]
                processed_count += 1
                try:
                    url, result = future.result()
                    if result: self.found_directories[url] = result
                except Exception as e:
                    logging.error(f"[!] 항목 '{dir_name}' 처리 중 오류: {e}", exc_info=False)
                # 진행률 표시
                if processed_count % 50 == 0 or processed_count == total_count:
                     progress = processed_count / total_count
                     bar = '#' * int(progress * 20) + '-' * (20 - int(progress * 20))
                     # 터미널 환경에서 같은 줄에 업데이트
                     try:
                       terminal_width = os.get_terminal_size().columns
                       line = f"\r    진행률: [{bar}] {processed_count}/{total_count} ({progress:.1%})"
                       sys.stdout.write(line.ljust(terminal_width)[:terminal_width]) # 화면 너비에 맞게 채움
                     except OSError: # 터미널 크기 못 얻는 경우 (e.g., 파일 리디렉션)
                       sys.stdout.write(f"\r    진행률: {processed_count}/{total_count} ({progress:.1%})")
                     sys.stdout.flush()

        try: # 진행률 표시 후 줄바꿈 (터미널 환경 아닐 수도 있으므로 try-except)
          print()
        except OSError:
          pass
        logging.info("[+] 딕셔너리 스캔 완료.")


    def report(self, output_file: Optional[str] = None):
        """
        스캔 결과를 요약하여 출력하고, 선택적으로 파일에 저장합니다.
        크롤링 결과(유효 페이지)도 포함합니다.
        """
        print("\n" + "="*60)
        print(" 스캔 결과 보고서")
        print("="*60)

        report_lines = []
        report_lines.append(f"스캔 대상: {self.target_url}")
        report_lines.append(f"Tor 사용: {'예' if self.use_tor else '아니오'}")
        report_lines.append(f"최대 크롤링 깊이: {self.max_depth}")
        if self.framework:
            report_lines.append(f"추정 기술 (초기 페이지 기준): {self.framework}")
            print(f"추정 기술 (초기 페이지 기준): {self.framework}")
        else:
            report_lines.append("추정 기술: 탐지 실패")
            print("추정 기술: 탐지 실패")

        # --- 크롤링 결과 보고 ---
        print(f"\n--- 크롤링 결과 ({len(self.visited_urls)}개 URL 방문) ---")
        report_lines.append(f"\n--- 크롤링 결과 ({len(self.visited_urls)}개 URL 방문) ---")
        crawled_ok_pages = {url: info for url, info in self.crawl_results.items() if info.get('status_code') == 200}
        crawled_other_pages = {url: info for url, info in self.crawl_results.items() if info.get('status_code') != 200 and info.get('status_code') is not None}
        crawled_failed = {url: info for url, info in self.crawl_results.items() if info.get('status_code') is None}

        print(f"[+] 성공적으로 접근한 페이지 ({len(crawled_ok_pages)}개):")
        report_lines.append(f"[+] 성공적으로 접근한 페이지 ({len(crawled_ok_pages)}개):")
        if crawled_ok_pages:
            for url, info in sorted(crawled_ok_pages.items()):
                line = f"  - {url} (Type: {info.get('content_type', 'N/A')})"
                line += f" -> 최종 URL: {info['final_url']}" if url != info['final_url'] else ""
                print(line)
                report_lines.append(line)
        else:
            print("  없음")
            report_lines.append("  없음")

        if crawled_other_pages:
            print(f"\n[!] 기타 상태 코드 페이지 ({len(crawled_other_pages)}개):")
            report_lines.append(f"\n[!] 기타 상태 코드 페이지 ({len(crawled_other_pages)}개):")
            for url, info in sorted(crawled_other_pages.items()):
                line = f"  - {url} (Status: {info['status_code']}, Type: {info.get('content_type', 'N/A')})"
                line += f" -> 최종 URL: {info['final_url']}" if url != info['final_url'] else ""
                print(line)
                report_lines.append(line)

        if crawled_failed:
             print(f"\n[-] 접근 실패 URL ({len(crawled_failed)}개):")
             report_lines.append(f"\n[-] 접근 실패 URL ({len(crawled_failed)}개):")
             for url, info in sorted(crawled_failed.items()):
                 print(f"  - {url}")
                 report_lines.append(f"  - {url}")


        # --- 딕셔너리 스캔 결과 보고 ---
        print(f"\n--- 딕셔너리 스캔 결과 ({len(self.found_directories)}개 유효 경로/파일 발견) ---")
        report_lines.append(f"\n--- 딕셔너리 스캔 결과 ({len(self.found_directories)}개 유효 경로/파일 발견) ---")

        results_by_status: Dict[int, List[Tuple[str, Dict]]] = {}
        for url, info in self.found_directories.items():
             if info: status = info['status_code']; results_by_status.setdefault(status, []).append((url, info))

        priority_order = [200, 403, 401, 407] + list(range(500, 600))
        sorted_statuses = sorted(results_by_status.keys(), key=lambda s: (s not in priority_order, priority_order.index(s) if s in priority_order else s))

        if not self.found_directories:
             no_result_msg = "  발견된 유효 경로/파일 없음 (404 제외)"
             print(no_result_msg)
             report_lines.append(no_result_msg)

        for status in sorted_statuses:
             status_results = sorted(results_by_status[status], key=lambda item: item[0])
             status_header = f"\n[+] 상태 코드: {status} ({len(status_results)}개)"
             print(status_header)
             report_lines.append(status_header)
             for req_url, info in status_results:
                 listing_str = " [리스팅 발견!]" if info['directory_listing'] else ""
                 length_str = f"(길이: {info['content_length']})"
                 final_url_str = f" -> 최종 URL: {info['final_url']}" if req_url != info['final_url'] else ""
                 line = f"  - {req_url} {length_str}{listing_str}{final_url_str}"
                 print(line)
                 report_lines.append(line)

        print("="*60)

        # 파일 저장
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write("\n".join(report_lines))
                logging.info(f"[+] 스캔 결과가 '{output_file}' 파일에 저장되었습니다.")
            except Exception as e:
                logging.error(f"[-] 결과를 파일에 저장하는 중 오류 발생: {e}")

# --- main 함수 ---
import os # 터미널 크기 얻기 위해 추가

def main():
    parser = argparse.ArgumentParser(description="웹사이트 스캐너 (재귀적 크롤링 지원)",
                                     epilog="주의: 반드시 허가된 대상에 대해서만 윤리적으로 사용하십시오.")
    parser.add_argument("target_url", help="스캔 시작 URL (예: https://example.com 또는 http://onionaddr.onion)")
    parser.add_argument("--max-depth", type=int, default=1, help="크롤링 최대 깊이 (0: 시작 URL만, 1: 시작 URL + 링크된 페이지 등, 기본값: 1)")
    parser.add_argument("--use-tor", action="store_true", help="Tor 프록시(127.0.0.1:9050) 사용")
    parser.add_argument("-d", "--dictionary", help="사용할 디렉토리/파일 목록 파일 경로", default=None)
    parser.add_argument("-w", "--workers", type=int, default=10, help="동시 딕셔너리 스캔 스레드 수 (기본값: 10)")
    parser.add_argument("-t", "--timeout", type=int, default=20, help="각 요청 타임아웃 (초, 기본값: 20)")
    parser.add_argument("-o", "--output", help="스캔 결과를 저장할 파일 이름", default=None)
    parser.add_argument("-v", "--verbose", action="store_true", help="상세 로깅 출력 (DEBUG 레벨)")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.debug("상세 로깅(DEBUG) 활성화됨.")

    # 윤리적 사용 경고 (이전과 동일)
    print("*" * 70)
    print(" 경고: 이 도구는 교육 및 합법적인 보안 테스트 목적으로만 사용해야 합니다. ")
    print("       허가 없이 시스템을 스캔하는 것은 불법이며 비윤리적입니다.        ")
    print("       테스트 전 반드시 대상 시스템 소유주의 명시적인 서면 동의를 받으십시오. ")
    if args.use_tor: print("       Tor 사용 시에도 완전한 익명성이 보장되지 않을 수 있습니다.        ")
    print("*" * 70)

    try:
        # max_depth 인자 전달
        scanner = WebScanner(args.target_url, args.max_depth, args.use_tor, args.dictionary, args.workers, args.timeout)

        # 1. 재귀적 크롤링 수행 (내부에서 초기 페이지 분석 포함)
        scanner.start_recursive_crawl()

        # 2. 딕셔너리 스캔 수행 (크롤링 후)
        scanner.dictionary_scan()

        # 3. 결과 보고 (크롤링 결과 + 딕셔너리 스캔 결과)
        scanner.report(args.output)

    except ValueError as e:
        logging.error(f"입력 또는 설정 오류: {e}")
        sys.exit(1)
    except ConnectionError as e:
        sys.exit(1)
    except KeyboardInterrupt:
        print()
        logging.info("\n[!] 사용자에 의해 스캔이 중단되었습니다.")
        sys.exit(0)
    except Exception as e:
        logging.exception(f"예상치 못한 심각한 오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
주요 변경 및 개선 사항:

argparse 사용:

명령줄에서 target_url, dictionary 파일 경로, workers 수, timeout, output 파일, skip-scan 옵션, verbose 로깅을 지정할 수 있습니다.
사용법: python your_script_name.py http://youronionaddress.onion -d common_dirs.txt -w 15 -o report.txt
로깅 개선 (logging 모듈):

print 대신 logging을 사용하여 정보, 경고, 오류 등을 체계적으로 기록합니다.
-v 또는 --verbose 옵션으로 DEBUG 레벨 로그(예: 404 응답)까지 볼 수 있습니다.
Tor 연결 상태, 스캔 진행률 등을 로깅합니다.
Tor 연결 확인:

__init__에서 세션을 만들 때 간단한 Tor 연결 테스트를 시도하고 실패 시 프로그램을 시작하지 않고 종료합니다.
딕셔너리 파일 로드:

-d 옵션으로 딕셔너리 파일을 지정할 수 있습니다.
파일을 읽어 중복 및 주석/공백 줄을 제거합니다.
파일이 제공되지 않으면 내장된 기본 목록을 사용하고 경고를 표시합니다.
프레임워크 탐지 강화:

X-Powered-By, Server 헤더뿐만 아니라 Set-Cookie 헤더의 세션 ID 패턴(PHPSESSID, ASP.NET_SESSIONID, JSESSIONID)도 확인합니다.
크롤링된 링크와 HTML 내용에서 .php, .asp, .aspx, .jsp, .do 등의 확장자를 검사합니다.
단서별로 점수를 매겨 가장 가능성 높은 프레임워크를 추론합니다.
디렉토리 리스팅 탐지 강화:

Index of / 외에 <title>Index of /...</title>, Parent Directory 같은 패턴도 검사합니다.
오류 처리 및 안정성:

Workspace_url에서 Timeout, TooManyRedirects, ConnectionError 등 구체적인 예외를 처리하고 경고 로그를 남깁니다.
dictionary_scan_single에서 상태 코드에 따라 로그 레벨을 다르게 하여 중요한 정보(200, 403, 리스팅 발견)를 강조하고 덜 중요한 정보(404)는 DEBUG 레벨로 처리합니다.
유효하지 않은 .onion URL 입력 시 시작 단계에서 오류를 발생시킵니다.
KeyboardInterrupt (Ctrl+C) 처리하여 깔끔하게 종료합니다.
전체 try...except 블록으로 예상치 못한 오류 발생 시 스택 트레이스와 함께 로깅합니다.
크롤링 개선:

urljoin을 사용하여 상대 경로와 절대 경로를 올바르게 처리합니다.
링크 필터링: javascript:, #fragment 등을 제외하고, http/https 스키마를 사용하며, 동일 도메인 내의 링크만 수집합니다.
crawled_links 세트를 사용하여 중복 방문을 방지합니다 (현재는 1단계 크롤링만).
보고서 개선:

상태 코드별로 결과를 그룹화하고 정렬하여 보여줍니다.
디렉토리 리스팅이 발견된 경우 강조 표시([리스팅 발견!])합니다.
-o 옵션으로 결과를 파일에 저장할 수 있습니다.
코드 구조 및 가독성:

타입 힌트(typing 모듈)를 추가하여 코드 이해도와 유지보수성을 높였습니다.
메서드와 클래스에 대한 Docstring을 보강했습니다.
윤리적 사용에 대한 경고 메시지를 강화하고 시작 시 출력합니다.
추가 고려 사항 및 향후 개선점:

재귀적 크롤링: 현재는 시작 페이지만 크롤링합니다. 발견된 내부 링크를 계속 따라가는 재귀적 크롤링 기능을 추가할 수 있지만, 스캔 범위와 깊이를 제어하는 로직(예: 최대 깊이 설정, URL 패턴 필터링)이 필수적입니다. 잘못하면 스캔이 끝나지 않거나 너무 광범위해질 수 있습니다.
더 정교한 프레임워크/CMS 탐지: Wappalyzer와 유사하게 JavaScript 변수, 특정 파일 경로 존재 여부, HTML 주석 등을 분석하여 더 정확하게 기술 스택을 식별할 수 있습니다.
취약점 스캔 확장: 디렉토리 리스팅 외에 다른 일반적인 웹 취약점(예: 설정 파일 노출, SQL 인젝션 파라미터 패턴 등) 스캔 기능을 추가할 수 있습니다. (매우 주의 필요)
Tor 회로 교체: 장시간 스캔 시 주기적으로 Tor 회로를 교체하는 기능을 추가하여 IP 추적 가능성을 더 낮출 수 있습니다 (Tor 컨트롤 포트와 stem 라이브러리 필요).
결과 저장 형식: 단순 텍스트 외에 JSON이나 CSV 형식으로 결과를 저장하는 옵션을 추가할 수 있습니다.
이 개선된 코드는 기존 기능은 유지하면서 안정성, 유연성, 정보력을 높이는 데 중점을 두었습니다. 사용 시에는 반드시 윤리적이고 합법적인 테두리 안에서 활용해야 합니다.
클래스 이름 변경: DarkwebScanner -> WebScanner
__init__ 수정: use_tor (boolean) 파라미터 추가. .onion 주소 입력 시 use_tor가 False면 경고 후 자동으로 True로 설정.
_is_valid_url 수정: 일반 http/https URL과 .onion URL 형식을 검사. use_tor 설정에 따라 유효성 검사 로직 변경.
_create_session 수정: use_tor 값에 따라 session.proxies를 설정하고, 각각의 경우에 맞는 연결 테스트(Tor 또는 일반 웹)를 수행.
main 함수 수정:
--use-tor 명령줄 인자 추가 (기본값은 False).
WebScanner 생성 시 args.use_tor 값을 전달.
도움말 및 경고 메시지 업데이트.
프레임워크 기반 스캔 조건 제거: 이제 프레임워크 분석 결과와 관계없이 항상 딕셔너리 스캔을 수행합니다 (프레임워크 정보는 보고서에 참고용으로 표시).
프레임워크 분석 강화: CMS(WordPress, Joomla, Drupal 예시) 탐지 로직 추가 및 점수 기반 추론 개선.
딕셔너리 스캔 로깅 및 결과:
404 응답은 기본적으로 DEBUG 레벨로 로깅 (verbose 모드에서만 보임).
403(Forbidden), 401/407(Unauthorized), 5xx(Server Error) 등 유의미한 상태 코드에 대해 WARNING/ERROR 레벨 로깅 및 보고서에 강조.
리다이렉션 발생 시 최종 URL도 결과에 기록.
진행률 표시 추가 (터미널 환경).
보고서 개선: 상태 코드별 그룹핑 시 우선순위(200, 403, 401, 5xx 등)를 두어 중요한 결과를 먼저 보여주도록 개선.
오류 처리: SSL 오류 처리 로직 추가 (기본적으로 실패 처리, 필요시 주석 해제하여 verify=False 사용 가능 - 보안 위험).
사용법:

일반 웹사이트 스캔:
Bash

python your_script_name.py https://example.com -d common_dirs.txt -o report.txt
다크웹 사이트 스캔 (Tor 필요):
Bash

python your_script_name.py http://youronionaddress.onion --use-tor -d common_dirs.txt -o report_onion.txt -v
(Tor 서비스가 로컬 9050 포트에서 실행 중이어야 합니다)

__init__: max_depth 파라미터 및 크롤링 상태 관리 변수(visited_urls, crawl_results) 추가.
start_recursive_crawl 메서드:
collections.deque를 사용하여 BFS(너비 우선 탐색) 방식으로 크롤링 큐 관리.
(url, depth) 튜플을 큐에 저장.
visited_urls 세트를 사용하여 방문한 URL 체크 및 루프 방지.
max_depth를 초과하는 경로는 큐에 추가하지 않음.
내부적으로 _process_page를 호출하여 각 페이지 처리 및 링크 추출.
초기 페이지의 응답을 저장하여 크롤링 완료 후 analyze_framework 호출.
_process_page 메서드:
기존 crawl 메서드의 역할을 수행 (단일 페이지 fetch, parse, link extraction).
크롤링 결과를 self.crawl_results에 기록.
main 함수:
--max-depth 인자 추가 (기본값 1).
WebScanner 생성 시 max_depth 전달.
start_recursive_crawl() 호출하여 크롤링 시작.
딕셔너리 스캔은 크롤링 완료 후 수행.
report 메서드:
크롤링 결과(방문 URL, 상태 코드, 콘텐츠 타입) 섹션 추가.
딕셔너리 스캔 결과는 기존과 동일하게 보고.
이제 --max-depth 옵션을 사용하여 원하는 깊이까지 사이트를 재귀적으로 탐색할 수 있습니다.

--max-depth 0: 시작 URL만 처리 (링크 따라가지 않음).
--max-depth 1: 시작 URL 처리 및 해당 페이지의 링크들 1회 방문.
--max-depth 2: 시작 URL -> 링크된 페이지 -> 해당 페이지들에서 링크된 페이지까지 방문.

'''