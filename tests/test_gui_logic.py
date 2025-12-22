import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys
import tempfile
import shutil
import tkinter as tk

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data_integrity_tool.gui import DataIntegrityApp, VerifyPage

class TestGUILogic(unittest.TestCase):
    def setUp(self):
        self.app = DataIntegrityApp()
        self.app.withdraw() # Hide window during tests
        self.verify_page = self.app.frames["VerifyPage"]
        
        self.test_dir = tempfile.mkdtemp()
        self.archive_path = Path(self.test_dir) / "test.zip"
        self.archive_path.touch()

    def tearDown(self):
        self.app.destroy()
        shutil.rmtree(self.test_dir)

    def test_auto_fill_hashes(self):
        # Create hash files
        hash_file = Path(str(self.archive_path) + ".sha256")
        hash_file.touch()
        content_hash_file = Path(str(self.archive_path) + ".content.sha256")
        content_hash_file.touch()

        # Simulate path change
        self.verify_page.check_hashes_for_file(str(self.archive_path))

        # Verify inputs were set
        self.assertEqual(self.verify_page.archive_hash_path.get(), str(hash_file))
        self.assertEqual(self.verify_page.content_hash_path.get(), str(content_hash_file))

    def test_auto_fill_no_hashes(self):
        # Simulate path change with no hashes
        self.verify_page.check_hashes_for_file(str(self.archive_path))

        # Verify inputs were cleared
        self.assertEqual(self.verify_page.archive_hash_path.get(), "")
        self.assertEqual(self.verify_page.content_hash_path.get(), "")

if __name__ == '__main__':
    unittest.main()
