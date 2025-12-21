import unittest
from pathlib import Path
import tempfile
import shutil
import sys
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data_integrity_tool.core import find_hash_files

class TestFindHashFiles(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.archive_path = Path(self.test_dir) / "test.zip"
        self.archive_path.touch()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_no_hashes(self):
        result = find_hash_files(self.archive_path)
        self.assertIsNone(result['archive_hash'])
        self.assertIsNone(result['content_hash'])

    def test_archive_hash_only(self):
        hash_file = Path(str(self.archive_path) + ".sha256")
        hash_file.touch()
        
        result = find_hash_files(self.archive_path)
        self.assertEqual(result['archive_hash'], hash_file)
        self.assertIsNone(result['content_hash'])

    def test_content_hash_only(self):
        content_hash_file = Path(str(self.archive_path) + ".content.sha256")
        content_hash_file.touch()
        
        result = find_hash_files(self.archive_path)
        self.assertIsNone(result['archive_hash'])
        self.assertEqual(result['content_hash'], content_hash_file)

    def test_both_hashes(self):
        hash_file = Path(str(self.archive_path) + ".sha256")
        hash_file.touch()
        content_hash_file = Path(str(self.archive_path) + ".content.sha256")
        content_hash_file.touch()
        
        result = find_hash_files(self.archive_path)
        self.assertEqual(result['archive_hash'], hash_file)
        self.assertEqual(result['content_hash'], content_hash_file)

if __name__ == '__main__':
    unittest.main()
