"""Plugins package providing capability contracts, registry, and discovery."""

from patangoma.plugins.contracts import (
    ArtworkProviderPlugin,
    DownloadBackendPlugin,
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
    "DownloadBackendPlugin",
    "LyricsProviderPlugin",
    "MediaToolPlugin",
    "MetadataProviderPlugin",
    "Plugin",
    "PluginCapability",
    "PluginRegistry",
    "create_default_plugin_registry",
]
