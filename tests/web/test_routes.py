"""Unit tests for web routes."""
import pytest
import json
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class TestWebRoutes:
    def test_index_get(self, client):
        """Test GET request to index page."""
        response = client.get("/")
        assert response.status_code == 200
        assert b"Wanda Telescope" in response.data

    def test_video_feed(self, client):
        """Test video feed endpoint."""
        response = client.get("/video_feed")
        assert response.status_code == 200

    def test_capture_still(self, client):
        """Test capture still endpoint."""
        response = client.post("/capture_still")
        assert response.status_code in [200, 302]

    def test_start_tracking(self, client):
        """Test start tracking endpoint."""
        response = client.post("/start_tracking")
        assert response.status_code in [200, 302]
