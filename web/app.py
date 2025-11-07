"""
Web application for Wanda astrophotography system.
Provides a REST API, MJPEG video feed, and Socket.IO for the Next.js frontend.
"""
import concurrent.futures
import eventlet
import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

from flask import Flask, Response, request
from flask_cors import CORS
from flask_socketio import Namespace, SocketIO, emit

import config
from camera import CameraFactory  # noqa: F401 (retained for backward compatibility)
from mount.controller import MountController
from session import SessionController

from .api_responses import error_response, success_response

logger = logging.getLogger(__name__)

socketio: Optional[SocketIO] = None


class CameraNamespace(Namespace):
    namespace = "/ws/camera"

    def on_connect(self, auth=None, environ=None):  # type: ignore[override]
        logger.debug("Client connected to camera namespace")
        if hasattr(self.server, 'camera_ref') and self.server.camera_ref:
            emit("status", build_camera_status_payload(self.server.camera_ref))

    def on_disconnect(self):  # type: ignore[override]
        logger.debug("Client disconnected from camera namespace")


class MountNamespace(Namespace):
    namespace = "/ws/mount"

    def on_connect(self, auth=None, environ=None):  # type: ignore[override]
        logger.debug("Client connected to mount namespace")
        if hasattr(self.server, 'mount_ref') and self.server.mount_ref:
            emit("status", build_mount_status_payload(self.server.mount_ref))

    def on_disconnect(self):  # type: ignore[override]
        logger.debug("Client disconnected from mount namespace")


class SessionNamespace(Namespace):
    namespace = "/ws/session"

    def on_connect(self, auth=None, environ=None):  # type: ignore[override]
        logger.debug("Client connected to session namespace")
        if hasattr(self.server, 'session_ref') and self.server.session_ref:
            emit("status", self.server.session_ref.get_session_status())

    def on_disconnect(self):  # type: ignore[override]
        logger.debug("Client disconnected from session namespace")


class WandaApp:
    """Flask application exposing REST endpoints for the Wanda system."""

    def __init__(self, camera=None, *, cors_origins: Optional[Sequence[str]] = None):
        global socketio
        if camera is None:
            raise ValueError("Camera instance is required")

        self.camera = camera
        self.mount = MountController()
        self.session_controller = SessionController(
            self.camera, self.mount, self.camera.capture_dir, event_callback=self._handle_session_event
        )
        # Thread pool for blocking camera operations
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

        self.app = Flask(__name__)

        self._cors_origins = list(cors_origins) if cors_origins else ["http://localhost:3000"]
        CORS(self.app, origins=self._cors_origins)

        socketio = SocketIO(
            self.app,
            cors_allowed_origins=self._cors_origins,
            async_mode="eventlet",
        )
        socketio.camera_ref = self.camera  # type: ignore[attr-defined]
        socketio.mount_ref = self.mount    # type: ignore[attr-defined]
        socketio.session_ref = self.session_controller  # type: ignore[attr-defined]

        socketio.on_namespace(CameraNamespace(CameraNamespace.namespace))
        socketio.on_namespace(MountNamespace(MountNamespace.namespace))
        socketio.on_namespace(SessionNamespace(SessionNamespace.namespace))

        self.app.after_request(self._inject_default_cors_headers)  # type: ignore[arg-type]

        self._register_routes()
        logger.info("REST web application initialized with Socket.IO")

    def _inject_default_cors_headers(self, response):
        if self._cors_origins:
            response.headers.setdefault("Access-Control-Allow-Origin", self._cors_origins[0])
            response.headers.setdefault("Access-Control-Allow-Headers", "Content-Type")
            response.headers.setdefault("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        return response

    def run(self):
        """Run the web application."""
        try:
            logger.info("Starting web server on %s:%s", config.HOST, config.PORT)
            socketio.run(self.app, host=config.HOST, port=config.PORT)  # type: ignore[union-attr]
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error("Error in web server: %s", exc)
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources when shutting down."""
        logger.info("Application shutting down, cleaning up resources...")
        self.camera.cleanup()
        self.mount.cleanup()
        self.session_controller.cleanup()
        logger.info("Application shutdown complete")

    # ------------------------------------------------------------------
    # Route registration
    # ------------------------------------------------------------------
    def _register_routes(self):
        self.app.route("/video_feed", methods=["GET"])(self._video_feed)

        # Camera endpoints
        self.app.route("/api/camera/status", methods=["GET"])(self._camera_status)
        self.app.route("/api/camera/settings", methods=["POST"])(self._update_camera_settings)
        self.app.route("/api/camera/capture", methods=["POST"])(self._capture_still)

        # Mount endpoints
        self.app.route("/api/mount/status", methods=["GET"])(self._mount_status)
        self.app.route("/api/mount/tracking", methods=["POST"])(self._mount_tracking)

        # Session endpoints
        self.app.route("/api/session/status", methods=["GET"])(self._session_status)
        self.app.route("/api/session/start", methods=["POST"])(self._start_session)
        self.app.route("/api/session/stop", methods=["POST"])(self._stop_session)
        self.app.route("/api/session/config", methods=["GET"])(self._get_session_config)
        self.app.route("/api/session/config", methods=["POST"])(self._save_session_config)

        # Captures
        self.app.route("/api/captures", methods=["GET"])(self._list_captures)
        self.app.route("/api/captures/folders", methods=["GET"])(self._list_capture_folders)
        self.app.route("/api/captures/<path:filename>", methods=["GET"])(self._serve_capture)

    # ------------------------------------------------------------------
    # Camera handlers
    # ------------------------------------------------------------------
    def _camera_status(self):
        try:
            return success_response(build_camera_status_payload(self.camera), message="Camera status retrieved")
        except Exception as exc:
            logger.exception("Failed to retrieve camera status")
            return error_response(
                code="STATUS_ERROR",
                message=str(exc),
                http_status=500,
            )

    def _update_camera_settings(self):
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return error_response(
                code="INVALID_REQUEST",
                message="Request body must be valid JSON",
                http_status=400,
            )

        try:
            updates_applied: List[str] = []

            exposure_seconds = payload.get("exposure_seconds")
            iso_value = payload.get("iso")

            exposure_us: Optional[int] = None
            gain: Optional[float] = None

            if exposure_seconds is not None:
                exposure_seconds = float(exposure_seconds)
                if exposure_seconds <= 0:
                    raise ValueError("exposure_seconds must be greater than 0")
                exposure_us = int(exposure_seconds * 1_000_000)
                updates_applied.append("exposure_seconds")

            if iso_value is not None:
                iso_value = float(iso_value)
                if iso_value <= 0:
                    raise ValueError("iso must be greater than 0")
                gain = self.camera.iso_to_gain(iso_value)
                updates_applied.append("iso")

            if exposure_us is not None or gain is not None:
                self.camera.set_exposure_us(
                    exposure_us if exposure_us is not None else self.camera.get_exposure_us(),
                    gain,
                )

            if "night_vision_mode" in payload:
                self.camera.night_vision_mode = bool(payload["night_vision_mode"])
                updates_applied.append("night_vision_mode")

            if "night_vision_intensity" in payload:
                intensity = float(payload["night_vision_intensity"])
                self.camera.night_vision_intensity = max(1.0, min(80.0, intensity))
                updates_applied.append("night_vision_intensity")

            if "save_raw" in payload:
                self.camera.save_raw = bool(payload["save_raw"])
                updates_applied.append("save_raw")

            if "skip_frames" in payload:
                self.camera.skip_frames = int(payload["skip_frames"])
                updates_applied.append("skip_frames")

            self.camera.update_camera_settings()

            broadcast_camera_update(self.camera)

            return success_response(
                {
                    "updates": updates_applied,
                    "exposure_seconds": self._safe_camera_call("get_exposure_seconds", default=0.0),
                    "iso": self._safe_camera_call("gain_to_iso", self.camera.gain),
                },
                message="Camera settings updated",
            )
        except ValueError as validation_error:
            return error_response(
                code="VALIDATION_ERROR",
                message=str(validation_error),
                http_status=400,
            )
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception("Failed to update camera settings")
            return error_response(
                code="SETTINGS_ERROR",
                message=str(exc),
                http_status=500,
            )

    def _capture_still(self):
        try:
            # Emit capture_start event before beginning capture
            broadcast_capture_event("capture_start", {
                "capture_status": "Capturing",
                "recording": True
            })
            
            # Run blocking camera capture in thread pool to avoid blocking eventlet
            # Timeout based on exposure time + 30 second buffer
            exposure = getattr(self.camera, "exposure_seconds", 1.0)
            timeout = max(exposure + 30, 60)  # At least 60 seconds
            future = self._executor.submit(self.camera.capture_still)
            success = future.result(timeout=timeout)

            if not success:
                return error_response(
                    code="CAPTURE_FAILED",
                    message="Unable to capture image",
                    http_status=500,
                )

            data = {
                "capture_status": getattr(self.camera, "capture_status", "Completed"),
                "recording": getattr(self.camera, "recording", False),
            }
            broadcast_capture_event("capture_complete", data)
            return success_response(data, message="Capture complete")
        except Exception as exc:
            logger.exception("Capture still failed")
            broadcast_capture_event("capture_error", {"error": str(exc)})
            return error_response(
                code="CAPTURE_ERROR",
                message=str(exc),
                http_status=500,
            )

    # ------------------------------------------------------------------
    # Mount handlers
    # ------------------------------------------------------------------
    def _mount_status(self):
        data = build_mount_status_payload(self.mount)
        return success_response(data, message="Mount status retrieved")

    def _mount_tracking(self):
        payload = request.get_json(silent=True) or {}
        action = payload.get("action")

        if action not in {"start", "stop"}:
            return error_response(
                code="INVALID_ACTION",
                message="action must be either 'start' or 'stop'",
                http_status=400,
            )

        try:
            if action == "start":
                if "speed" in payload or "direction" in payload:
                    self.mount.update_settings(
                        speed=payload.get("speed"),
                        direction=self._normalize_direction(payload.get("direction")),
                    )
                self.mount.start_tracking()
                broadcast_mount_event("tracking_start", build_mount_status_payload(self.mount))
            else:
                self.mount.stop_tracking()
                broadcast_mount_event("tracking_stop", build_mount_status_payload(self.mount))

            return success_response(
                {
                    "status": getattr(self.mount, "status", "Unknown"),
                    "tracking": getattr(self.mount, "tracking", False),
                },
                message="Tracking action applied",
            )
        except Exception as exc:
            logger.exception("Mount tracking action failed")
            broadcast_mount_event("mount_error", {"error": str(exc)})
            return error_response(
                code="MOUNT_ERROR",
                message=str(exc),
                http_status=500,
            )

    # ------------------------------------------------------------------
    # Session handlers
    # ------------------------------------------------------------------
    def _session_status(self):
        try:
            status = self.session_controller.get_session_status()
            # Transform backend format to frontend format
            frontend_status = {
                "active": status.get("running", False),
                "name": status.get("name", ""),
                "total_images": status.get("total_images", 0),
                "captured_images": status.get("images_captured", 0),
                "remaining_time": self._calculate_remaining_time(status),
            }
            # Include any additional fields
            for key, value in status.items():
                if key not in frontend_status:
                    frontend_status[key] = value
            return success_response(frontend_status, message="Session status retrieved")
        except Exception as exc:
            logger.exception("Failed to retrieve session status")
            return error_response(
                code="SESSION_STATUS_ERROR",
                message=str(exc),
                http_status=500,
            )

    def _start_session(self):
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return error_response(
                code="INVALID_REQUEST",
                message="Request body must be valid JSON",
                http_status=400,
            )

        try:
            name = str(payload.get("name", "")).strip()
            total_images = payload.get("total_images")
            use_current_settings = bool(payload.get("use_current_settings", False))
            enable_tracking = bool(payload.get("enable_tracking", False))
            total_time_hours = payload.get("total_time_hours")

            if not name:
                raise ValueError("Session name is required")

            if total_images is None:
                raise ValueError("total_images is required")

            total_images = int(total_images)
            if total_images <= 0:
                raise ValueError("total_images must be greater than 0")

            if total_time_hours is not None:
                total_time_hours = float(total_time_hours)
                if total_time_hours <= 0:
                    raise ValueError("total_time_hours must be greater than 0")
            else:
                total_time_hours = None

            success = self.session_controller.start_session(
                name=name,
                total_images=total_images,
                use_current_settings=use_current_settings,
                enable_tracking=enable_tracking,
                total_time_hours=total_time_hours,
            )

            if not success:
                return error_response(
                    code="SESSION_START_FAILED",
                    message="Failed to start capture session",
                    http_status=500,
                )

            return success_response(
                {
                    "session_status": self.session_controller.get_session_status(),
                },
                message="Session started",
            )
        except ValueError as validation_error:
            return error_response(
                code="VALIDATION_ERROR",
                message=str(validation_error),
                http_status=400,
            )
        except Exception as exc:
            logger.exception("Failed to start session")
            return error_response(
                code="SESSION_START_ERROR",
                message=str(exc),
                http_status=500,
            )

    def _stop_session(self):
        try:
            success = self.session_controller.stop_session()
            if not success:
                return error_response(
                    code="SESSION_STOP_FAILED",
                    message="Failed to stop capture session",
                    http_status=500,
                )

            return success_response(
                {
                    "session_status": self.session_controller.get_session_status(),
                },
                message="Session stopped",
            )
        except Exception as exc:
            logger.exception("Failed to stop session")
            return error_response(
                code="SESSION_STOP_ERROR",
                message=str(exc),
                http_status=500,
            )

    def _get_session_config(self):
        """Get saved session configuration."""
        try:
            capture_dir = getattr(self.camera, "capture_dir", "captures")
            if not os.path.isabs(capture_dir):
                capture_dir = os.path.abspath(os.path.expanduser(capture_dir))
            
            config_path = os.path.join(capture_dir, "session_config.json")
            
            if not os.path.exists(config_path):
                return success_response({}, message="No saved session config")
            
            with open(config_path, "r") as f:
                config = json.load(f)
            
            return success_response(config, message="Session config retrieved")
        except json.JSONDecodeError as exc:
            logger.exception("Failed to parse session config")
            return error_response(
                code="CONFIG_PARSE_ERROR",
                message=f"Invalid config file format: {str(exc)}",
                http_status=500,
            )
        except Exception as exc:
            logger.exception("Failed to retrieve session config")
            return error_response(
                code="CONFIG_ERROR",
                message=str(exc),
                http_status=500,
            )

    def _save_session_config(self):
        """Save session configuration."""
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return error_response(
                code="INVALID_REQUEST",
                message="Request body must be valid JSON",
                http_status=400,
            )

        try:
            capture_dir = getattr(self.camera, "capture_dir", "captures")
            if not os.path.isabs(capture_dir):
                capture_dir = os.path.abspath(os.path.expanduser(capture_dir))
            
            # Ensure capture directory exists
            os.makedirs(capture_dir, exist_ok=True)
            
            config_path = os.path.join(capture_dir, "session_config.json")
            
            # Validate and sanitize config data
            config = {
                "name": str(payload.get("name", "")).strip(),
                "totalImages": int(payload.get("totalImages", 10)),
                "enableTracking": bool(payload.get("enableTracking", False)),
                "useCurrentSettings": bool(payload.get("useCurrentSettings", True)),
                "sessionMode": str(payload.get("sessionMode", "timed")),
                "totalTimeHours": payload.get("totalTimeHours"),
            }
            
            # Validate sessionMode
            if config["sessionMode"] not in ["rapid", "timed"]:
                raise ValueError("sessionMode must be 'rapid' or 'timed'")
            
            # Validate totalImages
            if config["totalImages"] <= 0:
                raise ValueError("totalImages must be greater than 0")
            
            # Validate totalTimeHours for timed mode
            if config["sessionMode"] == "timed":
                if config["totalTimeHours"] is None:
                    raise ValueError("totalTimeHours is required for timed mode")
                total_time_hours = float(config["totalTimeHours"])
                if total_time_hours <= 0:
                    raise ValueError("totalTimeHours must be greater than 0")
                config["totalTimeHours"] = total_time_hours
            else:
                config["totalTimeHours"] = None
            
            # Save config to file
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)
            
            return success_response(config, message="Session config saved")
        except ValueError as validation_error:
            return error_response(
                code="VALIDATION_ERROR",
                message=str(validation_error),
                http_status=400,
            )
        except Exception as exc:
            logger.exception("Failed to save session config")
            return error_response(
                code="CONFIG_SAVE_ERROR",
                message=str(exc),
                http_status=500,
            )

    # ------------------------------------------------------------------
    # Capture listing
    # ------------------------------------------------------------------
    def _list_captures(self):
        capture_dir = getattr(self.camera, "capture_dir", "captures")
        
        # Convert relative path to absolute path
        if not os.path.isabs(capture_dir):
            capture_dir = os.path.abspath(os.path.expanduser(capture_dir))
        
        # Check for folder query parameter
        folder = request.args.get("folder")
        if folder:
            # Sanitize folder name to prevent directory traversal
            folder = os.path.basename(folder)
            capture_dir = os.path.join(capture_dir, folder)
        
        try:
            if not os.path.exists(capture_dir):
                files = []
            else:
                # List only files, not directories, sorted by modification time (newest first)
                files_with_time = []
                for f in os.listdir(capture_dir):
                    file_path = os.path.join(capture_dir, f)
                    if os.path.isfile(file_path):
                        mtime = os.path.getmtime(file_path)
                        files_with_time.append((f, mtime))
                
                # Sort by modification time descending (newest first)
                files_with_time.sort(key=lambda x: x[1], reverse=True)
                files = [f[0] for f in files_with_time]
        except FileNotFoundError:
            files = []
        except Exception as exc:
            logger.exception("Failed to list captures")
            return error_response(
                code="CAPTURE_LIST_ERROR",
                message=str(exc),
                http_status=500,
            )

        return success_response({"files": files}, message="Capture list retrieved")

    def _list_capture_folders(self):
        """List all sub-folders in the captures directory."""
        capture_dir = getattr(self.camera, "capture_dir", "captures")
        
        # Convert relative path to absolute path
        if not os.path.isabs(capture_dir):
            capture_dir = os.path.abspath(os.path.expanduser(capture_dir))
        
        try:
            if not os.path.exists(capture_dir):
                folders = []
            else:
                # List only directories, not files
                folders = [
                    f for f in os.listdir(capture_dir)
                    if os.path.isdir(os.path.join(capture_dir, f))
                ]
                folders = sorted(folders)
        except Exception as exc:
            logger.exception("Failed to list capture folders")
            return error_response(
                code="FOLDER_LIST_ERROR",
                message=str(exc),
                http_status=500,
            )

        return success_response({"folders": folders}, message="Capture folders retrieved")

    def _serve_capture(self, filename):
        """Serve a single capture file."""
        from flask import send_from_directory
        capture_dir = getattr(self.camera, "capture_dir", "captures")
        
        # Convert relative path to absolute path
        if not os.path.isabs(capture_dir):
            # If relative, resolve it relative to the application root
            # Assuming the app runs from /home/admin/wanda-telescope
            capture_dir = os.path.abspath(os.path.expanduser(capture_dir))
        
        # Check if filename contains a folder path (e.g., "session_name/image_0001.jpg")
        if "/" in filename:
            parts = filename.split("/", 1)
            folder = os.path.basename(parts[0])  # Sanitize folder name
            filename = parts[1]
            capture_dir = os.path.join(capture_dir, folder)
        
        try:
            return send_from_directory(capture_dir, filename)
        except FileNotFoundError:
            return error_response(
                code="FILE_NOT_FOUND",
                message=f"Capture file not found: {filename}",
                http_status=404,
            )
        except Exception as exc:
            logger.exception("Failed to serve capture file")
            return error_response(
                code="SERVE_ERROR",
                message=str(exc),
                http_status=500,
            )

    # ------------------------------------------------------------------
    # Video feed (unchanged behaviour)
    # ------------------------------------------------------------------
    def _video_feed(self):
        def generate():
            while True:
                try:
                    frame_data = self.camera.get_frame()
                    if frame_data is not None:
                        yield (
                            b"--frame\r\n"
                            b"Content-Type: image/jpeg\r\n\r\n" + frame_data + b"\r\n"
                        )
                    else:
                        yield (
                            b"--frame\r\n"
                            b"Content-Type: image/jpeg\r\n\r\n" + b"" + b"\r\n"
                        )
                except Exception as exc:  # pragma: no cover - generator resilience
                    logger.error("Video feed error: %s", exc)
                    break
                time.sleep(0.1)

        return Response(
            generate(),
            mimetype="multipart/x-mixed-replace; boundary=frame",
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _safe_camera_call(self, attr: str, *args: Any, default: Any = None) -> Any:
        method = getattr(self.camera, attr, None)
        if callable(method):
            try:
                return method(*args)  # type: ignore[misc]
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.warning("Camera call %s failed: %s", attr, exc)
        return default

    def _calculate_remaining_time(self, status: Dict[str, Any]) -> float:
        """Calculate remaining time in hours for the session."""
        total_time_hours = status.get("total_time_hours")
        if not total_time_hours or not status.get("start_time"):
            return 0.0
        
        try:
            start_time = datetime.fromisoformat(status["start_time"])
            elapsed_seconds = (datetime.now() - start_time).total_seconds()
            elapsed_hours = elapsed_seconds / 3600
            remaining = max(0.0, total_time_hours - elapsed_hours)
            return remaining
        except (ValueError, KeyError, TypeError):
            return 0.0

    @staticmethod
    def _normalize_direction(direction: Any) -> Optional[bool]:
        if direction is None:
            return None
        if isinstance(direction, bool):
            return direction
        if isinstance(direction, str):
            lowered = direction.strip().lower()
            if lowered in {"cw", "clockwise"}:
                return True
            if lowered in {"ccw", "counterclockwise", "counter-clockwise"}:
                return False
        return None

    def _handle_session_event(self, event_name: str, payload: Dict[str, Any]):
        # Transform payload format for frontend compatibility
        if isinstance(payload, dict) and "running" in payload:
            transformed_payload = payload.copy()
            transformed_payload["active"] = payload.get("running", False)
            if "images_captured" in payload:
                transformed_payload["captured_images"] = payload["images_captured"]
            if "remaining_time" not in transformed_payload:
                transformed_payload["remaining_time"] = self._calculate_remaining_time(payload)
            payload = transformed_payload
        
        if event_name == "session_progress":
            broadcast_session_event("session_progress", payload)
        elif event_name == "session_complete":
            broadcast_session_event("session_complete", payload)
        elif event_name == "session_error":
            broadcast_session_event("session_error", payload)
        elif event_name == "session_start":
            broadcast_session_event("session_start", payload)
        elif event_name == "session_stop":
            broadcast_session_event("session_stop", payload)


def build_camera_status_payload(camera) -> Dict[str, Any]:
    return {
        "mode": getattr(camera, "mode", "still"),
        "capture_status": getattr(camera, "capture_status", "Idle"),
        "recording": getattr(camera, "recording", False),
        "iso": getattr(camera, "gain", 0.0) and camera.gain_to_iso(camera.gain),
        "gain": getattr(camera, "gain", 0.0),
        "exposure_seconds": getattr(camera, "get_exposure_seconds", lambda: 0.0)(),
        "night_vision_mode": getattr(camera, "night_vision_mode", False),
        "night_vision_intensity": getattr(camera, "night_vision_intensity", 0.0),
        "save_raw": getattr(camera, "save_raw", False),
        "skip_frames": getattr(camera, "skip_frames", 0),
    }


def build_mount_status_payload(mount) -> Dict[str, Any]:
    return {
        "status": getattr(mount, "status", "Unknown"),
        "tracking": getattr(mount, "tracking", False),
        "direction": getattr(mount, "direction", True),
        "speed": getattr(mount, "speed", 0.0),
    }


def broadcast_camera_update(camera):
    if socketio:
        socketio.emit("status", build_camera_status_payload(camera), namespace="/ws/camera")


def broadcast_capture_event(event: str, payload: Dict[str, Any]):
    if socketio:
        socketio.emit(event, payload, namespace="/ws/camera")


def broadcast_mount_event(event: str, payload: Dict[str, Any]):
    if socketio:
        socketio.emit(event, payload, namespace="/ws/mount")


def broadcast_session_event(event: str, payload: Dict[str, Any]):
    if socketio:
        socketio.emit(event, payload, namespace="/ws/session")