"""
Tests for main.py - Main application entry point.
"""
import pytest
import sys
import signal
import logging
from unittest.mock import Mock, patch, MagicMock, call
import tempfile
import os

# Import the functions to test
from main import setup_logging, initialize_camera, signal_handler, main


class TestSetupLogging:
    """Test logging setup functionality."""
    
    def test_setup_logging_returns_logger(self):
        """Test that setup_logging returns a logger instance."""
        logger = setup_logging()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "main"  # When imported as module, name is 'main'
    
    def test_setup_logging_configures_handlers(self):
        """Test that logging is configured with proper handlers."""
        with patch('logging.basicConfig') as mock_basic_config:
            setup_logging()
            mock_basic_config.assert_called_once()
            
            # Check that basicConfig was called with expected arguments
            call_args = mock_basic_config.call_args
            assert call_args[1]['level'] == logging.INFO
            assert 'handlers' in call_args[1]
            assert len(call_args[1]['handlers']) == 2


class TestInitializeCamera:
    """Test camera initialization functionality."""
    
    @patch('main.CameraFactory')
    @patch('builtins.print')
    def test_initialize_camera_success(self, mock_print, mock_factory):
        """Test successful camera initialization."""
        # Mock camera instance
        mock_camera = Mock()
        mock_camera.create_preview_configuration.return_value = {'width': 640, 'height': 480}
        mock_factory.create_camera.return_value = mock_camera
        
        result = initialize_camera()
        
        # Verify camera was created and configured
        mock_factory.create_camera.assert_called_once()
        mock_camera.initialize.assert_called_once()
        mock_camera.create_preview_configuration.assert_called_once()
        mock_camera.configure.assert_called_once_with({'width': 640, 'height': 480})
        mock_camera.start.assert_called_once()
        mock_print.assert_called_with("Camera initialized successfully")
        assert result == mock_camera
    
    @patch('main.CameraFactory')
    @patch('builtins.print')
    def test_initialize_camera_factory_exception(self, mock_print, mock_factory):
        """Test camera initialization when factory raises exception."""
        mock_factory.create_camera.side_effect = Exception("Factory error")
        
        result = initialize_camera()
        
        mock_print.assert_called_with("Failed to initialize camera: Factory error")
        assert result is None
    
    @patch('main.CameraFactory')
    @patch('builtins.print')
    def test_initialize_camera_initialize_exception(self, mock_print, mock_factory):
        """Test camera initialization when camera.initialize() raises exception."""
        mock_camera = Mock()
        mock_camera.initialize.side_effect = Exception("Initialize error")
        mock_factory.create_camera.return_value = mock_camera
        
        result = initialize_camera()
        
        mock_print.assert_called_with("Failed to initialize camera: Initialize error")
        assert result is None
    
    @patch('main.CameraFactory')
    @patch('builtins.print')
    def test_initialize_camera_configure_exception(self, mock_print, mock_factory):
        """Test camera initialization when camera.configure() raises exception."""
        mock_camera = Mock()
        mock_camera.create_preview_configuration.return_value = {'width': 640, 'height': 480}
        mock_camera.configure.side_effect = Exception("Configure error")
        mock_factory.create_camera.return_value = mock_camera
        
        result = initialize_camera()
        
        mock_print.assert_called_with("Failed to initialize camera: Configure error")
        assert result is None


class TestSignalHandler:
    """Test signal handling functionality."""
    
    @patch('main.sys')
    @patch('builtins.print')
    def test_signal_handler_with_camera(self, mock_print, mock_sys):
        """Test signal handler when camera exists."""
        # Mock global camera
        mock_camera = Mock()
        
        # Mock the global camera variable
        with patch.dict('main.__dict__', {'camera': mock_camera}):
            signal_handler(signal.SIGINT, None)
            
            mock_print.assert_has_calls([
                call("Received termination signal, shutting down..."),
                call("Camera restored to original state and cleaned up")
            ])
            mock_camera.stop.assert_called_once()
            mock_camera.cleanup.assert_called_once()
            mock_sys.exit.assert_called_with(0)
    
    @patch('main.sys')
    @patch('builtins.print')
    def test_signal_handler_without_camera(self, mock_print, mock_sys):
        """Test signal handler when camera doesn't exist."""
        # Mock the global camera variable as None
        with patch.dict('main.__dict__', {'camera': None}):
            signal_handler(signal.SIGINT, None)
            
            mock_print.assert_called_with("Received termination signal, shutting down...")
            mock_sys.exit.assert_called_with(0)
    
    @patch('main.sys')
    @patch('builtins.print')
    def test_signal_handler_camera_cleanup_exception(self, mock_print, mock_sys):
        """Test signal handler when camera cleanup raises exception."""
        mock_camera = Mock()
        mock_camera.stop.side_effect = Exception("Stop error")
        
        # Mock the global camera variable
        with patch.dict('main.__dict__', {'camera': mock_camera}):
            signal_handler(signal.SIGINT, None)
            
            mock_print.assert_has_calls([
                call("Received termination signal, shutting down..."),
                call("Error during camera cleanup: Stop error")
            ])
            mock_sys.exit.assert_called_with(0)


class TestMain:
    """Test main function functionality."""
    
    @patch('main.signal')
    @patch('main.initialize_camera')
    @patch('main.WandaApp')
    @patch('builtins.print')
    def test_main_success(self, mock_print, mock_wanda_app, mock_init_camera, mock_signal):
        """Test successful main execution."""
        # Mock camera
        mock_camera = Mock()
        mock_init_camera.return_value = mock_camera
        
        # Mock WandaApp
        mock_app = Mock()
        mock_wanda_app.return_value = mock_app
        
        # Mock the global camera variable
        with patch.dict('main.__dict__', {'camera': mock_camera}):
            main()
            
            # Verify signal handlers were registered
            mock_signal.signal.assert_has_calls([
                call(mock_signal.SIGINT, signal_handler),
                call(mock_signal.SIGTERM, signal_handler)
            ])
            
            # Verify camera was initialized
            mock_init_camera.assert_called_once()
            
            # Verify WandaApp was created and run
            mock_wanda_app.assert_called_once_with(camera=mock_camera)
            mock_app.run.assert_called_once()
            
            # Verify logging
            mock_print.assert_called_with("Starting Wanda Astrophotography System")
    
    @patch('main.signal')
    @patch('main.initialize_camera')
    @patch('main.WandaApp')
    @patch('main.sys')
    @patch('builtins.print')
    def test_main_app_run_exception(self, mock_print, mock_sys, mock_wanda_app, mock_init_camera, mock_signal):
        """Test main when app.run() raises exception."""
        # Mock camera
        mock_camera = Mock()
        mock_init_camera.return_value = mock_camera
        
        # Mock WandaApp that raises exception
        mock_app = Mock()
        mock_app.run.side_effect = Exception("App run error")
        mock_wanda_app.return_value = mock_app
        
        # Mock the global camera variable
        with patch.dict('main.__dict__', {'camera': mock_camera}):
            main()
            
            # Verify error was logged
            mock_print.assert_has_calls([
                call("Starting Wanda Astrophotography System"),
                call("Error running application: App run error")
            ])
            
            # Verify camera cleanup was attempted
            mock_camera.stop.assert_called_once()
            mock_camera.cleanup.assert_called_once()
            
            # Verify system exit
            mock_sys.exit.assert_called_with(1)
    
    @patch('main.signal')
    @patch('main.initialize_camera')
    @patch('main.WandaApp')
    @patch('main.sys')
    @patch('builtins.print')
    def test_main_app_run_exception_no_camera(self, mock_print, mock_sys, mock_wanda_app, mock_init_camera, mock_signal):
        """Test main when app.run() raises exception and camera is None."""
        # Mock camera as None
        mock_init_camera.return_value = None
        
        # Mock WandaApp that raises exception
        mock_app = Mock()
        mock_app.run.side_effect = Exception("App run error")
        mock_wanda_app.return_value = mock_app
        
        # Mock the global camera variable as None
        with patch.dict('main.__dict__', {'camera': None}):
            main()
            
            # Verify error was logged
            mock_print.assert_has_calls([
                call("Starting Wanda Astrophotography System"),
                call("Error running application: App run error")
            ])
            
            # Verify system exit
            mock_sys.exit.assert_called_with(1)
    
    @patch('main.signal')
    @patch('main.initialize_camera')
    @patch('main.WandaApp')
    @patch('main.sys')
    @patch('builtins.print')
    def test_main_app_run_exception_camera_cleanup_fails(self, mock_print, mock_sys, mock_wanda_app, mock_init_camera, mock_signal):
        """Test main when app.run() raises exception and camera cleanup also fails."""
        # Mock camera
        mock_camera = Mock()
        mock_camera.stop.side_effect = Exception("Stop error")
        mock_init_camera.return_value = mock_camera
        
        # Mock WandaApp that raises exception
        mock_app = Mock()
        mock_app.run.side_effect = Exception("App run error")
        mock_wanda_app.return_value = mock_app
        
        # Mock the global camera variable
        with patch.dict('main.__dict__', {'camera': mock_camera}):
            main()
            
            # Verify error was logged
            mock_print.assert_has_calls([
                call("Starting Wanda Astrophotography System"),
                call("Error running application: App run error")
            ])
            
            # Verify system exit (even if cleanup fails)
            mock_sys.exit.assert_called_with(1)


class TestMainModule:
    """Test main module execution."""
    
    def test_main_module_has_main_function(self):
        """Test that main module has the main function."""
        assert callable(main)
    
    def test_main_module_has_setup_logging_function(self):
        """Test that main module has the setup_logging function."""
        assert callable(setup_logging)
    
    def test_main_module_has_initialize_camera_function(self):
        """Test that main module has the initialize_camera function."""
        assert callable(initialize_camera)
    
    def test_main_module_has_signal_handler_function(self):
        """Test that main module has the signal_handler function."""
        assert callable(signal_handler)


class TestMainIntegration:
    """Integration tests for main module."""
    
    @patch('main.CameraFactory')
    @patch('main.WandaApp')
    @patch('builtins.print')
    def test_full_initialization_flow(self, mock_print, mock_wanda_app, mock_factory):
        """Test the full initialization flow from main."""
        # Mock camera
        mock_camera = Mock()
        mock_camera.create_preview_configuration.return_value = {'width': 640, 'height': 480}
        mock_factory.create_camera.return_value = mock_camera
        
        # Mock WandaApp
        mock_app = Mock()
        mock_wanda_app.return_value = mock_app
        
        # Mock signal handlers
        with patch('main.signal') as mock_signal:
            # Mock the global camera variable
            with patch.dict('main.__dict__', {'camera': mock_camera}):
                main()
                
                # Verify the complete flow
                mock_factory.create_camera.assert_called_once()
                mock_camera.initialize.assert_called_once()
                mock_camera.create_preview_configuration.assert_called_once()
                mock_camera.configure.assert_called_once()
                mock_camera.start.assert_called_once()
                mock_wanda_app.assert_called_once_with(camera=mock_camera)
                mock_app.run.assert_called_once()
                
                # Verify signal handlers were registered
                mock_signal.signal.assert_has_calls([
                    call(mock_signal.SIGINT, signal_handler),
                    call(mock_signal.SIGTERM, signal_handler)
                ]) 