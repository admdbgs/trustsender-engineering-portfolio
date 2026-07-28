# Architecture

This directory contains the approved, sanitized public architecture model:

- [`workspace.dsl`](workspace.dsl) is the canonical Structurizr DSL source of truth.
- [`styles.dsl`](styles.dsl) is the shared dark-mode visual-style definition.
- [`model-notes.md`](model-notes.md) explains scope, status language, modeling decisions, and the publication plan.

## Available views

The workspace currently defines only a C4 System Context view and a C4 Container view. The text model is intentionally readable without rendering.

Rendering, additional views, and automated validation may be added in later reviewed work. D2 is planned as the presentation layer for the main overview, with reviewed SVGs as the future publication format.

## Public safety

All architecture content must remain high-level, publicly reviewable, and grounded in approved information. Do not add private infrastructure identifiers, secrets, proprietary implementation details, raw internal data, unsupported claims, or unverified metrics. Ongoing work must remain clearly distinct from operational capabilities.
