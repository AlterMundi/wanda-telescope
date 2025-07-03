"""Unit tests for configuration."""
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import config

class TestConfig:
    def test_config_values_exist(self):
        """Test that required config values exist."""
        assert hasattr(config, "DEFAULT_EXPOSURE_US")
        assert hasattr(config, "DEFAULT_GAIN")
        assert hasattr(config, "HOST")
        assert hasattr(config, "PORT")

    def test_config_types(self):
        """Test config value types."""
        assert isinstance(config.DEFAULT_EXPOSURE_US, int)
        assert isinstance(config.HOST, str)
        assert isinstance(config.PORT, int)
