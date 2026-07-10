"""Integrations. `wrap` is imported lazily to avoid a hard graphiti-core dep."""
from __future__ import annotations


def wrap(client, **kwargs):
    """Wrap a Graphiti LLMClient with GraphThrift instrumentation. See graphiti.wrap."""
    from graphthrift.integrations.graphiti import wrap as _wrap

    return _wrap(client, **kwargs)


__all__ = ["wrap"]
