# Architecture model notes

## Public scope

This model is a public, sanitized description of TrustSender.io. It records only approved people, external dependencies, containers, responsibilities, statuses, and high-level relationships. It is designed to remain useful and readable as text without a rendered diagram.

The model intentionally omits private infrastructure identifiers, security-sensitive configuration, proprietary implementation details, raw schemas, endpoint inventories, datasets, commercial scoring internals, and operational metrics.

## Canonical model and status language

[`workspace.dsl`](workspace.dsl) is the canonical C4 architecture source because Structurizr DSL provides a reviewable, version-controlled representation of the model. Other presentations must remain consistent with this source.

**Operational** identifies approved current containers and relationships. **ONGOING** identifies planned or in-progress evolution that must not be interpreted as operational or production-ready. The P2 SMTP Execution Plane and every relationship involving it preserve that distinction.

## Current views and presentation

The canonical workspace contains these C4 views:

- System Context
- Container

The main Engineering Overview is a separate reviewed Structurizr manual Flow Graph under `poc/manual-engineering-overview/`. It contains 16 reviewed visible nodes and 20 logical directed relationships on an approved 3795x1967 manual canvas. Its geometry is persisted in `workspace.json` rather than generated with automatic layout.

Future reviewed modeling may add dedicated views for Infrastructure and Deployment, Trust Boundaries, Authentication and Identity, Billing and Day Pass, Job Control Plane, Distributed P1 Execution, P2 SMTP Evolution, Outputs and Authority, and CI/CD and Production Protection. Those topics are a publication plan, not additional implementation claims in the current workspace.

## Presentation and publication

Structurizr is used for both the canonical C4 model and the separately reviewed Engineering Overview presentation workspace. SVG is the publication format. Generated SVGs must pass automated validation, visual inspection, and public-safety inspection before publication.
