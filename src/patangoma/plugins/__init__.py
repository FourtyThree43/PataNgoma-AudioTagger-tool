"""PataNgoma Plugin Subsystem."""

from patangoma.plugins.capabilities import CapabilityRegistry
from patangoma.plugins.contracts import (
    ArtworkProviderPlugin,
    DownloadBackendPlugin,
    ExporterPlugin,
    ImporterPlugin,
    LyricsProviderPlugin,
    MediaToolPlugin,
    MetadataProviderPlugin,
    Plugin,
    PluginCapability,
)
from patangoma.plugins.discovery import create_default_plugin_registry
from patangoma.plugins.registry import PluginRegistry

__all__ = [
    "ArtworkProviderPlugin",
    "CapabilityRegistry",
    "DownloadBackendPlugin",
    "ExporterPlugin",
    "ImporterPlugin",
    "LyricsProviderPlugin",
    "MediaToolPlugin",
    "MetadataProviderPlugin",
    "Plugin",
    "PluginCapability",
    "PluginRegistry",
    "create_default_plugin_registry",
]
