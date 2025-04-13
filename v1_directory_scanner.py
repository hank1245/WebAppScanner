import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import concurrent.futures
import re

class DirectoryScanner:
    def __init__(self, target_url, dictionary):
        self.target_url = target_url
        self.base_domain = urlparse(target_url).netloc
        self.dictionary = dictionary
        self.found_directories = {}

    def fetch_url(self, url):
        try:
            response = requests.get(url)
            return response.text
        except Exception:
            return ""

    def crawl(self):
        # 웹 크롤링: 시작 URL에서 내부 링크 추출
        html = self.fetch_url(self.target_url)
        soup = BeautifulSoup(html, 'html.parser')
        links = [urljoin(self.target_url, a.get('href')) for a in soup.find_all('a', href=True)]
        return links

    def dictionary_scan(self):
        # 딕셔너리 기반 디렉토리 스캔
        results = {}
        for dir_name in self.dictionary:
            url = f"{self.target_url.rstrip('/')}/{dir_name.lstrip('/')}"
            try:
                response = requests.get(url)
                results[url] = {
                    'status_code': response.status_code,
                    'content_length': len(response.content)
                }
            except Exception:
                results[url] = None
        self.found_directories.update(results)

    def check_directory_listing(self):
        # 간단한 디렉토리 리스팅 탐지
        listing_pattern = r"Index of /"
        for url, info in self.found_directories.items():
            if info and info['status_code'] == 200:
                response = requests.get(url)
                if re.search(listing_pattern, response.text, re.IGNORECASE):
                    info['directory_listing'] = True
                else:
                    info['directory_listing'] = False

    def report(self):
        # 결과 보고
        for url, info in self.found_directories.items():
            print(f"URL: {url}")
            if info:
                print(f"  Status: {info['status_code']}, Length: {info['content_length']}, "
                      f"Listing: {info.get('directory_listing', False)}")
            else:
                print("  Request failed.")

if __name__ == "__main__":
    scanner = DirectoryScanner("http://testphp.vulnweb.com", ["admin", "backup", "config", "logs", "test"])
    scanner.dictionary_scan()
    scanner.check_directory_listing()
    scanner.report()
