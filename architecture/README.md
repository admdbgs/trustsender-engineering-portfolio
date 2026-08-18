# Architecture

This directory contains the approved, sanitized public architecture model:

- [`workspace.dsl`](workspace.dsl) is the canonical Structurizr DSL source of truth.
- [`styles.dsl`](styles.dsl) is the shared dark-mode visual-style definition.
- [`model-notes.md`](model-notes.md) explains scope, status language, modeling decisions, and the publication plan.
- [`poc/manual-engineering-overview/`](poc/manual-engineering-overview/) contains the reviewed manual Structurizr Engineering Overview presentation baseline.

## Available views

The canonical workspace defines a C4 System Context view and a C4 Container view. The Engineering Overview is maintained separately so its reviewed manual presentation geometry does not alter those C4 views.

## Validation and preview rendering

The canonical model remains [`workspace.dsl`](workspace.dsl). The [`validation script`](../scripts/validate-architecture.sh) checks the model and repository invariants, while the [`rendering script`](../scripts/render-architecture.sh) creates the reviewed C4 previews. The Engineering Overview renderer reads its approved `workspace.json` directly and verifies the recorded baseline hash before rendering.

Reviewed SVG publication outputs are stored under `diagrams/` after automated validation and visual inspection.

## Public safety

All architecture content must remain high-level, publicly reviewable, and grounded in approved information. Ongoing work must remain clearly distinct from operational capabilities.
