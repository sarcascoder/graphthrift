"""Realistic large system prompts for the demo pipeline.

Graphiti's real extraction/dedup prompts are large (instructions + few-shot
examples), often 1-2k tokens of *fixed* prefix sent on every call. Modeling that
here is what makes two optimizations bite in dollar terms:
  - EdgeBatcher: sends the big prefix ONCE instead of once per edge.
  - PromptCompressor: strips the prunable few-shot EXAMPLES block (a real,
    quality-neutral technique) to cut input tokens.
The EXAMPLES block is wrapped in markers the compressor recognizes.
"""
from __future__ import annotations

_INSTRUCTIONS = {
    "extract_nodes.extract_message": "You are an entity extraction system. Extract all salient entities (people, organizations, projects, technologies, dates) from the episode. Return typed entities with canonical names. Be precise and exhaustive; do not hallucinate entities not grounded in the text.",
    "dedupe_nodes.nodes": "You resolve whether newly extracted entity nodes are duplicates of existing graph nodes. Consider name variants, abbreviations, and aliases. Return a mapping of duplicates.",
    "extract_edges.edge": "You are a relationship extraction system. Extract factual (subject, predicate, object) triples that are explicitly supported by the episode. Use canonical predicate names in SCREAMING_SNAKE_CASE. Do not infer unstated relationships.",
    "dedupe_edges.resolve_edge": "You resolve whether an extracted edge duplicates an existing edge and whether it contradicts/invalidates any existing edge. Consider temporal validity. Return the resolution decision.",
    "extract_edges.extract_timestamps": "You extract the valid_at and invalid_at timestamps for a relationship based on the episode's temporal context. Return ISO-8601 dates or null.",
    "extract_nodes.extract_summaries_batch": "You write concise one-sentence summaries for entity nodes based on their mentions across episodes.",
}

# A big, prunable few-shot block (the same for every stage in the demo) — this is
# what the compressor removes. ~2k characters of 'examples'.
_EXAMPLES = "<<<EXAMPLES\n" + "\n".join(
    f"Example {i}: given episode text, the correct structured output follows the schema with "
    f"canonical names, correct types, and no hallucinated content; coreference and temporal "
    f"qualifiers handled as in case {i}."
    for i in range(1, 6)
) + "\n>>>"


def system_prompt(stage_prompt_name: str) -> str:
    instr = _INSTRUCTIONS.get(stage_prompt_name, "Follow the schema exactly and ground every output in the input.")
    return f"{instr}\n\n{_EXAMPLES}"
