import unittest
from unittest.mock import patch, MagicMock
from urllib.parse import urlparse
import sys
import os

# Add the backend directory to sys.path to allow imports
# This assumes the tests directory is directly inside the backend directory's parent
# or that scanner.py is otherwise findable.
# A more robust solution might involve setting PYTHONPATH or using a proper package structure.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scanner import MultiWebScanner # Should now be found due to sys.path modification

class TestMultiWebScanner(unittest.TestCase):

    def setUp(self):
        self.default_dictionary = ["admin", "test", "api/v1"]
        # MultiWebScanner 인스턴스 생성 시 필요한 최소 인자들로 초기화
        # 실제 테스트에서는 각 테스트 메서드 내에서 필요에 따라 mock 객체와 함께 생성

    @patch('scanner.requests.Session') # Note: path to mock might change based on how scanner is imported
    def test_init_session_cookies_parsing(self, MockSession):
        mock_session_instance = MockSession.return_value
        mock_session_instance.cookies = MagicMock()

        cookie_string = "sessionid=abc123; csrftoken=xyz789"
        scanner = MultiWebScanner(
            target_url="http://example.com",
            dictionary=self.default_dictionary,
            session_cookies_string=cookie_string
        )
        # 세션 쿠키가 올바르게 파싱되어 session 객체에 설정되었는지 확인
        mock_session_instance.cookies.update.assert_called_once_with({
            "sessionid": "abc123",
            "csrftoken": "xyz789"
        })

    @patch('scanner.requests.Session')
    def test_init_darkweb_mode_proxy(self, MockSession):
        mock_session_instance = MockSession.return_value
        
        scanner = MultiWebScanner(
            target_url="http://example.onion",
            dictionary=self.default_dictionary,
            mode="darkweb"
        )
        # darkweb 모드일 때 프록시가 설정되었는지 확인
        self.assertIn('http', scanner.session.proxies)
        self.assertIn('https', scanner.session.proxies)
        self.assertTrue(scanner.session.proxies['http'].startswith('socks5h://'))

    def test_parse_js_for_endpoints(self):
        # MultiWebScanner 인스턴스 생성 (여기서는 _parse_js_for_endpoints만 테스트하므로 session 모킹 불필요)
        scanner = MultiWebScanner(target_url="http://example.com", dictionary=[])
        
        js_content_fetch = """
        fetch('/api/users');
        fetch("http://example.com/api/data?id=1");
        fetch('../relative/path');
        """
        # page_url_where_script_was_found는 JS 파일이 발견된 HTML 페이지의 URL
        endpoints_fetch = scanner._parse_js_for_endpoints(js_content_fetch, "http://example.com/somepage.html")
        self.assertIn("http://example.com/api/users", endpoints_fetch)
        self.assertIn("http://example.com/api/data", endpoints_fetch) # 쿼리 파라미터 제거 확인
        self.assertIn("http://example.com/relative/path", endpoints_fetch) # 상대 경로 변환 확인

        js_content_axios = """
        axios.get('/v1/items');
        axios.post("https://example.com/v2/products");
        const myUrl = "/config/settings.json"; // 단순 문자열
        """
        endpoints_axios = scanner._parse_js_for_endpoints(js_content_axios, "http://example.com/another.html")
        self.assertIn("http://example.com/v1/items", endpoints_axios)
        self.assertIn("http://example.com/v2/products", endpoints_axios)
        self.assertIn("http://example.com/config/settings.json", endpoints_axios)

        js_content_no_api = "console.log('hello'); var x = '/assets/image.png';"
        endpoints_no_api = scanner._parse_js_for_endpoints(js_content_no_api, "http://example.com/")
        self.assertEqual(len(endpoints_no_api), 0)

        js_content_external = "fetch('http://external.com/api/info');"
        endpoints_external = scanner._parse_js_for_endpoints(js_content_external, "http://example.com/")
        self.assertNotIn("http://external.com/api/info", endpoints_external) # 외부 도메인 제외 확인

    @patch('scanner.MultiWebScanner.fetch_url')
    def test_dictionary_scan_single_found(self, mock_fetch_url):
        # 응답 모의 객체 설정
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"Directory Listing"
        mock_response.text = "Directory Listing" # analyze_directory_listing에서 사용
        mock_response.headers = {'Content-Type': 'text/html'}
        mock_fetch_url.return_value = mock_response

        scanner = MultiWebScanner(target_url="http://example.com", dictionary=[])
        # analyze_directory_listing이 True를 반환하도록 모킹 (필요시)
        scanner.analyze_directory_listing = MagicMock(return_value=True)

        url, info = scanner.dictionary_scan_single("http://example.com", "admin", source="test_source")

        self.assertEqual(url, "http://example.com/admin")
        self.assertEqual(info['status_code'], 200)
        self.assertEqual(info['content_length'], len(b"Directory Listing"))
        self.assertTrue(info['directory_listing'])
        self.assertEqual(info['source'], 'test_source')
        mock_fetch_url.assert_called_once_with("http://example.com/admin")

    @patch('scanner.MultiWebScanner.fetch_url')
    def test_dictionary_scan_single_not_found(self, mock_fetch_url):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.content = b"Not Found"
        mock_response.text = "Not Found"
        mock_response.headers = {}
        mock_fetch_url.return_value = mock_response

        scanner = MultiWebScanner(target_url="http://example.com", dictionary=[])
        scanner.analyze_directory_listing = MagicMock(return_value=False)

        url, info = scanner.dictionary_scan_single("http://example.com", "secret", source="test_source_nf")
        
        self.assertEqual(url, "http://example.com/secret")
        self.assertEqual(info['status_code'], 404)
        self.assertFalse(info['directory_listing'])
        self.assertEqual(info['source'], 'test_source_nf')

    @patch('scanner.MultiWebScanner.fetch_url')
    def test_dictionary_scan_single_excluded(self, mock_fetch_url):
        scanner = MultiWebScanner(target_url="http://example.com", dictionary=[], exclusions=["http://example.com/excluded_path"])
        
        url, info = scanner.dictionary_scan_single("http://example.com", "excluded_path", source="test_excluded")
        
        self.assertEqual(url, "http://example.com/excluded_path")
        self.assertEqual(info['status_code'], 'EXCLUDED')
        self.assertFalse(info['directory_listing'])
        self.assertEqual(info['source'], 'test_excluded')
        mock_fetch_url.assert_not_called() # 제외되었으므로 fetch_url 호출 안됨

    @patch('scanner.requests.Session')
    def test_is_excluded(self, MockSession):
        # robots.txt 파싱 모킹
        scanner = MultiWebScanner(
            target_url="http://example.com",
            dictionary=[],
            exclusions=["/user/settings", "/api/confidential"],
            respect_robots_txt=True
        )
        scanner._parse_robots_txt = MagicMock() # robots.txt 파싱 로직은 별도 테스트
        scanner.robots_disallowed_paths = {"http://example.com/robots_excluded/", "http://example.com/admin_via_robots/"} # Ensure full URLs if that's what is_disallowed_by_robots expects

        self.assertTrue(scanner.is_excluded("http://example.com/user/settings/profile"))
        self.assertTrue(scanner.is_excluded("http://example.com/api/confidential"))
        self.assertFalse(scanner.is_excluded("http://example.com/api/public"))
        
        self.assertTrue(scanner.is_excluded("http://example.com/robots_excluded/page.html"))
        self.assertFalse(scanner.is_excluded("http://example.com/allowed_by_robots/"))

        # respect_robots_txt = False 일 때
        scanner_no_robots = MultiWebScanner(
            target_url="http://example.com",
            dictionary=[],
            exclusions=["/user/settings"],
            respect_robots_txt=False
        )
        scanner_no_robots._parse_robots_txt = MagicMock()
        scanner_no_robots.robots_disallowed_paths = {"http://example.com/robots_excluded/"}
        self.assertFalse(scanner_no_robots.is_excluded("http://example.com/robots_excluded/page.html")) # Should not be excluded by robots
        self.assertTrue(scanner_no_robots.is_excluded("http://example.com/user/settings/profile"))


if __name__ == '__main__':
    unittest.main()