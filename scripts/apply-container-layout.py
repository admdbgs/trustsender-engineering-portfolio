#!/usr/bin/env python3
"""Validate and apply the approved manual Container View element layout."""

import copy
import json
import os
from pathlib import Path
import stat
import sys
import tempfile


CONTEXT_KEY = "trustsender-system-context"
CONTAINER_KEY = "trustsender-container-view"
INTERNAL_SYSTEM = "TrustSender.io"
PEOPLE = {"Customer", "Platform Operator"}
EXTERNAL_SYSTEMS = {
    "Google Identity", "Microsoft Identity", "Stripe", "Brevo",
    "Internet Mail Infrastructure",
}
CONTAINERS = {
    "Edge and Routing", "Web Application", "Application API",
    "PostgreSQL Database", "Job Control Plane",
    "Distributed P1 Worker Plane", "P2 SMTP Execution Plane",
    "WordPress Blog",
}
LAYOUT = {
    "Customer": (100, 700, 400, 400),
    "Platform Operator": (100, 1500, 400, 400),
    "Edge and Routing": (700, 1100, 460, 300),
    "Web Application": (1350, 650, 460, 300),
    "WordPress Blog": (1350, 1500, 460, 300),
    "Application API": (2050, 1100, 460, 300),
    "PostgreSQL Database": (2750, 650, 460, 320),
    "Job Control Plane": (2750, 1500, 460, 300),
    "Distributed P1 Worker Plane": (3450, 900, 460, 300),
    "P2 SMTP Execution Plane": (3450, 1600, 460, 300),
    "Internet Mail Infrastructure": (4350, 1250, 460, 300),
    "Google Identity": (1400, 100, 420, 280),
    "Microsoft Identity": (1900, 100, 420, 280),
    "Stripe": (2400, 100, 420, 280),
    "Brevo": (2900, 100, 420, 280),
}


class LayoutError(ValueError):
    """An actionable workspace or filesystem validation error."""


def _require(condition, message):
    if not condition:
        raise LayoutError(message)


def _tags(value, subject):
    _require(isinstance(value, str), "{} tags must be a string".format(subject))
    return {token.strip() for token in value.split(",") if token.strip()}


def _list(mapping, key, subject):
    value = mapping.get(key)
    _require(isinstance(value, list), "{} must contain a '{}' array".format(subject, key))
    return value


def _index_model(model):
    _require(isinstance(model, dict), "workspace must contain a model object")
    people = _list(model, "people", "model")
    systems = _list(model, "softwareSystems", "model")
    elements = []
    relationships = []

    def add_relationships(owner):
        records = owner.get("relationships", [])
        _require(isinstance(records, list), "model relationships must be arrays")
        for relationship in records:
            _require(isinstance(relationship, dict), "model relationship records must be objects")
            relationships.append(relationship)

    def add_element(element, c4_type, owner_id=None):
        _require(isinstance(element, dict), "model element records must be objects")
        elements.append((element, c4_type, owner_id))
        add_relationships(element)

    for person in people:
        add_element(person, "Person")
    for system in systems:
        add_element(system, "SoftwareSystem")
        containers = system.get("containers", [])
        _require(isinstance(containers, list), "software system containers must be arrays")
        for container in containers:
            add_element(container, "Container", system.get("id"))
            components = container.get("components", [])
            _require(isinstance(components, list), "container components must be arrays")
            for component in components:
                add_element(component, "Component", container.get("id"))
    add_relationships(model)

    by_id = {}
    by_name = {}
    for element, c4_type, owner_id in elements:
        identifier = element.get("id")
        name = element.get("name")
        _require(isinstance(identifier, str) and identifier,
                 "every model element must have a non-empty string ID")
        _require(identifier not in by_id,
                 "duplicate model element ID: {}".format(identifier))
        _require(isinstance(name, str) and name,
                 "every model element must have a non-empty string name")
        record = (element, c4_type, owner_id)
        by_id[identifier] = record
        by_name.setdefault(name, []).append(record)

    relationship_by_id = {}
    for relationship in relationships:
        identifier = relationship.get("id")
        _require(isinstance(identifier, str) and identifier,
                 "every model relationship must have a non-empty string ID")
        _require(identifier not in relationship_by_id,
                 "duplicate model relationship ID: {}".format(identifier))
        _require(isinstance(relationship.get("sourceId"), str) and
                 isinstance(relationship.get("destinationId"), str),
                 "model relationship {} must have sourceId and destinationId".format(identifier))
        relationship_by_id[identifier] = relationship
    return elements, relationships, by_id, by_name, relationship_by_id


def _unique_named(by_name, name, expected_type, expected_owner=None):
    matches = by_name.get(name, [])
    _require(len(matches) == 1,
             "required name '{}' must occur exactly once; found {}".format(name, len(matches)))
    _require(matches[0][1] == expected_type,
             "'{}' must be a {}, not a {}".format(name, expected_type, matches[0][1]))
    if expected_owner is not None:
        _require(matches[0][2] == expected_owner,
                 "container '{}' must be directly owned by {}".format(name, INTERNAL_SYSTEM))
    return matches[0][0]


def _find_view(views, collection, key, label):
    records = _list(views, collection, "views")
    matches = [view for view in records
               if isinstance(view, dict) and view.get("key") == key]
    _require(len(matches) == 1,
             "expected exactly one {} with key '{}'; found {}".format(label, key, len(matches)))
    return matches[0]


def transform(workspace):
    """Return a validated deep copy with deterministic element placement."""
    _require(isinstance(workspace, dict), "workspace JSON root must be an object")
    _require("model" in workspace and isinstance(workspace.get("views"), dict),
             "unexpected workspace schema: model and views objects are required")
    (elements, relationships, by_id, by_name,
     relationship_by_id) = _index_model(workspace["model"])

    _require(sum(1 for item in elements if item[1] == "Person") == 2,
             "model must contain exactly 2 people")
    _require(sum(1 for item in elements if item[1] == "SoftwareSystem") == 7,
             "model must contain exactly 7 software systems")
    for name in PEOPLE:
        _unique_named(by_name, name, "Person")
    trust_sender = _unique_named(by_name, INTERNAL_SYSTEM, "SoftwareSystem")
    trust_sender_id = trust_sender["id"]
    for name in EXTERNAL_SYSTEMS:
        _unique_named(by_name, name, "SoftwareSystem")
    _require(len(trust_sender.get("containers", [])) == 8,
             "TrustSender.io must directly own exactly 8 containers")
    for name in CONTAINERS:
        _unique_named(by_name, name, "Container", trust_sender_id)

    p2 = _unique_named(by_name, "P2 SMTP Execution Plane", "Container", trust_sender_id)
    p2_tags = _tags(p2.get("tags"), "P2 SMTP Execution Plane")
    _require("Ongoing" in p2_tags, "P2 SMTP Execution Plane must have the Ongoing tag")
    _require("Operational" not in p2_tags,
             "P2 SMTP Execution Plane must not have the Operational tag")
    description = p2.get("description")
    _require(isinstance(description, str), "P2 SMTP Execution Plane description must be a string")
    _require(description.count("Status: ONGOING.") == 1,
             "P2 SMTP Execution Plane description must contain 'Status: ONGOING.' exactly once")
    incident = [relationship for relationship in relationships
                if p2["id"] in (relationship.get("sourceId"), relationship.get("destinationId"))]
    _require(incident, "P2 SMTP Execution Plane must have at least one incident relationship")
    for relationship in incident:
        tokens = _tags(relationship.get("tags"),
                       "P2 relationship {}".format(relationship["id"]))
        _require("Ongoing" in tokens,
                 "P2 relationship {} must have the Ongoing tag".format(relationship["id"]))
        _require("Operational" not in tokens,
                 "P2 relationship {} must not have the Operational tag".format(relationship["id"]))

    views = workspace["views"]
    context = _find_view(views, "systemContextViews", CONTEXT_KEY, "System Context View")
    container = _find_view(views, "containerViews", CONTAINER_KEY, "Container View")
    view_elements = _list(container, "elements", "Container View")
    view_relationships = _list(container, "relationships", "Container View")
    _require(len(view_elements) == 15, "Container View must contain exactly 15 elements")
    _require(len(view_relationships) == 19,
             "Container View must contain exactly 19 relationships")
    element_ids = []
    for member in view_elements:
        _require(isinstance(member, dict) and isinstance(member.get("id"), str),
                 "Container View element memberships must have string IDs")
        identifier = member["id"]
        _require(identifier in by_id,
                 "unresolved Container View element ID: {}".format(identifier))
        element_ids.append(identifier)
    _require(len(element_ids) == len(set(element_ids)),
             "duplicate Container View element membership")
    names = [by_id[identifier][0]["name"] for identifier in element_ids]
    _require("GitHub Actions" not in names,
             "Container View must not include the GitHub Actions element")
    _require(set(names) == set(LAYOUT),
             "Container View elements do not match the approved 15-element layout")

    relationship_ids = []
    for member in view_relationships:
        _require(isinstance(member, dict) and isinstance(member.get("id"), str),
                 "Container View relationship memberships must have string IDs")
        identifier = member["id"]
        _require(identifier in relationship_by_id,
                 "unresolved Container View relationship ID: {}".format(identifier))
        relationship_ids.append(identifier)
    _require(len(relationship_ids) == len(set(relationship_ids)),
             "duplicate Container View relationship membership")

    result = copy.deepcopy(workspace)
    result_context = _find_view(result["views"], "systemContextViews", CONTEXT_KEY,
                                "System Context View")
    result_container = _find_view(result["views"], "containerViews", CONTAINER_KEY,
                                  "Container View")
    result_container.pop("automaticLayout", None)
    for member in result_container["elements"]:
        name = by_id[member["id"]][0]["name"]
        member["x"], member["y"], member["width"], member["height"] = LAYOUT[name]

    _require(result["model"] == workspace["model"], "preservation gate failed: model changed")
    _require(result_context == context, "preservation gate failed: System Context View changed")
    _require(result_container["relationships"] == container["relationships"],
             "preservation gate failed: Container View relationships changed")
    _require([item["id"] for item in result_container["elements"]] == element_ids,
             "preservation gate failed: Container View element membership changed")
    _require([item["id"] for item in result_container["relationships"]] == relationship_ids,
             "preservation gate failed: Container View relationship membership changed")
    result_counts = _index_model(result["model"])
    _require(len(result_counts[0]) == len(elements) and len(result_counts[1]) == len(relationships),
             "preservation gate failed: model counts changed")
    return result


def apply_layout(input_path, output_path):
    """Read, validate, transform, and atomically write a workspace."""
    source = Path(input_path)
    destination = Path(output_path)
    _require(not source.is_symlink(), "input path must not be a symbolic link: {}".format(source))
    _require(source.exists(), "input file does not exist: {}".format(source))
    _require(stat.S_ISREG(source.stat().st_mode), "input path is not a regular file: {}".format(source))
    _require(source.stat().st_size > 0, "input file is empty: {}".format(source))
    _require(not destination.is_symlink(),
             "output path must not be a symbolic link: {}".format(destination))
    _require(destination.parent.exists() and destination.parent.is_dir(),
             "output directory does not exist: {}".format(destination.parent))
    _require(source.resolve() != destination.resolve(),
             "input and output paths must be different")
    try:
        raw = source.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise LayoutError("input is not valid UTF-8: {}".format(error))
    try:
        workspace = json.loads(raw)
    except json.JSONDecodeError as error:
        raise LayoutError("input is not valid JSON at line {}, column {}: {}".format(
            error.lineno, error.colno, error.msg))
    result = transform(workspace)
    serialized = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    temporary_name = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n",
                                         dir=str(destination.parent),
                                         prefix=".{}-".format(destination.name),
                                         suffix=".tmp", delete=False) as temporary:
            temporary_name = temporary.name
            temporary.write(serialized)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_name, str(destination))
        temporary_name = None
    finally:
        if temporary_name is not None:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass


def main(argv=None):
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) != 2:
        print("Usage: python3 scripts/apply-container-layout.py INPUT_JSON OUTPUT_JSON",
              file=sys.stderr)
        return 2
    try:
        apply_layout(arguments[0], arguments[1])
    except (LayoutError, OSError) as error:
        print("Error: {}".format(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
