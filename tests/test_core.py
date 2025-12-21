import pytest
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock
from data_integrity_tool.core import calculate_file_hash, verify_archive_integrity, get_archive_content_hash, create_hashes, ArchiveError

@pytest.fixture
def temp_file(tmp_path):
    p = tmp_path / "test.txt"
    p.write_text("hello world")
    return p

def test_calculate_file_hash(temp_file):
    expected = hashlib.sha256(b"hello world").hexdigest()
    assert calculate_file_hash(temp_file) == expected

@patch("subprocess.run")
@patch("shutil.which")
def test_verify_archive_integrity_success(mock_which, mock_run, tmp_path):
    mock_which.return_value = "/usr/bin/7z"
    mock_run.return_value = MagicMock(returncode=0)
    
    archive = tmp_path / "test.zip"
    assert verify_archive_integrity(archive) is True

@patch("subprocess.run")
@patch("shutil.which")
def test_verify_archive_integrity_failure(mock_which, mock_run, tmp_path):
    mock_which.return_value = "/usr/bin/7z"
    mock_run.return_value = MagicMock(returncode=1)
    
    archive = tmp_path / "test.zip"
    assert verify_archive_integrity(archive) is False

@patch("subprocess.run")
@patch("shutil.which")
def test_get_archive_content_hash(mock_which, mock_run, tmp_path):
    mock_which.return_value = "/usr/bin/7z"
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout="Everything is Ok\nSHA256 for data: abcdef123456\n"
    )
    
    archive = tmp_path / "test.zip"
    assert get_archive_content_hash(archive) == "abcdef123456"

@patch("data_integrity_tool.core.calculate_file_hash")
@patch("data_integrity_tool.core.get_archive_content_hash")
def test_create_hashes(mock_get_content, mock_calc_hash, temp_file):
    mock_calc_hash.return_value = "hash123"
    mock_get_content.return_value = "content123"
    
    # Rename temp_file to simulate archive
    archive = temp_file.with_name("test.zip")
    temp_file.rename(archive)
    
    hash_file, content_hash_file = create_hashes(archive)
    
    assert hash_file.exists()
    assert content_hash_file.exists()
    
    assert "hash123" in hash_file.read_text()
    assert "content123" in content_hash_file.read_text()
