"""Capability-oriented query and routing layer over PluginRegistry."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from patangoma.plugins.contracts import (
    ArtworkProviderPlugin,
    DownloadBackendPlugin,
    ExporterPlugin,
    ImporterPlugin,
    LyricsProviderPlugin,
    MediaToolPlugin,
    MetadataProviderPlugin,
    PluginCapability,
)

if TYPE_CHECKING:
    from patangoma.plugins.registry import PluginRegistry


class CapabilityRegistry:
    """Provides strongly-typed capability lookups and query interfaces."""

    def __init__(self, registry: PluginRegistry) -> None:
        self._registry = registry

    # -------------------------------------------------------------------------
    # Metadata Providers
    # -------------------------------------------------------------------------

    def get_metadata_provider(self, name: str) -> MetadataProviderPlugin | None:
        """Retrieve a metadata provider plugin by identifier."""
        plugin = self._registry.get(name)
        if plugin and PluginCapability.METADATA in plugin.capabilities:
            return cast(MetadataProviderPlugin, plugin)
        return None

    def get_metadata_provider_strict(self, name: str) -> MetadataProviderPlugin:
        """Retrieve a metadata provider or raise PluginNotFoundError."""
        plugin = self._registry.get_strict(name)
        return cast(MetadataProviderPlugin, plugin)

    def list_metadata_providers(self) -> list[MetadataProviderPlugin]:
        """List all active metadata provider plugins."""
        return [
            cast(MetadataProviderPlugin, p)
            for p in self._registry.get_by_capability(PluginCapability.METADATA)
        ]

    # -------------------------------------------------------------------------
    # Download Backends
    # -------------------------------------------------------------------------

    def get_download_backend(self, name: str) -> DownloadBackendPlugin | None:
        """Retrieve a download backend plugin by identifier."""
        plugin = self._registry.get(name)
        if plugin and PluginCapability.DOWNLOAD in plugin.capabilities:
            return cast(DownloadBackendPlugin, plugin)
        return None

    def list_download_backends(self) -> list[DownloadBackendPlugin]:
        """List all active download backend plugins."""
        return [
            cast(DownloadBackendPlugin, p)
            for p in self._registry.get_by_capability(PluginCapability.DOWNLOAD)
        ]

    # -------------------------------------------------------------------------
    # Media Tools
    # -------------------------------------------------------------------------

    def get_media_tool(self, name: str) -> MediaToolPlugin | None:
        """Retrieve a media tool plugin by identifier."""
        plugin = self._registry.get(name)
        if plugin and PluginCapability.MEDIA_TOOL in plugin.capabilities:
            return cast(MediaToolPlugin, plugin)
        return None

    def list_media_tools(self) -> list[MediaToolPlugin]:
        """List all active media tool plugins."""
        return [
            cast(MediaToolPlugin, p)
            for p in self._registry.get_by_capability(PluginCapability.MEDIA_TOOL)
        ]

    # -------------------------------------------------------------------------
    # Artwork Providers
    # -------------------------------------------------------------------------

    def get_artwork_provider(self, name: str) -> ArtworkProviderPlugin | None:
        """Retrieve an artwork provider plugin by identifier."""
        plugin = self._registry.get(name)
        if plugin and PluginCapability.ARTWORK in plugin.capabilities:
            return cast(ArtworkProviderPlugin, plugin)
        return None

    def list_artwork_providers(self) -> list[ArtworkProviderPlugin]:
        """List all active artwork provider plugins."""
        return [
            cast(ArtworkProviderPlugin, p)
            for p in self._registry.get_by_capability(PluginCapability.ARTWORK)
        ]

    # -------------------------------------------------------------------------
    # Lyrics Providers
    # -------------------------------------------------------------------------

    def get_lyrics_provider(self, name: str) -> LyricsProviderPlugin | None:
        """Retrieve a lyrics provider plugin by identifier."""
        plugin = self._registry.get(name)
        if plugin and PluginCapability.LYRICS in plugin.capabilities:
            return cast(LyricsProviderPlugin, plugin)
        return None

    def list_lyrics_providers(self) -> list[LyricsProviderPlugin]:
        """List all active lyrics provider plugins."""
        return [
            cast(LyricsProviderPlugin, p)
            for p in self._registry.get_by_capability(PluginCapability.LYRICS)
        ]

    # -------------------------------------------------------------------------
    # Exporters & Importers
    # -------------------------------------------------------------------------

    def get_exporter(self, format_name: str) -> ExporterPlugin | None:
        """Retrieve an exporter plugin by supported format name."""
        for plugin in self._registry.get_by_capability(PluginCapability.EXPORTER):
            exp = cast(ExporterPlugin, plugin)
            if (
                hasattr(exp, "format_name")
                and exp.format_name.lower() == format_name.lower()
            ):
                return exp
        return None

    def list_exporters(self) -> list[ExporterPlugin]:
        """List all active exporter plugins."""
        return [
            cast(ExporterPlugin, p)
            for p in self._registry.get_by_capability(PluginCapability.EXPORTER)
        ]

    def get_importer(self, format_name: str) -> ImporterPlugin | None:
        """Retrieve an importer plugin by supported format name."""
        for plugin in self._registry.get_by_capability(PluginCapability.IMPORTER):
            imp = cast(ImporterPlugin, plugin)
            if (
                hasattr(imp, "format_name")
                and imp.format_name.lower() == format_name.lower()
            ):
                return imp
        return None

    def list_importers(self) -> list[ImporterPlugin]:
        """List all active importer plugins."""
        return [
            cast(ImporterPlugin, p)
            for p in self._registry.get_by_capability(PluginCapability.IMPORTER)
        ]
