"""插件注册中心。

提供全局注册表和装饰器，让用户可以通过字符串名查找插件实现。

用法::

    # 装饰器注册
    @register_plugin("writer", "my_writer")
    class MyWriter(BaseWriter): ...

    # 动态注册
    registry.register("writer", "my_writer", MyWriter)

    # 查找
    cls = registry.get("writer", "my_writer")
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_VALID_NAMESPACES = frozenset({
    "writer",
    "polisher",
    "style_analyzer",
    "typesetter",
    "image_generator",
    "renderer",
    "publisher",
})


class PluginRegistry:
    """分命名空间的插件注册表。"""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, type]] = {ns: {} for ns in _VALID_NAMESPACES}

    def register(self, namespace: str, name: str, cls: type) -> None:
        """注册一个插件实现。

        Args:
            namespace: 环节名称，如 "writer" / "typesetter" / "renderer"
            name: 插件名称，用于查找
            cls: 插件类
        """
        if namespace not in _VALID_NAMESPACES:
            raise ValueError(
                f"未知的插件命名空间 '{namespace}'，"
                f"可选值: {sorted(_VALID_NAMESPACES)}"
            )
        if name in self._store[namespace]:
            logger.warning(
                "插件 '%s/%s' 已存在，将被覆盖为 %s",
                namespace, name, cls.__name__,
            )
        self._store[namespace][name] = cls

    def get(self, namespace: str, name: str) -> type:
        """根据命名空间和名称查找插件类。

        Raises:
            KeyError: 插件未注册。
        """
        if namespace not in _VALID_NAMESPACES:
            raise ValueError(f"未知的插件命名空间 '{namespace}'")
        try:
            return self._store[namespace][name]
        except KeyError:
            available = list(self._store[namespace].keys()) or ["（无）"]
            raise KeyError(
                f"插件 '{namespace}/{name}' 未注册。"
                f"已注册: {', '.join(available)}"
            ) from None

    def list_plugins(self, namespace: str | None = None) -> dict[str, list[str]]:
        """列出已注册的插件。

        Args:
            namespace: 指定命名空间，None 返回全部。
        """
        if namespace:
            return {namespace: list(self._store.get(namespace, {}).keys())}
        return {ns: list(plugins.keys()) for ns, plugins in self._store.items()}

    def resolve(self, namespace: str, plugin: Any) -> Any:
        """解析插件参数：如果是字符串则从注册表查找并实例化，否则原样返回。"""
        if isinstance(plugin, str):
            cls = self.get(namespace, plugin)
            return cls()
        return plugin


# 全局注册表实例
registry = PluginRegistry()


def register_plugin(namespace: str, name: str):
    """装饰器：注册插件到全局注册表。

    用法::

        @register_plugin("writer", "my_writer")
        class MyWriter(BaseWriter): ...
    """
    def decorator(cls: type) -> type:
        registry.register(namespace, name, cls)
        return cls
    return decorator
