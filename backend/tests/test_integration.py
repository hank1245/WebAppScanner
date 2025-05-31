import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scanner import MultiWebScanner

class TestIntegration(unittest.TestCase):

    def test_scanner_creation(self):
        """스캐너 생성 테스트"""
        scanner = MultiWebScanner(
            target_url="http://testphp.vulnweb.com",
            dictionary=["admin/"],
            mode="normal"
        )
        
        self.assertIsNotNone(scanner)
        self.assertEqual(scanner.target_url, "http://testphp.vulnweb.com")

if __name__ == '__main__':
    unittest.main()