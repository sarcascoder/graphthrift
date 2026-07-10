"""One-line GraphThrift instrumentation of a real Graphiti pipeline.

Verified end-to-end against graphiti-core + Neo4j (see docs/REAL_MODEL_RUN.md).

Prereqs:
    pip install "graphthrift[graphiti]"        # graphiti-core
    # a Neo4j on bolt://localhost:7687 (e.g. `docker run -p 7687:7687 -e NEO4J_AUTH=neo4j/testpassword123 neo4j:5.26`)
    # an LLM: either OpenAI (set OPENAI_API_KEY) or local Ollama (default here, key-free)

Run:
    python examples/graphiti_quickstart.py
"""
import asyncio
import os
from datetime import datetime, timezone

from graphiti_core import Graphiti
from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.llm_client.openai_client import OpenAIClient
from graphiti_core.llm_client.openai_generic_client import OpenAIGenericClient
from graphiti_core.nodes import EpisodeType

import graphthrift

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "testpassword123")
USE_OLLAMA = os.getenv("OPENAI_API_KEY") is None  # default to key-free local models

EPISODES = [
    "Alice joined Acme Corp as a staff engineer in January and started leading the Atlas project.",
    "Bob is a data scientist at Acme Corp who reports to Alice and prefers working in Python.",
]


def build_llm_and_embedder():
    if USE_OLLAMA:
        base = "http://localhost:11434/v1"
        llm = OpenAIGenericClient(
            config=LLMConfig(api_key="ollama", model="qwen2.5:3b", small_model="qwen2.5:0.5b", base_url=base)
        )
        embedder = OpenAIEmbedder(
            config=OpenAIEmbedderConfig(api_key="ollama", embedding_model="nomic-embed-text", base_url=base)
        )
    else:
        llm = OpenAIClient(config=LLMConfig(model="gpt-5.5", small_model="gpt-4.1-nano"))
        embedder = OpenAIEmbedder(config=OpenAIEmbedderConfig(embedding_model="text-embedding-3-small"))
    return llm, embedder


async def main():
    base_llm, embedder = build_llm_and_embedder()

    # >>> The one line: wrap Graphiti's LLM client with GraphThrift instrumentation. <<<
    trace = graphthrift.RunTrace(label="graphiti")
    llm = graphthrift.wrap(base_llm, trace=trace)

    g = Graphiti(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, llm_client=llm, embedder=embedder)
    try:
        await g.build_indices_and_constraints()
        for i, body in enumerate(EPISODES):
            await g.add_episode(
                name=f"ep{i+1}",
                episode_body=body,
                source_description="quickstart",
                reference_time=datetime.now(timezone.utc),
                source=EpisodeType.text,
            )

        s = trace.summary()
        print("GraphThrift metered the real Graphiti pipeline:")
        print(f"  LLM calls        : {s['total_llm_calls']}")
        print(f"  prompt tokens    : {s['prompt_tokens']}")
        print(f"  total latency ms : {s['total_latency_ms']}")
        print(f"  per stage        : { {k: v['calls'] for k, v in s['by_stage'].items()} }")
    finally:
        await g.close()


if __name__ == "__main__":
    asyncio.run(main())
