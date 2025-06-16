"""Unit tests for storage utilities."""
import pytest
import tempfile
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.storage import get_capture_dir, get_free_space, format_space

class TestStorageUtils:
    def test_get_capture_dir(self):
        """Test capture directory selection."""
        capture_dir = get_capture_dir()
        assert isinstance(capture_dir, str)
        assert len(capture_dir) > 0

    def test_get_free_space(self):
        """Test getting free space."""
        free_space = get_free_space(".")
        assert isinstance(free_space, int)
        assert free_space >= 0

    def test_format_space(self):
        """Test space formatting."""
        assert format_space(1024) == "1.0 KB"
        assert format_space(1024 * 1024) == "1.0 MB"
