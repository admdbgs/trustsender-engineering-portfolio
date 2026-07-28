# TrustSender.io Engineering Portfolio

This repository is a public, sanitized visual engineering portfolio and architecture whitepaper for TrustSender.io. It is intended to communicate approved system context and design decisions without exposing sensitive or proprietary material. The production source code and internal documentation remain private.

## Architecture at a glance

The intended architecture stack includes Next.js, FastAPI, PostgreSQL, distributed workers, Stripe, WordPress, and GitHub Actions. References in this portfolio remain deliberately high-level until they can be represented through reviewed, sanitized architecture models.

## Delivery status

- **P1 distributed validation — Operational**
- **P2 SMTP evolution — Ongoing implementation**

P2 is not represented as operational. Its documentation will evolve only as approved information becomes suitable for public release.

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
