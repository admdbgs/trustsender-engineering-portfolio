# Architecture model notes

## Public scope

This model is a public, sanitized description of TrustSender.io. It records only approved people, external dependencies, containers, responsibilities, statuses, and high-level relationships. It is designed to remain useful and readable as text without a rendered diagram.

The model intentionally omits private infrastructure identifiers, security-sensitive configuration, proprietary implementation details, raw schemas, endpoint inventories, datasets, commercial scoring internals, and operational metrics.

## Canonical model and status language

[`workspace.dsl`](workspace.dsl) is the canonical architecture source because Structurizr DSL provides a reviewable, version-controlled representation of the C4 model. Other presentations must be derived from, and remain consistent with, this source.

**Operational** identifies approved current containers and relationships. **ONGOING** identifies planned or in-progress evolution that must not be interpreted as operational or production-ready. The P2 SMTP Execution Plane and every relationship involving it use the `Ongoing` model tag and future-tense descriptions to preserve that distinction.

## Current and future views

The current workspace contains only these C4 views:

- System Context
- Container

Future reviewed modeling may add dedicated views for:

- Infrastructure and Deployment
- Trust Boundaries
- Authentication and Identity
- Billing and Day Pass
- Job Control Plane
- Distributed P1 Execution
- P2 SMTP Evolution
- Outputs and Authority
- CI/CD and Production Protection

Those future topics are a publication plan, not additional views or implementation claims in the current workspace.

## Presentation and publication

D2 will later provide the visual presentation layer for the main portfolio overview. SVG is the intended publication format, and every generated SVG will be reviewed for correctness and public safety before publication.
