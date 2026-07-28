# Scripts

This directory contains deterministic utilities for the sanitized public architecture model:

- [`validate-architecture.sh`](validate-architecture.sh) validates the canonical DSL with `structurizr/structurizr:2026.06.28-noble`, exports it to temporary compiled Structurizr JSON, checks repository semantic invariants against that JSON, and removes the JSON after validation. [`validate-architecture-json.py`](validate-architecture-json.py) is the internal standard-library semantic checker; no compiled JSON is committed.
- [`render-architecture.sh`](render-architecture.sh) renders two dark-mode diagram previews with `structurizr/structurizr:2026.06.28-playwright`. Each preview is accompanied by an automatically generated key/legend SVG, producing four artifact files in total. The script verifies all output files and their boundaries.

Both scripts require Docker and Bash 4 or newer; `validate-architecture.sh` also requires Python 3. Local rendering additionally requires GNU/Linux or WSL, GNU findutils, and GNU coreutils. Stock macOS Bash 3.2 is unsupported. macOS users may run validation with a separately installed Bash 4+, while rendering should use a compatible GNU/Linux environment, such as a Linux container, virtual machine, or equivalent.

From the repository root, run:

```bash
bash scripts/validate-architecture.sh
bash scripts/render-architecture.sh
```

From another directory, invoke the scripts using the explicit absolute or relative path to the repository clone.

Generated SVGs under `build/architecture-svg/` are temporary local or CI preview outputs. They are not copied into the publication directory or committed automatically.

GitHub Actions uses Ubuntu and is the canonical automated validation and rendering environment. These scripts operate only on sanitized files in this public repository; no private repository access occurs.
