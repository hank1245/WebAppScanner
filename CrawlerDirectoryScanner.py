import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import argparse
import concurrent.futures
import re
from collections import defaultdict

class CrawlerDirectoryScanner:
    def __init__(self, target_url, max_depth=3, threads=10, dictionary_file=None, timeout=5):
        self.target_url = target_url
        self.base_domain = urlparse(target_url).netloc
        self.max_depth = max_depth
        self.threads = threads
        self.timeout = timeout
        self.visited_urls = set()
        self.directories = set()
        self.found_directories = defaultdict(list)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # 사전 파일 로드 (기존 무차별 대입 스캐너에서 사용하던 사전)
        self.dictionary = []
        if dictionary_file:
            try:
                with open(dictionary_file, 'r') as f:
                    self.dictionary = [line.strip() for line in f.readlines()]
                print(f"[+] Loaded {len(self.dictionary)} directories from dictionary file")
            except Exception as e:
                print(f"[-] Error loading dictionary file: {e}")
    
    def is_same_domain(self, url):
        """URL이 동일한 도메인에 속하는지 확인"""
        parsed_url = urlparse(url)
        return parsed_url.netloc == self.base_domain or not parsed_url.netloc
    
    def normalize_url(self, url):
        """URL을 정규화"""
        # 쿼리 파라미터와 프래그먼트 제거
        url = url.split('?')[0].split('#')[0]
        # URL 끝의 슬래시 제거
        if url.endswith('/'):
            url = url[:-1]
        return url
    
    def extract_directory(self, url):
        """URL에서 디렉토리 경로 추출"""
        parsed_url = urlparse(url)
        path = parsed_url.path
        
        # 경로가 없거나 루트인 경우 무시
        if not path or path == '/':
            return None
            
        # 파일 확장자가 있는 URL인 경우 파일명 제거하고 디렉토리만 추출
        if '.' in path.split('/')[-1]:
            directory = '/'.join(path.split('/')[:-1])
            if not directory:
                directory = '/'
        else:
            directory = path
            
        return directory
    
    def fetch_url(self, url, depth=0):
        """URL을 방문하고 링크를 추출"""
        if url in self.visited_urls or depth > self.max_depth:
            return []
        
        try:
            self.visited_urls.add(url)
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            
            # 성공적인 응답만 처리
            if response.status_code != 200:
                return []
                
            # 디렉토리 추출 및 저장
            directory = self.extract_directory(url)
            if directory:
                self.directories.add(directory)
                self.found_directories[directory].append({
                    'url': url,
                    'status_code': response.status_code,
                    'content_length': len(response.content)
                })
                
            # 링크 추출
            soup = BeautifulSoup(response.text, 'html.parser')
            links = []
            
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                absolute_url = urljoin(url, href)
                
                # 같은 도메인만 처리
                if self.is_same_domain(absolute_url):
                    normalized_url = self.normalize_url(absolute_url)
                    links.append(normalized_url)
            
            return links
            
        except Exception as e:
            print(f"[-] Error fetching {url}: {e}")
            return []
    
    def crawl(self):
        """웹사이트 크롤링 시작"""
        print(f"[+] Starting crawler on {self.target_url} with max depth {self.max_depth}")
        queue = [(self.target_url, 0)]  # (url, depth)
        
        while queue:
            current_batch = queue[:self.threads]
            queue = queue[self.threads:]
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.threads) as executor:
                future_to_url = {executor.submit(self.fetch_url, url, depth): (url, depth) for url, depth in current_batch}
                
                for future in concurrent.futures.as_completed(future_to_url):
                    url, depth = future_to_url[future]
                    try:
                        new_links = future.result()
                        for link in new_links:
                            if link not in self.visited_urls:
                                queue.append((link, depth + 1))
                    except Exception as e:
                        print(f"[-] Error processing {url}: {e}")
        
        print(f"[+] Crawling completed. Found {len(self.directories)} directories.")
    
    def dictionary_scan(self):
        """사전 기반 디렉토리 스캔"""
        if not self.dictionary:
            print("[-] No dictionary loaded, skipping dictionary scan")
            return
            
        print(f"[+] Starting dictionary-based scan with {len(self.dictionary)} entries")
        base_url = self.target_url.rstrip('/')
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = []
            for dir_name in self.dictionary:
                dir_name = dir_name.lstrip('/')
                test_url = f"{base_url}/{dir_name}"
                futures.append(executor.submit(self.test_directory, test_url))
                
        print(f"[+] Dictionary scan completed")
    
    def test_directory(self, url):
        """디렉토리 존재 여부 테스트"""
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            directory = self.extract_directory(url)
            
            if directory and response.status_code == 200:
                self.directories.add(directory)
                self.found_directories[directory].append({
                    'url': url,
                    'status_code': response.status_code,
                    'content_length': len(response.content)
                })
                print(f"[+] Found directory: {directory} ({response.status_code})")
        except Exception as e:
            pass
    
    def check_directory_listing(self):
        """발견된 디렉토리에서 디렉토리 리스팅 취약점 확인"""
        print(f"[+] Checking directory listing vulnerability in {len(self.directories)} directories")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = []
            for directory in self.directories:
                url = self.target_url.rstrip('/') + directory
                futures.append(executor.submit(self.check_listing, url, directory))
                
        print(f"[+] Directory listing check completed")
    
    def check_listing(self, url, directory):
        """디렉토리 리스팅 확인"""
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            
            # 디렉토리 리스팅 표시 패턴
            listing_patterns = [
                r'Index of /',
                r'<title>Index of',
                r'<h1>Index of',
                r'Directory Listing For',
                r'Parent Directory</a>'
            ]
            
            if response.status_code == 200:
                for pattern in listing_patterns:
                    if re.search(pattern, response.text, re.IGNORECASE):
                        print(f"[!] Directory listing found: {url}")
                        self.found_directories[directory].append({
                            'url': url,
                            'status_code': response.status_code,
                            'directory_listing': True,
                            'content_length': len(response.content)
                        })
                        break
        except Exception as e:
            pass
    
    def run(self):
        """전체 스캔 실행"""
        self.crawl()
        self.dictionary_scan()
        self.check_directory_listing()
        self.report()
    
    def report(self):
        """결과 보고서 생성"""
        print("\n" + "="*60)
        print("DIRECTORY SCANNER RESULTS")
        print("="*60)
        
        print(f"\nTotal URLs visited: {len(self.visited_urls)}")
        print(f"Total directories found: {len(self.directories)}")
        
        print("\nDirectories with directory listing vulnerability:")
        vulnerable_dirs = [d for d in self.found_directories if any(info.get('directory_listing') for info in self.found_directories[d])]
        
        if vulnerable_dirs:
            for dir_path in vulnerable_dirs:
                print(f"  - {dir_path}")
        else:
            print("  No directory listing vulnerabilities found")
            
        print("\nAll discovered directories:")
        for directory in sorted(self.directories):
            print(f"  - {directory}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Web Crawler Directory Scanner")
    parser.add_argument("-u", "--url", required=True, help="Target URL")
    parser.add_argument("-d", "--depth", type=int, default=3, help="Maximum crawling depth")
    parser.add_argument("-w", "--wordlist", help="Dictionary file for directory names")
    parser.add_argument("-t", "--threads", type=int, default=10, help="Number of threads")
    parser.add_argument("--timeout", type=int, default=5, help="Request timeout in seconds")
    
    args = parser.parse_args()
    
    scanner = CrawlerDirectoryScanner(
        target_url=args.url,
        max_depth=args.depth,
        threads=args.threads,
        dictionary_file=args.wordlist,
        timeout=args.timeout
    )
    
    scanner.run()