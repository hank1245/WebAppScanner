import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app # main.py에서 FastAPI app 객체를 가져옵니다.

class TestMainAppSimplified(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch('main.MultiWebScanner') # main.py 내에서 사용되는 MultiWebScanner를 모킹
    def test_scan_endpoint_success_call(self, mock_scanner_class):
        """/scan 엔드포인트 기본 성공 호출 테스트"""
        mock_scanner_instance = MagicMock()
        # MultiWebScanner.run()이 반환할 간단한 모의 결과
        mock_scanner_instance.run.return_value = {
            "directories": {"http://example.com/found": {"status_code": 200, "content_length": 100, "directory_listing": False, "note": "Mocked scan.", "source": "initial"}},
            "server_info": {"Server": "MockedServer/1.0"}
        }
        mock_scanner_class.return_value = mock_scanner_instance

        payload = {
            "target_urls": ["http://example.com"],
            "mode": "normal",
            "exclusions": [],
            "max_depth": 1,
            "respect_robots_txt": True,
            "dictionary_operations": [],
            "use_default_dictionary": False, # 기본 사전 사용 안 함으로 설정하여 외부 파일 의존성 줄임
            "custom_dictionary_path": None, # 또는 빈 리스트를 제공하는 custom_dictionary를 사용
            "session_cookies_string": None
        }

        response = self.client.post("/scan", json=payload)
        
        self.assertEqual(response.status_code, 200)
        # MultiWebScanner가 올바른 인자들로 초기화되었는지 간단히 확인
        mock_scanner_class.assert_called_once()
        args, kwargs = mock_scanner_class.call_args
        self.assertEqual(kwargs.get('target_url'), "http://example.com")
        self.assertEqual(kwargs.get('mode'), "normal")
        
        # run 메소드가 호출되었는지 확인
        mock_scanner_instance.run.assert_called_once()
        
        # 응답 내용에 대한 기본적인 검증
        response_data = response.json()
        self.assertIn("result", response_data)
        self.assertIn("http://example.com", response_data["result"])
        self.assertIn("directories", response_data["result"]["http://example.com"])

if __name__ == '__main__':
    unittest.main()