"""
Auto-discovery of Rule subclasses under src/rules/...

Add a new rule by placing a .py file with a Rule subclass in the right
folder. No importer list edit. Online CLI and offline Docker both pick it
up when src/ is mounted (default) or after image rebuild.
"""
from __future__ import annotations

import importlib
import logging
import pkgutil
from pathlib import Path
from typing import Iterable, List, Set, Type

from src.core.rule_base import Rule, RuleRegistry

logger = logging.getLogger(__name__)


def discover_rule_classes(package_name: str) -> List[Type[Rule]]:
    """Return Rule subclasses defined in modules under *package_name*."""
    found: List[Type[Rule]] = []
    seen_cls: Set[type] = set()

    def _collect_from_module(mod) -> None:
        for attr in dir(mod):
            obj = getattr(mod, attr, None)
            if not isinstance(obj, type):
                continue
            if obj is Rule or not issubclass(obj, Rule):
                continue
            if getattr(obj, "__module__", None) != mod.__name__:
                continue
            if obj in seen_cls:
                continue
            seen_cls.add(obj)
            found.append(obj)

    try:
        pkg = importlib.import_module(package_name)
    except ImportError as exc:
        logger.debug("Package not importable: %s (%s)", package_name, exc)
        return found

    paths = getattr(pkg, "__path__", None)
    module_names = []
    if paths:
        for mod_info in pkgutil.iter_modules(paths, prefix=package_name + "."):
            if mod_info.ispkg:
                continue
            module_names.append(mod_info.name)
        for p in paths:
            for py in Path(p).glob("*.py"):
                if py.name.startswith("_"):
                    continue
                name = f"{package_name}.{py.stem}"
                if name not in module_names:
                    module_names.append(name)

    for name in module_names:
        try:
            mod = importlib.import_module(name)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Skip rule module %s: %s", name, exc)
            continue
        _collect_from_module(mod)

    return found


def register_packages(
    registry: RuleRegistry,
    packages: Iterable[str],
    *,
    already: Set[str] | None = None,
) -> int:
    """Discover and register Rule subclasses; dedupe by rule.name."""
    seen: Set[str] = already if already is not None else set()
    for r in registry.all():
        seen.add(r.name)

    count = 0
    for package_name in packages:
        for cls in discover_rule_classes(package_name):
            try:
                instance = cls()
            except Exception as exc:  # noqa: BLE001
                logger.warning("Cannot instantiate %s: %s", cls, exc)
                continue
            key = instance.name or cls.__name__
            if key in seen:
                continue
            seen.add(key)
            registry.register(instance)
            count += 1
            logger.debug("Registered rule %s (%s)", key, cls.__module__)
    return count
