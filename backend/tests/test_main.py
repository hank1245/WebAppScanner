import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app

class TestMainAPI(unittest.TestCase):
    
    def setUp(self):
        self.client = TestClient(app)

    @patch('main.MultiWebScanner')
    def test_scan_endpoint_basic(self, mock_scanner_class):
        """기본 스캔 API 테스트"""
        mock_scanner = MagicMock()
        mock_scanner.found_directories = {}
        mock_scanner.server_info = {}
        mock_scanner_class.return_value = mock_scanner

        payload = {
            "target_urls": ["http://testphp.vulnweb.com"],
            "mode": "normal",
            "exclusions": [],
            "max_depth": 1,
            "respect_robots_txt": True,
            "dictionary_operations": [],
            "use_default_dictionary": True,
            "session_cookies_string": None
        }

        response = self.client.post("/scan", json=payload)
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()