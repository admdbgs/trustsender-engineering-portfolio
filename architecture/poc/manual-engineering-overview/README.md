# Structurizr Manual Engineering Overview

This directory contains the reviewed manual Structurizr presentation workspace for the TrustSender.io Engineering Overview.

The canonical C4 source remains `architecture/workspace.dsl`. The Engineering Overview is intentionally maintained as a separate presentation workspace so its approved manual geometry does not alter the canonical System Context or Container View.

## Selected visual direction

The selected direction is a compact Flow Graph inspired by Structurizr Explore. It keeps the reviewed architecture semantics while prioritizing a simple left-to-right flow, circular nodes, and direct/inclined connections.

The presentation model contains exactly 16 visible nodes and 20 logical directed relationships. GitHub Actions is explicitly represented with the reviewed deployment relationship to Edge and Routing. P1 remains operational and the P2 SMTP Execution Plane remains `ONGOING`.

The circles are deliberately sized at `190x190`. Relationship labels use `fontSize 20` for improved readability while preserving the approved geometry and `Direct` routing.

All model, relationship, title, description, and presentation text is maintained in English. The viewset explicitly sets `structurizr.locale` to `en-GB` and `structurizr.timezone` to `UTC`.

## Final manual layout baseline

The approved manual layout is versioned as `workspace.json` and is designated:

`FINAL_MANUAL_LAYOUT_BASELINE`

Approved workspace baseline:

- SHA-256: `DD24ED01C9764B28C4D53BC0F204B780F68C8B85F85DCCA3164D079B7679E77B`
- GitHub blob SHA: `7becc8724fdc9aae8ef00d8d0ee33712d43dd90d`
- previous approved geometry-only baseline SHA-256: `4AD5A2AA59B341776D305ECAE361F6BA41271D0C272868229B67066DD32DEA41`
- canvas: `3795x1967`
- visible nodes: `16`
- logical directed relationships: `20`
- node shape and size: `Circle`, `190x190`
- relationship routing: `Direct`

The final generated `workspace.json` incorporates the reviewed descriptions, inspection configuration, English locale, UTC timezone, and relationship font size. Its canvas, element positions, and relationship vertices are identical to the previously approved geometry baseline. The generated layout JSON was not edited by hand.

## Inspection classification

The previously recorded inspection findings were resolved or classified without changing the approved geometry. Final inspection summary:

- errors: `0`
- warnings: `0`
- info: `21`

## Manual layout

The stable view key is:

`trustsender-engineering-overview-manual-poc`

The DSL view deliberately has no `autoLayout` statement. The approved geometry is persisted in `workspace.json` rather than hardcoded into the DSL.

Relationships use `Direct` routing. Manual vertices are persisted in the approved `workspace.json` where inclined or multi-segment routes improve readability.

## Local editing

Requires Java 21 or newer and the Structurizr `.war` binary.

From this directory, run:

```text
java -jar PATH_TO_STRUCTURIZR_WAR local .
```

Then open `http://localhost:8080`, select the Engineering Overview view, and use the diagram editor.

Future non-geometric refinements must preserve the approved geometry, regenerate `workspace.json` through Structurizr, visually review the result, and record the replacement SHA-256 before updating this baseline.

## Publication guardrails

- `architecture/workspace.dsl` remains the canonical C4 source.
- Preserve exactly 16 reviewed visible nodes and 20 logical relationships unless a separately reviewed architecture change requires otherwise.
- Preserve the approved `3795x1967` canvas and manual positions/vertices unless a separately reviewed geometry change explicitly replaces this baseline.
- Keep P1 represented as operational.
- Keep the P2 SMTP Execution Plane represented as `ONGOING`.
- Do not add group boundaries or `autoLayout` to the selected Flow Graph view.
- Keep all public diagram text in English.
- Do not introduce private repository names, credentials, IP addresses, internal filesystem paths, or production-only implementation details.
- The publication SVG is `diagrams/trustsender-engineering-overview.svg` and must remain derived from this approved workspace baseline.
- Automated checks and visual review are required before publication changes are accepted.
