import unittest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scanner import MultiWebScanner

TARGET_HOST_URL = "http://testphp.vulnweb.com"

class TestIntegrationSimplified(unittest.TestCase):

    @patch('scanner.requests.Session.get')
    def test_scanner_creation_with_robots_check(self, mock_session_get):
        """스캐너 생성 및 robots.txt 확인 (모킹) 테스트"""
        mock_robots_response = MagicMock()
        mock_robots_response.status_code = 200
        mock_robots_response.text = "User-agent: *\nDisallow: /confidential/" # robots.txt는 경로만 포함
        mock_robots_response.headers = {'Server': 'TestServer', 'Content-Type': 'text/plain'}
        mock_session_get.return_value = mock_robots_response
        
        scanner = MultiWebScanner(
            target_url=TARGET_HOST_URL,
            dictionary=["test/"],
            mode="normal",
            respect_robots_txt=True
        )
        
        self.assertIsNotNone(scanner)
        self.assertEqual(scanner.target_url, TARGET_HOST_URL)
        # robots_disallowed_paths는 전체 URL로 저장됨
        self.assertIn(f"{TARGET_HOST_URL}/confidential/", scanner.robots_disallowed_paths)
        mock_session_get.assert_called_once_with(f"{TARGET_HOST_URL}/robots.txt", timeout=10)

if __name__ == '__main__':
    unittest.main()