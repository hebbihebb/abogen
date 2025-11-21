"""
TTS backend factory and registry for Abogen.

This module provides a central registry for TTS engines and factory functions
to create engine instances based on configuration.
"""

import logging
from typing import Type, Optional, Dict, Any
from .base import TTSBackend, TTSResult
from .kokoro_backend import KokoroBackend
from .f5_tts_backend import F5TTSBackend

logger = logging.getLogger(__name__)

# Registry mapping engine names to their implementation classes
ENGINE_REGISTRY: Dict[str, Type[TTSBackend]] = {
    "kokoro": KokoroBackend,
    "f5_tts": F5TTSBackend,
}


def create_tts_engine(
    engine_name: str,
    lang_code: str,
    device: str = "cpu",
    **kwargs
) -> TTSBackend:
    """
    Factory function to create TTS engine instances.

    This is the main entry point for creating TTS backends. It handles
    engine selection, dependency checking, and provides helpful error
    messages if something goes wrong.

    Args:
        engine_name: Engine identifier ("kokoro", "f5_tts", etc.)
        lang_code: Language code (e.g., "a" for American English)
        device: Device to run on ("cpu", "cuda", "mps")
        **kwargs: Engine-specific configuration parameters

    Returns:
        Initialized TTS backend instance

    Raises:
        ValueError: If engine_name not recognized
        ImportError: If engine dependencies not installed
        RuntimeError: If engine initialization fails

    Example:
        >>> engine = create_tts_engine(
        ...     "kokoro",
        ...     lang_code="a",
        ...     device="cuda"
        ... )
        >>> for result in engine("Hello world", voice="af_heart", speed=1.0):
        ...     process_audio(result.audio)
    """
    if engine_name not in ENGINE_REGISTRY:
        available = ", ".join(ENGINE_REGISTRY.keys())
        raise ValueError(
            f"Unknown TTS engine '{engine_name}'.\n"
            f"Available engines: {available}\n"
            f"\n"
            f"To add a new engine, register it in ENGINE_REGISTRY."
        )

    engine_class = ENGINE_REGISTRY[engine_name]

    logger.info(f"Creating TTS engine: {engine_name}")

    try:
        return engine_class(lang_code=lang_code, device=device, **kwargs)
    except ImportError as e:
        # Provide helpful installation instructions
        install_instructions = {
            "kokoro": "pip install kokoro",
            "f5_tts": (
                "pip install f5-tts\n"
                "  Or from source: git clone https://github.com/SWivid/F5-TTS.git && "
                "cd F5-TTS && pip install -e ."
            ),
        }

        instruction = install_instructions.get(
            engine_name,
            f"pip install abogen[{engine_name}]"
        )

        raise ImportError(
            f"Failed to load '{engine_name}' TTS engine.\n"
            f"\n"
            f"Missing dependencies: {e}\n"
            f"\n"
            f"To fix, install the required packages:\n"
            f"  {instruction}\n"
        ) from e
    except Exception as e:
        logger.error(f"Failed to initialize {engine_name} engine: {e}")
        raise RuntimeError(
            f"Failed to initialize '{engine_name}' TTS engine: {e}"
        ) from e


def get_available_engines() -> list[str]:
    """
    Return list of engine names that can be loaded (have dependencies installed).

    This is useful for UI dropdowns or configuration validation - only show
    engines that are actually available on the current system.

    Returns:
        List of engine names (e.g., ["kokoro", "f5_tts"])

    Example:
        >>> engines = get_available_engines()
        >>> print(f"Available engines: {engines}")
        Available engines: ['kokoro']  # if F5-TTS not installed
    """
    available = []

    for name, engine_class in ENGINE_REGISTRY.items():
        try:
            # Check if dependencies are available
            if hasattr(engine_class, '_check_dependencies'):
                engine_class._check_dependencies()
            available.append(name)
        except ImportError:
            logger.debug(f"Engine '{name}' not available (missing dependencies)")

    return available


def get_engine_info(engine_name: str) -> Dict[str, Any]:
    """
    Get metadata about a specific engine.

    Args:
        engine_name: Engine identifier

    Returns:
        Dictionary with engine metadata (display_name, description, etc.)

    Raises:
        ValueError: If engine not found
    """
    if engine_name not in ENGINE_REGISTRY:
        raise ValueError(f"Unknown engine: {engine_name}")

    # Import constants for engine metadata
    try:
        from abogen.constants import ENGINE_CONFIGS
        if engine_name in ENGINE_CONFIGS:
            return ENGINE_CONFIGS[engine_name]
    except ImportError:
        pass

    # Fallback to basic info from class docstring
    engine_class = ENGINE_REGISTRY[engine_name]
    return {
        "display_name": engine_name.replace("_", " ").title(),
        "description": (engine_class.__doc__ or "").split("\n")[0],
        "class": engine_class.__name__,
    }


# Export public API
__all__ = [
    "TTSBackend",
    "TTSResult",
    "KokoroBackend",
    "F5TTSBackend",
    "create_tts_engine",
    "get_available_engines",
    "get_engine_info",
    "ENGINE_REGISTRY",
]
