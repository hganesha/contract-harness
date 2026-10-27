"""Lovable Contract Alignment Harness.

An open, dependency-light pipeline that turns:

  requirements + business rules + target contracts
  + a Lovable-generated UI codebase (dummy data)

into:

  discovered UI contracts -> alignment matrix -> change specs -> migration plan

Everything deterministic works offline with the Python standard library only.
An optional LLM adapter (any OpenAI-compatible endpoint, incl. local Ollama)
can enrich narrative sections; it is never required.
"""

__version__ = "1.0.0"
