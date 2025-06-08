import unittest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scanner import MultiWebScanner

TARGET_HOST_URL = "http://testphp.vulnweb.com"

class TestMultiWebScannerSimplified(unittest.TestCase):
    
    @patch('scanner.requests.Session.get')
    def test_fetch_url_basic(self, mock_session_get):
        scanner_success = MultiWebScanner(target_url=TARGET_HOST_URL, dictionary=[], respect_robots_txt=False)
        
        mock_page_success_response = MagicMock()
        mock_page_success_response.status_code = 200
        mock_page_success_response.headers = {'Content-Type': 'text/html'}
        mock_page_success_response.text = "<html><body>Test Page</body></html>"
        
        mock_page_not_found_response = MagicMock()
        mock_page_not_found_response.status_code = 404
        mock_page_not_found_response.headers = {'Content-Type': 'text/html'}
        mock_page_not_found_response.text = "<html><body>Not Found</body></html>"
        
        mock_session_get.return_value = mock_page_success_response
        
        response_success = scanner_success.fetch_url(f"{TARGET_HOST_URL}/goodpage")
        
        self.assertIsNotNone(response_success)
        self.assertEqual(response_success.status_code, 200)
        mock_session_get.assert_called_once_with(f"{TARGET_HOST_URL}/goodpage", timeout=10)
        mock_session_get.reset_mock()

        scanner_not_found = MultiWebScanner(target_url=TARGET_HOST_URL, dictionary=[], respect_robots_txt=False)
        mock_session_get.return_value = mock_page_not_found_response

        response_not_found = scanner_not_found.fetch_url(f"{TARGET_HOST_URL}/badpage")
        self.assertIsNotNone(response_not_found) 
        self.assertEqual(response_not_found.status_code, 404)
        mock_session_get.assert_called_once_with(f"{TARGET_HOST_URL}/badpage", timeout=10)
    
    def test_is_excluded_simple(self):
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