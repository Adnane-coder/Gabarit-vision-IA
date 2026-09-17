class AppError(Exception):
    """Base class for errors that should be surfaced as structured API errors."""

    code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred."
    status_code: int = 500

    def __init__(self, message: str | None = None):
        self.message = message or self.message
        super().__init__(self.message)


class CameraUnavailableError(AppError):
    code = "CAMERA_UNAVAILABLE"
    message = "Camera service is currently unavailable."
    status_code = 503


class CameraCaptureError(AppError):
    code = "CAMERA_CAPTURE_FAILED"
    message = "Failed to capture an image from the camera."
    status_code = 502


class ModelUnavailableError(AppError):
    code = "MODEL_UNAVAILABLE"
    message = "The inspection model is not available."
    status_code = 503


class InferenceError(AppError):
    code = "INFERENCE_FAILED"
    message = "Model inference failed."
    status_code = 502


class HardwareUnavailableError(AppError):
    code = "HARDWARE_UNAVAILABLE"
    message = "Required hardware is not available."
    status_code = 503
