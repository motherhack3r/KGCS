import pytest
from unittest.mock import patch
from src.ingest.downloader import StandardsDownloader

class TestStandardsDownloader:
    @patch('src.ingest.downloader.StandardsDownloader.download_file')
    def test_download_mitre_shield(self, mock_download_file):
        downloader = StandardsDownloader()
        downloader.download_mitre_shield()
        assert mock_download_file.called

    @patch('data_raw.src.downloader.StandardsDownloader.download_file')
    def test_download_mitre_engage(self, mock_download_file):
        downloader = StandardsDownloader()
        downloader.download_mitre_engage()
        assert mock_download_file.called

    # Add more tests for other methods as needed
