# Scripts

This directory contains deterministic utilities for the sanitized public architecture model:

- [`validate-architecture.sh`](validate-architecture.sh) validates the canonical DSL with `structurizr/structurizr:2026.06.28-noble`, then checks repository-specific view, status, tag, and style invariants.
- [`render-architecture.sh`](render-architecture.sh) renders two dark-mode diagram previews with `structurizr/structurizr:2026.06.28-playwright`. Each preview is accompanied by an automatically generated key/legend SVG, producing four artifact files in total. The script verifies all output files and their boundaries.

Docker is required for both scripts. Local rendering additionally requires GNU/Linux or WSL, Bash 4 or newer, GNU findutils, and GNU coreutils. Stock macOS Bash and BSD utilities are not supported directly; macOS users should run the rendering command through a compatible GNU/Linux environment, such as a Linux container, virtual machine, or equivalent.

Run the scripts from any directory with:

```bash
bash scripts/validate-architecture.sh
bash scripts/render-architecture.sh
```

Generated SVGs under `build/architecture-svg/` are temporary local or CI preview outputs. They are not copied into the publication directory or committed automatically.

GitHub Actions uses Ubuntu and is the canonical automated validation and rendering environment. These scripts operate only on sanitized files in this public repository; no private repository access occurs.
