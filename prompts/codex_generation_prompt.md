# Dataset Item Generation Prompt

Create one executable TR-CodeBench item for Python 3.11.

Requirements:

- Paraphrase the task; do not copy an existing statement verbatim.
- Provide a fixed function signature.
- Provide at least three public tests.
- Provide a sealed oracle path and a hidden-test generator hook.
- Record tags, difficulty, allowed imports, target complexity, and known alternative paradigms.
- Keep the item deterministic and free of network, filesystem, or third-party package dependencies.
