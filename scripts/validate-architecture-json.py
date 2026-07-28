#!/usr/bin/env python3
"""Validate public architecture invariants in compiled Structurizr JSON."""

import json
import pathlib
import sys
from typing import Any, Iterator


class ValidationError(Exception):
    """An expected architecture invariant was not satisfied."""


def require_object(value: Any, location: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{location} must be an object")
    return value


def require_array(value: Any, location: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValidationError(f"{location} must be an array")
    return value


def parse_tags(value: Any, location: str) -> set[str]:
    if value is None:
        return set()
    if not isinstance(value, str):
        raise ValidationError(f"{location} must be a string or null")
    return {token.strip() for token in value.split(",") if token.strip()}


def relationship_objects(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        if "sourceId" in value and "destinationId" in value:
            yield value
        for child in value.values():
            yield from relationship_objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from relationship_objects(child)


def validate_named_view(
    views: dict[str, Any], array_name: str, expected_key: str
) -> None:
    entries = require_array(views.get(array_name), f"views.{array_name}")
    if len(entries) != 1:
        raise ValidationError(f"views.{array_name} must contain exactly one view")
    view = require_object(entries[0], f"views.{array_name}[0]")
    if view.get("key") != expected_key:
        raise ValidationError(
            f"views.{array_name}[0].key must be {expected_key!r}"
        )


def validate_workspace(workspace: Any) -> None:
    root = require_object(workspace, "root")
    model = require_object(root.get("model"), "model")
    software_systems = require_array(
        model.get("softwareSystems"), "model.softwareSystems"
    )

    matching_systems = []
    for index, value in enumerate(software_systems):
        system = require_object(value, f"model.softwareSystems[{index}]")
        if system.get("name") == "TrustSender.io":
            matching_systems.append(system)
    if len(matching_systems) != 1:
        raise ValidationError(
            "model.softwareSystems must contain exactly one 'TrustSender.io' system"
        )

    containers = require_array(
        matching_systems[0].get("containers"), "TrustSender.io containers"
    )
    p2_containers = []
    for index, value in enumerate(containers):
        container = require_object(value, f"TrustSender.io containers[{index}]")
        if container.get("name") == "P2 SMTP Execution Plane":
            p2_containers.append(container)
    if len(p2_containers) != 1:
        raise ValidationError(
            "TrustSender.io must contain exactly one 'P2 SMTP Execution Plane' container"
        )

    p2_container = p2_containers[0]
    description = p2_container.get("description")
    if not isinstance(description, str):
        raise ValidationError("P2 container description must be a string")
    if "Status: ONGOING." not in description:
        raise ValidationError("P2 container description must contain 'Status: ONGOING.'")
    p2_tags = parse_tags(p2_container.get("tags"), "P2 container tags")
    if "Ongoing" not in p2_tags or "Operational" in p2_tags:
        raise ValidationError(
            "P2 container tags must include 'Ongoing' and exclude 'Operational'"
        )

    p2_id = p2_container.get("id")
    if not isinstance(p2_id, str) or not p2_id:
        raise ValidationError("P2 container id must be a non-empty string")
    p2_relationships = [
        relationship
        for relationship in relationship_objects(model)
        if relationship.get("sourceId") == p2_id
        or relationship.get("destinationId") == p2_id
    ]
    if not p2_relationships:
        raise ValidationError("at least one compiled P2 relationship is required")
    for index, relationship in enumerate(p2_relationships):
        tags = parse_tags(relationship.get("tags"), f"P2 relationship[{index}] tags")
        if "Ongoing" not in tags or "Operational" in tags:
            raise ValidationError(
                f"P2 relationship[{index}] tags must include 'Ongoing' "
                "and exclude 'Operational'"
            )

    views = require_object(root.get("views"), "views")
    validate_named_view(
        views, "systemContextViews", "trustsender-system-context"
    )
    validate_named_view(views, "containerViews", "trustsender-container-view")
    for array_name in (
        "systemLandscapeViews",
        "componentViews",
        "dynamicViews",
        "deploymentViews",
        "filteredViews",
        "imageViews",
        "customViews",
    ):
        if array_name in views:
            entries = require_array(views[array_name], f"views.{array_name}")
            if entries:
                raise ValidationError(f"views.{array_name} must be empty")

    configuration = require_object(views.get("configuration"), "views.configuration")
    styles = require_object(configuration.get("styles"), "views.configuration.styles")
    relationship_styles = require_array(
        styles.get("relationships"), "views.configuration.styles.relationships"
    )
    for required_tag, expected_dashed in (("Operational", False), ("Ongoing", True)):
        matches = []
        for index, value in enumerate(relationship_styles):
            style = require_object(
                value, f"views.configuration.styles.relationships[{index}]"
            )
            if style.get("tag") == required_tag:
                matches.append(style)
        if len(matches) != 1:
            raise ValidationError(
                f"relationship styles must contain exactly one {required_tag!r} style"
            )
        dashed = matches[0].get("dashed")
        if type(dashed) is not bool or dashed is not expected_dashed:
            raise ValidationError(
                f"{required_tag} relationship style dashed must be exactly "
                f"{str(expected_dashed).lower()}"
            )


def main() -> int:
    if len(sys.argv) != 2:
        print(
            "Error: expected exactly one compiled workspace JSON path",
            file=sys.stderr,
        )
        return 2

    path = pathlib.Path(sys.argv[1])
    try:
        with path.open("r", encoding="utf-8") as compiled_file:
            workspace = json.load(compiled_file)
        validate_workspace(workspace)
    except (OSError, json.JSONDecodeError) as error:
        print(f"Error: could not read compiled workspace JSON: {error}", file=sys.stderr)
        return 1
    except ValidationError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
