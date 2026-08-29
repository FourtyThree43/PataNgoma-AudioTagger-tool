"""AcoustID provider re-export bridge for backward compatibility."""

from patangoma.plugins.metadata.acoustid import (
    AcoustIDPlugin,
    AcoustIDProvider,
    find_fpcalc_binary,
    generate_chromaprint,
)

__all__ = [
    "AcoustIDPlugin",
    "AcoustIDProvider",
    "find_fpcalc_binary",
    "generate_chromaprint",
]
