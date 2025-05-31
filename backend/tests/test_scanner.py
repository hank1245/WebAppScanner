import unittest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scanner import MultiWebScanner

class TestMultiWebScanner(unittest.TestCase):
    
    def setUp(self):
        self.scanner = MultiWebScanner(
            target_url="http://testphp.vulnweb.com",
            dictionary=["admin/"],
            mode="normal"
        )

    def test_init(self):
        """스캐너 초기화 테스트"""
        self.assertEqual(self.scanner.target_url, "http://testphp.vulnweb.com")
        self.assertEqual(self.scanner.dictionary, ["admin/"])
        self.assertEqual(self.scanner.mode, "normal")

    def test_is_excluded_basic(self):
        """기본 제외 확인 테스트"""
        # 제외 목록에 없는 URL은 False 반환
        result = self.scanner.is_excluded("http://testphp.vulnweb.com/login.php")
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()