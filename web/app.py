"""
Web application for Wanda astrophotography system.
Provides a REST API and MJPEG video feed for the Next.js frontend.
"""
import logging
import os
import time
from typing import Any, Dict, List, Optional, Sequence

from flask import Flask, Response, request
from flask_cors import CORS

import config
from camera import CameraFactory  # noqa: F401 (retained for backward compatibility)
from mount.controller import MountController
from session import SessionController

from .api_responses import error_response, success_response

logger = logging.getLogger(__name__)


class WandaApp:
    """Flask application exposing REST endpoints for the Wanda system."""

    def __init__(self, camera=None, *, cors_origins: Optional[Sequence[str]] = None):
        if camera is None:
            raise ValueError("Camera instance is required")

        self.camera = camera
        self.mount = MountController()
        self.session_controller = SessionController(
            self.camera, self.mount, self.camera.capture_dir
        )

        self.app = Flask(__name__)

        self._cors_origins = list(cors_origins) if cors_origins else ["http://localhost:3000"]
        CORS(self.app, origins=self._cors_origins)

        @self.app.after_request
        def _inject_default_cors_headers(response):  # type: ignore[override]
            if self._cors_origins:
                response.headers.setdefault("Access-Control-Allow-Origin", self._cors_origins[0])
                response.headers.setdefault("Access-Control-Allow-Headers", "Content-Type")
                response.headers.setdefault("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
            return response

        self._register_routes()
        logger.info("REST web application initialized")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self):
        """Run the web application."""
        try:
            logger.info("Starting web server on %s:%s", config.HOST, config.PORT)
            self.app.run(host=config.HOST, port=config.PORT, threaded=True)
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

        # Captures
        self.app.route("/api/captures", methods=["GET"])(self._list_captures)

    # ------------------------------------------------------------------
    # Camera handlers
    # ------------------------------------------------------------------
    def _camera_status(self):
        try:
            data = {
                "mode": getattr(self.camera, "mode", "still"),
                "capture_status": getattr(self.camera, "capture_status", "Idle"),
                "recording": getattr(self.camera, "recording", False),
                "iso": self._safe_camera_call("gain_to_iso", self.camera.gain),
                "gain": getattr(self.camera, "gain", 0.0),
                "exposure_seconds": self._safe_camera_call("get_exposure_seconds", default=0.0),
                "night_vision_mode": getattr(self.camera, "night_vision_mode", False),
                "night_vision_intensity": getattr(self.camera, "night_vision_intensity", 0.0),
                "save_raw": getattr(self.camera, "save_raw", False),
                "skip_frames": getattr(self.camera, "skip_frames", 0),
            }
            return success_response(data, message="Camera status retrieved")
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
            success = self.camera.capture_still()

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
            return success_response(data, message="Capture complete")
        except Exception as exc:
            logger.exception("Capture still failed")
            return error_response(
                code="CAPTURE_ERROR",
                message=str(exc),
                http_status=500,
            )

    # ------------------------------------------------------------------
    # Mount handlers
    # ------------------------------------------------------------------
    def _mount_status(self):
        data = {
            "status": getattr(self.mount, "status", "Unknown"),
            "tracking": getattr(self.mount, "tracking", False),
            "direction": getattr(self.mount, "direction", True),
            "speed": getattr(self.mount, "speed", 0.0),
        }
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
            else:
                self.mount.stop_tracking()

            return success_response(
                {
                    "status": getattr(self.mount, "status", "Unknown"),
                    "tracking": getattr(self.mount, "tracking", False),
                },
                message="Tracking action applied",
            )
        except Exception as exc:
            logger.exception("Mount tracking action failed")
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
            return success_response(status, message="Session status retrieved")
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

    # ------------------------------------------------------------------
    # Capture listing
    # ------------------------------------------------------------------
    def _list_captures(self):
        capture_dir = getattr(self.camera, "capture_dir", "captures")
        try:
            files = sorted(os.listdir(capture_dir))
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