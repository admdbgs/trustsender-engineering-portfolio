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
CONTAINER_VIEW_WIDTH = 5000
CONTAINER_VIEW_HEIGHT = 2200
INTERNAL_SYSTEM = "TrustSender.io"
PEOPLE = {"Customer", "Platform Operator"}
EXTERNAL_SYSTEMS = {
    "Google Identity", "Microsoft Identity", "Stripe", "Brevo",
    "GitHub Actions", "Internet Mail Infrastructure",
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
ROUTES = {
    ("Customer", "Edge and Routing"): (35, [(560, 900), (560, 1190)]),
    ("Platform Operator", "Edge and Routing"): (45, [(620, 1700), (620, 1310)]),
    ("Edge and Routing", "Web Application"): (55, [(1230, 1180), (1230, 800)]),
    ("Edge and Routing", "Application API"): (65, [(1600, 1250)]),
    ("Edge and Routing", "WordPress Blog"): (35, [(1290, 1320), (1290, 1650)]),
    ("Web Application", "Application API"): (45, [(1930, 800), (1930, 1180)]),
    ("Application API", "PostgreSQL Database"): (55, [(2630, 1250), (2630, 810)]),
    ("Application API", "Google Identity"): (65, [(2080, 560), (1610, 560)]),
    ("Application API", "Microsoft Identity"): (60, [(2180, 500), (2110, 500)]),
    ("Application API", "Stripe"): (78, [(2380, 440), (2610, 440)]),
    ("Application API", "Brevo"): (76, [(2480, 500), (3110, 500)]),
    ("Application API", "Job Control Plane"): (65, [(2280, 1450), (2980, 1450)]),
    ("Job Control Plane", "PostgreSQL Database"): (35, [(3050, 1235)]),
    ("Job Control Plane", "Distributed P1 Worker Plane"): (25, [(3330, 1650), (3330, 1050)]),
    ("Distributed P1 Worker Plane", "Internet Mail Infrastructure"): (55, [(4130, 1050), (4130, 1400)]),
    ("Distributed P1 Worker Plane", "Job Control Plane"): (30, [(3270, 1050), (3270, 1650)]),
    ("Job Control Plane", "P2 SMTP Execution Plane"): (50, [(3330, 1680)]),
    ("P2 SMTP Execution Plane", "Internet Mail Infrastructure"): (45, [(4210, 1750), (4210, 1400)]),
    ("P2 SMTP Execution Plane", "Job Control Plane"): (95, [(3330, 1760)]),
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
    """Return a validated deep copy with deterministic placement and routing."""
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
    route_key_by_id = {}
    observed_route_ids = {}
    for member in view_relationships:
        _require(isinstance(member, dict) and isinstance(member.get("id"), str),
                 "Container View relationship memberships must have string IDs")
        identifier = member["id"]
        _require(identifier in relationship_by_id,
                 "unresolved Container View relationship ID: {}".format(identifier))
        _require(identifier not in relationship_ids,
                 "duplicate Container View relationship membership")
        relationship = relationship_by_id[identifier]
        endpoint_ids = (relationship["sourceId"], relationship["destinationId"])
        for endpoint_id in endpoint_ids:
            _require(endpoint_id in by_id,
                     "Container View relationship {} has unresolved endpoint {}".format(
                         identifier, endpoint_id))
        endpoint_names = [by_id[endpoint_id][0]["name"] for endpoint_id in endpoint_ids]
        for endpoint_id in endpoint_ids:
            _require(endpoint_id in element_ids,
                     "Container View relationship {} has endpoint {} outside the Container "
                     "View ({} -> {})".format(identifier, endpoint_id, *endpoint_names))
        route_key = tuple(endpoint_names)
        _require(route_key not in observed_route_ids,
                 "duplicate directional relationship {} -> {} (IDs {} and {})".format(
                     route_key[0], route_key[1], observed_route_ids.get(route_key), identifier))
        observed_route_ids[route_key] = identifier
        route_key_by_id[identifier] = route_key
        relationship_ids.append(identifier)
    _require(len(relationship_ids) == len(set(relationship_ids)),
             "duplicate Container View relationship membership")
    missing_routes = set(ROUTES) - set(observed_route_ids)
    unexpected_routes = set(observed_route_ids) - set(ROUTES)
    _require(not missing_routes and not unexpected_routes,
             "Container View directional relationships differ from approved routes; "
             "missing: {}; unexpected: {}".format(
                 sorted("{} -> {}".format(*key) for key in missing_routes),
                 sorted("{} -> {} (ID {})".format(key[0], key[1], observed_route_ids[key])
                        for key in unexpected_routes)))

    result = copy.deepcopy(workspace)
    result_context = _find_view(result["views"], "systemContextViews", CONTEXT_KEY,
                                "System Context View")
    result_container = _find_view(result["views"], "containerViews", CONTAINER_KEY,
                                  "Container View")
    result_container.pop("automaticLayout", None)
    result_container["dimensions"] = {
        "width": CONTAINER_VIEW_WIDTH,
        "height": CONTAINER_VIEW_HEIGHT,
    }
    for member in result_container["elements"]:
        name = by_id[member["id"]][0]["name"]
        member["x"], member["y"], member["width"], member["height"] = LAYOUT[name]
    for member in result_container["relationships"]:
        position, vertices = ROUTES[route_key_by_id[member["id"]]]
        member["routing"] = "Orthogonal"
        member["position"] = position
        member["vertices"] = [{"x": x, "y": y} for x, y in vertices]

    _require(result["model"] == workspace["model"], "preservation gate failed: model changed")
    _require(result_context == context, "preservation gate failed: System Context View changed")
    source_view_preserved = {
        key: value for key, value in container.items()
        if key not in {"automaticLayout", "dimensions", "elements", "relationships"}
    }
    result_view_preserved = {
        key: value for key, value in result_container.items()
        if key not in {"automaticLayout", "dimensions", "elements", "relationships"}
    }
    _require(source_view_preserved == result_view_preserved,
             "preservation gate failed: unrelated Container View field changed")
    _require(result_container.get("dimensions") == {
        "width": CONTAINER_VIEW_WIDTH,
        "height": CONTAINER_VIEW_HEIGHT,
    }, "preservation gate failed: Container View dimensions differ from approved canvas")
    _require([item["id"] for item in result_container["elements"]] == element_ids,
             "preservation gate failed: Container View element membership changed")
    _require([item["id"] for item in result_container["relationships"]] == relationship_ids,
             "preservation gate failed: Container View relationship membership changed")
    for source_member, result_member in zip(container["elements"],
                                            result_container["elements"]):
        source_preserved = {key: value for key, value in source_member.items()
                            if key not in {"x", "y", "width", "height"}}
        result_preserved = {key: value for key, value in result_member.items()
                            if key not in {"x", "y", "width", "height"}}
        _require(source_preserved == result_preserved,
                 "preservation gate failed: non-layout fields changed for element {}".format(
                     source_member["id"]))
    for source_member, result_member in zip(container["relationships"],
                                            result_container["relationships"]):
        source_preserved = {key: value for key, value in source_member.items()
                            if key not in {"routing", "position", "vertices"}}
        result_preserved = {key: value for key, value in result_member.items()
                            if key not in {"routing", "position", "vertices"}}
        _require(source_preserved == result_preserved,
                 "preservation gate failed: non-routing fields changed for relationship {}".format(
                     source_member["id"]))
        position, vertices = ROUTES[route_key_by_id[source_member["id"]]]
        expected_route = {"routing": "Orthogonal", "position": position,
                          "vertices": [{"x": x, "y": y} for x, y in vertices]}
        actual_route = {key: result_member.get(key) for key in expected_route}
        _require(actual_route == expected_route,
                 "preservation gate failed: route differs for relationship {}".format(
                     source_member["id"]))
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
