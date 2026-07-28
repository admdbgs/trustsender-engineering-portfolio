# TrustSender.io Engineering Portfolio

This repository is a public, sanitized visual engineering portfolio and architecture whitepaper for TrustSender.io. It is intended to communicate approved system context and design decisions without exposing sensitive or proprietary material. The production source code and internal documentation remain private.

## Architecture at a glance

The intended architecture stack includes Next.js, FastAPI, PostgreSQL, distributed workers, Stripe, WordPress, and GitHub Actions. References in this portfolio remain deliberately high-level until they can be represented through reviewed, sanitized architecture models.

## Delivery status

- **P1 distributed validation — Operational**
- **P2 SMTP evolution — ONGOING**

P2 is not represented as operational. Its documentation will evolve only as approved information becomes suitable for public release.

## Architecture model

The canonical public architecture is maintained as text in [`architecture/workspace.dsl`](architecture/workspace.dsl). Its sanitized scope and modeling conventions are documented in [`architecture/model-notes.md`](architecture/model-notes.md).

Rendered diagrams will be added only after the textual model is reviewed.

## Architecture validation

GitHub Actions validates the canonical Structurizr DSL and generates two dark-mode architecture previews as temporary CI artifacts. Each preview is accompanied by an automatically generated key/legend SVG. Diagrams are published only after human validation, visual, and public-safety review; previews are not embedded or published automatically.

## Roadmap

1. Canonical C4 model with Structurizr DSL
2. Dark-mode D2 engineering overview
3. Multi-level architecture diagrams
4. Sanitized engineering metrics
5. GitHub Pages visual whitepaper

## Repository contents

- `architecture/` contains reviewed architecture narratives and, in the future, the canonical model.
- `visuals/` defines the presentation direction for the visual whitepaper.
- `diagrams/` will hold reviewed publication-ready diagrams.
- `metrics/` defines a schema for future sanitized aggregate metrics.
- `scripts/` is reserved for reviewed portfolio-generation utilities.
- `assets/` is reserved for approved publication assets and icons.

All public content must follow the safety and review requirements in [`AGENTS.md`](AGENTS.md).
