import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# 프로젝트 루트의 backend 폴더를 sys.path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scanner import MultiWebScanner

TARGET_HOST_URL = "http://testphp.vulnweb.com"

class TestMultiWebScannerSimplified(unittest.TestCase):

    @patch('scanner.requests.Session.get')
    def test_initialization_and_robots_txt_handling(self, mock_session_get):
        """스캐너 초기화 및 robots.txt 기본 처리 (성공 및 404) 테스트"""
        # Case 1: robots.txt found
        mock_robots_response_found = MagicMock()
        mock_robots_response_found.status_code = 200
        mock_robots_response_found.text = "User-agent: *\nDisallow: /admin/"
        mock_robots_response_found.headers = {'Server': 'TestServer', 'Content-Type': 'text/plain'}
        
        # Case 2: robots.txt not found (다른 응답 객체 사용)
        mock_robots_response_not_found = MagicMock()
        mock_robots_response_not_found.status_code = 404
        mock_robots_response_not_found.headers = {'Server': 'TestServer', 'Content-Type': 'text/plain'}

        # Test with robots.txt found
        mock_session_get.return_value = mock_robots_response_found
        scanner_found = MultiWebScanner(
            target_url=TARGET_HOST_URL, # 기본 TARGET_HOST_URL 사용
            dictionary=[],
            respect_robots_txt=True
        )
        self.assertEqual(scanner_found.target_url, TARGET_HOST_URL)
        self.assertTrue(scanner_found.respect_robots_txt)
        self.assertIn(f"{TARGET_HOST_URL}/admin/", scanner_found.robots_disallowed_paths)
        mock_session_get.assert_called_with(f"{TARGET_HOST_URL}/robots.txt", timeout=10)
        mock_session_get.reset_mock() 

        # Test with robots.txt not found
        # MultiWebScanner는 target_url의 루트에서 robots.txt를 찾으므로,
        # 다른 target_url을 사용해도 robots.txt 경로는 동일한 호스트의 루트가 됨
        mock_session_get.return_value = mock_robots_response_not_found
        scanner_not_found = MultiWebScanner(
            target_url=f"{TARGET_HOST_URL}/some/other/path", # 다른 target_url로 초기화
            dictionary=[],
            respect_robots_txt=True
        )
        self.assertEqual(scanner_not_found.robots_disallowed_paths, set())
        # robots.txt는 항상 target_url의 scheme + netloc + /robots.txt 에서 가져옴
        # urlparse(f"{TARGET_HOST_URL}/some/other/path").scheme -> http
        # urlparse(f"{TARGET_HOST_URL}/some/other/path").netloc -> testphp.vulnweb.com
        # 따라서 robots.txt URL은 f"{TARGET_HOST_URL}/robots.txt"가 되어야 함
        mock_session_get.assert_called_with(f"{TARGET_HOST_URL}/robots.txt", timeout=10)

    @patch('scanner.requests.Session.get')
    def test_fetch_url_basic(self, mock_session_get):
        """fetch_url 기본 성공 및 실패(404) 테스트"""
        mock_page_success_response = MagicMock()
        mock_page_success_response.status_code = 200
        mock_page_success_response.text = "<html>Success</html>"
        mock_page_success_response.content = b"<html>Success</html>"
        mock_page_success_response.headers = {'Content-Type': 'text/html', 'Server': 'TestServer'}

        mock_page_not_found_response = MagicMock()
        mock_page_not_found_response.status_code = 404
        mock_page_not_found_response.text = "Not Found"
        mock_page_not_found_response.content = b"Not Found"
        mock_page_not_found_response.headers = {'Content-Type': 'text/html', 'Server': 'TestServer'}
        
        # Scenario 1: Successful fetch
        scanner_success = MultiWebScanner(target_url=TARGET_HOST_URL, dictionary=[], respect_robots_txt=False)
        mock_session_get.return_value = mock_page_success_response
        
        response_success = scanner_success.fetch_url(f"{TARGET_HOST_URL}/goodpage")
        
        self.assertIsNotNone(response_success)
        self.assertEqual(response_success.status_code, 200)
        # allow_redirects 인자 없이 실제 호출과 일치하도록 수정
        mock_session_get.assert_called_once_with(f"{TARGET_HOST_URL}/goodpage", timeout=10)
        mock_session_get.reset_mock()

        # Scenario 2: Not found fetch
        scanner_not_found = MultiWebScanner(target_url=TARGET_HOST_URL, dictionary=[], respect_robots_txt=False)
        mock_session_get.return_value = mock_page_not_found_response

        response_not_found = scanner_not_found.fetch_url(f"{TARGET_HOST_URL}/badpage")
        self.assertIsNotNone(response_not_found) 
        self.assertEqual(response_not_found.status_code, 404)
        # allow_redirects 인자 없이 실제 호출과 일치하도록 수정
        mock_session_get.assert_called_once_with(f"{TARGET_HOST_URL}/badpage", timeout=10)

    def test_is_excluded_simple(self):
        """간단한 경로 제외 테스트 (네트워크 호출 없음)"""
        with patch('scanner.requests.Session.get') as mock_get_init_for_robots:
            mock_get_init_for_robots.return_value.status_code = 404 
            
            scanner = MultiWebScanner(
                target_url=TARGET_HOST_URL,
                dictionary=[],
                exclusions={"/secret/", "/confidential/path/"}, 
                respect_robots_txt=False 
            )
        
        self.assertTrue(scanner.is_excluded(f"{TARGET_HOST_URL}/secret/file.txt"), 
                        f"URL '{TARGET_HOST_URL}/secret/file.txt' should be excluded by '/secret/'")
        self.assertTrue(scanner.is_excluded(f"{TARGET_HOST_URL}/confidential/path/deep/file.php"),
                        f"URL '{TARGET_HOST_URL}/confidential/path/deep/file.php' should be excluded by '/confidential/path/'")
        self.assertFalse(scanner.is_excluded(f"{TARGET_HOST_URL}/public/file.txt"),
                         f"URL '{TARGET_HOST_URL}/public/file.txt' should not be excluded")
        self.assertFalse(scanner.is_excluded(f"{TARGET_HOST_URL}/secret"), 
                         f"URL '{TARGET_HOST_URL}/secret' should not be excluded by '/secret/' if trailing slash matters in pattern")


if __name__ == '__main__':
    unittest.main()