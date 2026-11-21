"""
Model Loader Service.
Lazily loads and caches the calibrated detector ensemble artifact.
Defaults to CPU execution; memory-safe for RTX 2050 (4 GB VRAM) if GPU is enabled.
"""

import os
import logging
from typing import Optional
from backend.app.core.config import settings
from backend.app.core.errors import DocumentProcessingException
from ml.src.models.baseline import FeatureClassifierPipeline

logger = logging.getLogger(__name__)


class ModelRegistry:
    _instance: Optional["ModelRegistry"] = None
    _pipeline: Optional[FeatureClassifierPipeline] = None

    def __new__(cls) -> "ModelRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_pipeline(self) -> FeatureClassifierPipeline:
        if self._pipeline is None:
            artifact_path = settings.MODEL_ARTIFACT_PATH
            if not os.path.exists(artifact_path):
                # Search up or resolve absolute path if running from different working dir
                alt_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..", artifact_path))
                if os.path.exists(alt_path):
                    artifact_path = alt_path
                else:
                    logger.error("Detector model artifact not found at: %s", artifact_path)
                    raise DocumentProcessingException(
                        status_code=500,
                        code="MODEL_ARTIFACT_NOT_FOUND",
                        message=f"Model artifact not found at {settings.MODEL_ARTIFACT_PATH}.",
                    )

            logger.info("Loading calibrated detector model artifact from %s", artifact_path)
            self._pipeline = FeatureClassifierPipeline.load(artifact_path)
            logger.info("Model pipeline loaded successfully.")

        return self._pipeline


model_registry = ModelRegistry()
