"""Plugin registry for managing plugin lifecycle, discovery, and capabilities."""

from __future__ import annotations

from typing import Any

from patangoma.domain.exceptions import PluginNotFoundError
from patangoma.plugins.contracts import Plugin, PluginCapability


class PluginRegistry:
    """Central registry holding all loaded plugins and routing capability lookups."""

    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}
        self._enabled: dict[str, bool] = {}

    def register(self, plugin: Plugin) -> None:
        """Register a new plugin instance."""
        pid = plugin.id.lower().strip()
        plugin.initialize()
        self._plugins[pid] = plugin
        self._enabled[pid] = True

    def unregister(self, plugin_id: str) -> bool:
        """Unload and unregister a plugin."""
        pid = plugin_id.lower().strip()
        plugin = self._plugins.pop(pid, None)
        if plugin:
            plugin.shutdown()
            self._enabled.pop(pid, None)
            return True
        return False

    def get(self, plugin_id: str) -> Plugin | None:
        """Get plugin by ID if registered and enabled."""
        pid = plugin_id.lower().strip()
        if self._enabled.get(pid, False):
            return self._plugins.get(pid)
        return None

    def get_strict(self, plugin_id: str) -> Plugin:
        """Get plugin by ID or raise PluginNotFoundError."""
        plugin = self.get(plugin_id)
        if not plugin:
            available = ", ".join(self._plugins.keys())
            raise PluginNotFoundError(
                f"Plugin '{plugin_id}' not found or disabled. Available: {available}"
            )
        return plugin

    def get_by_capability(self, capability: PluginCapability) -> list[Plugin]:
        """Return all enabled plugins offering a specific capability."""
        matches = []
        for pid, plugin in self._plugins.items():
            if self._enabled.get(pid, False) and capability in plugin.capabilities:
                matches.append(plugin)
        return matches

    def list_plugins(self) -> list[Plugin]:
        """Return all registered plugins."""
        return list(self._plugins.values())

    def enable(self, plugin_id: str) -> None:
        """Enable an existing plugin."""
        pid = plugin_id.lower().strip()
        if pid in self._plugins:
            self._enabled[pid] = True

    def disable(self, plugin_id: str) -> None:
        """Disable a plugin without unregistering it."""
        pid = plugin_id.lower().strip()
        if pid in self._plugins:
            self._enabled[pid] = False

    def health_all(self) -> dict[str, dict[str, Any]]:
        """Run health checks on all registered plugins."""
        results: dict[str, dict[str, Any]] = {}
        for pid, plugin in self._plugins.items():
            try:
                results[pid] = plugin.health()
            except Exception as e:
                results[pid] = {
                    "status": "UNHEALTHY",
                    "error": str(e),
                    "enabled": self._enabled.get(pid, False),
                }
        return results
