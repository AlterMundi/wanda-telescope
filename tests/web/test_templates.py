"""Unit tests for web templates."""
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class TestWebTemplates:
    def test_index_template_renders(self, client):
        """Test that index template renders correctly."""
        response = client.get("/")
        assert response.status_code == 200
        assert b"Camera Controls" in response.data
        assert b"Mount Controls" in response.data

    def test_template_has_required_elements(self, client):
        """Test that template contains required UI elements."""
        response = client.get("/")
        assert b"video_feed" in response.data
        assert b"capture_still" in response.data
        assert b"start_tracking" in response.data
