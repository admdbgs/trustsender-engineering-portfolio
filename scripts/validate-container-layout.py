#!/usr/bin/env python3
"""Independently validate the published manual Container View geometry."""

import json
from pathlib import Path
import stat
import sys


CONTEXT_KEY = "trustsender-system-context"
CONTAINER_KEY = "trustsender-container-view"
INTERNAL_SYSTEM = "TrustSender.io"
PEOPLE = {"Customer", "Platform Operator"}
EXTERNAL_SYSTEMS = {"Google Identity", "Microsoft Identity", "Stripe", "Brevo",
                    "GitHub Actions", "Internet Mail Infrastructure"}
CONTAINERS = {"Edge and Routing", "Web Application", "Application API",
              "PostgreSQL Database", "Job Control Plane", "Distributed P1 Worker Plane",
              "P2 SMTP Execution Plane", "WordPress Blog"}
LAYOUT = {
    "Customer": (100, 700, 400, 400), "Platform Operator": (100, 1500, 400, 400),
    "Edge and Routing": (700, 1100, 460, 300), "Web Application": (1350, 650, 460, 300),
    "WordPress Blog": (1350, 1500, 460, 300), "Application API": (2050, 1100, 460, 300),
    "PostgreSQL Database": (2750, 650, 460, 320), "Job Control Plane": (2750, 1500, 460, 300),
    "Distributed P1 Worker Plane": (3450, 900, 460, 300),
    "P2 SMTP Execution Plane": (3450, 1600, 460, 300),
    "Internet Mail Infrastructure": (4350, 1250, 460, 300),
    "Google Identity": (1400, 100, 420, 280), "Microsoft Identity": (1900, 100, 420, 280),
    "Stripe": (2400, 100, 420, 280), "Brevo": (2900, 100, 420, 280),
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
    ("Application API", "Microsoft Identity"): (35, [(2180, 500), (2110, 500)]),
    ("Application API", "Stripe"): (45, [(2380, 440), (2610, 440)]),
    ("Application API", "Brevo"): (55, [(2480, 500), (3110, 500)]),
    ("Application API", "Job Control Plane"): (65, [(2280, 1450), (2980, 1450)]),
    ("Job Control Plane", "PostgreSQL Database"): (35, [(3050, 1235)]),
    ("Job Control Plane", "Distributed P1 Worker Plane"): (45, [(3330, 1650), (3330, 1050)]),
    ("Distributed P1 Worker Plane", "Internet Mail Infrastructure"): (55, [(4130, 1050), (4130, 1400)]),
    ("Distributed P1 Worker Plane", "Job Control Plane"): (65, [(3270, 1050), (3270, 1650)]),
    ("Job Control Plane", "P2 SMTP Execution Plane"): (35, [(3330, 1680)]),
    ("P2 SMTP Execution Plane", "Internet Mail Infrastructure"): (45, [(4210, 1750), (4210, 1400)]),
    ("P2 SMTP Execution Plane", "Job Control Plane"): (55, [(3330, 1760)]),
}


class ValidationError(ValueError):
    """An actionable input or invariant failure."""


def _require(condition, message):
    if not condition:
        raise ValidationError(message)


def _array(mapping, key, subject):
    value = mapping.get(key)
    _require(isinstance(value, list), "{} must contain a '{}' array".format(subject, key))
    return value


def _tokens(value, subject):
    _require(isinstance(value, str), "{} tags must be a string".format(subject))
    return {part.strip() for part in value.split(",") if part.strip()}


def _index_model(model):
    _require(isinstance(model, dict), "workspace must contain a model object")
    elements = []
    relationships = []

    def add_relationships(owner):
        records = owner.get("relationships", [])
        _require(isinstance(records, list), "model relationships must be arrays")
        for record in records:
            _require(isinstance(record, dict), "model relationship records must be objects")
            relationships.append(record)

    def add(element, kind, owner=None):
        _require(isinstance(element, dict), "model element records must be objects")
        elements.append((element, kind, owner))
        add_relationships(element)

    people = _array(model, "people", "model")
    systems = _array(model, "softwareSystems", "model")
    for person in people:
        add(person, "Person")
    for system in systems:
        add(system, "SoftwareSystem")
        containers = system.get("containers", [])
        _require(isinstance(containers, list), "software system containers must be arrays")
        for container in containers:
            add(container, "Container", system.get("id"))
            components = container.get("components", [])
            _require(isinstance(components, list), "container components must be arrays")
            for component in components:
                add(component, "Component", container.get("id"))
    add_relationships(model)

    by_id = {}
    by_name = {}
    for element, kind, owner in elements:
        identifier, name = element.get("id"), element.get("name")
        _require(isinstance(identifier, str) and identifier,
                 "every model element must have a non-empty string ID")
        _require(identifier not in by_id, "duplicate model element ID: {}".format(identifier))
        _require(isinstance(name, str) and name,
                 "every model element must have a non-empty string name")
        record = (element, kind, owner)
        by_id[identifier] = record
        by_name.setdefault(name, []).append(record)
    relationship_by_id = {}
    for relationship in relationships:
        identifier = relationship.get("id")
        _require(isinstance(identifier, str) and identifier,
                 "every model relationship must have a non-empty string ID")
        _require(identifier not in relationship_by_id,
                 "duplicate model relationship ID: {}".format(identifier))
        source, destination = relationship.get("sourceId"), relationship.get("destinationId")
        _require(isinstance(source, str) and source and isinstance(destination, str) and destination,
                 "model relationship {} has malformed endpoints".format(identifier))
        _require(source in by_id and destination in by_id,
                 "model relationship {} has unresolved endpoint".format(identifier))
        relationship_by_id[identifier] = relationship
    return elements, relationships, by_id, by_name, relationship_by_id


def _named(by_name, name, kind, owner=None):
    matches = by_name.get(name, [])
    _require(len(matches) == 1, "required name '{}' must occur exactly once; found {}".format(name, len(matches)))
    _require(matches[0][1] == kind, "'{}' must be a {}, not a {}".format(name, kind, matches[0][1]))
    if owner is not None:
        _require(matches[0][2] == owner, "container '{}' has incorrect direct ownership".format(name))
    return matches[0][0]


def _view(views, collection, key, label):
    records = _array(views, collection, "views")
    matches = [record for record in records if isinstance(record, dict) and record.get("key") == key]
    _require(len(matches) == 1, "expected exactly one {} with key '{}'; found {}".format(label, key, len(matches)))
    return matches[0]


def _inside(point, rectangle):
    x, y = point
    left, top, width, height = rectangle
    return left < x < left + width and top < y < top + height


def _segment_crosses_interior(first, second, rectangle):
    x1, y1 = first
    x2, y2 = second
    left, top, width, height = rectangle
    right, bottom = left + width, top + height
    if x1 == x2:
        return left < x1 < right and max(min(y1, y2), top) < min(max(y1, y2), bottom)
    if y1 == y2:
        return top < y1 < bottom and max(min(x1, x2), left) < min(max(x1, x2), right)
    return False


def validate_geometry(vertices, relationship_id, source, destination, rectangles=None):
    """Validate explicit route vertices and segments independently of exact matching."""
    label = "relationship {} ({} -> {})".format(relationship_id, source, destination)
    _require(isinstance(vertices, list) and vertices, "{} must have at least one explicit vertex".format(label))
    points = []
    for index, vertex in enumerate(vertices):
        _require(isinstance(vertex, dict) and set(vertex) == {"x", "y"},
                 "{} vertex {} must contain exactly x and y".format(label, index))
        _require(type(vertex["x"]) is int and type(vertex["y"]) is int,
                 "{} vertex {} coordinates must be integers".format(label, index))
        point = (vertex["x"], vertex["y"])
        _require(0 <= point[0] <= 5000 and 0 <= point[1] <= 2000,
                 "{} vertex {} {} is outside bounds".format(label, index, point))
        for name, rectangle in (LAYOUT if rectangles is None else rectangles).items():
            _require(not _inside(point, rectangle),
                     "{} vertex {} {} lies inside '{}'".format(label, index, point, name))
        points.append(point)
    for index, (first, second) in enumerate(zip(points, points[1:])):
        _require(first != second, "{} segment {} has duplicate consecutive vertices {}".format(label, index, first))
        _require(first[0] == second[0] or first[1] == second[1],
                 "{} segment {} {} -> {} is diagonal".format(label, index, first, second))
        for name, rectangle in (LAYOUT if rectangles is None else rectangles).items():
            _require(not _segment_crosses_interior(first, second, rectangle),
                     "{} segment {} {} -> {} crosses '{}' interior".format(label, index, first, second, name))


def validate_workspace(workspace):
    """Raise ValidationError unless every approved invariant holds."""
    _require(isinstance(workspace, dict), "workspace JSON root must be an object")
    _require(isinstance(workspace.get("model"), dict) and isinstance(workspace.get("views"), dict),
             "unexpected workspace schema: model and views objects are required")
    elements, relationships, by_id, by_name, relationship_by_id = _index_model(workspace["model"])
    _require(sum(item[1] == "Person" for item in elements) == 2, "model must contain exactly 2 people")
    _require(sum(item[1] == "SoftwareSystem" for item in elements) == 7,
             "model must contain exactly 7 software systems")
    for name in PEOPLE:
        _named(by_name, name, "Person")
    internal = _named(by_name, INTERNAL_SYSTEM, "SoftwareSystem")
    for name in EXTERNAL_SYSTEMS:
        _named(by_name, name, "SoftwareSystem")
    _require(len(internal.get("containers", [])) == 8,
             "TrustSender.io must directly own exactly 8 containers")
    for name in CONTAINERS:
        _named(by_name, name, "Container", internal["id"])

    p2 = _named(by_name, "P2 SMTP Execution Plane", "Container", internal["id"])
    tags = _tokens(p2.get("tags"), "P2 SMTP Execution Plane")
    _require("Ongoing" in tags and "Operational" not in tags, "P2 SMTP Execution Plane status tags are invalid")
    _require(isinstance(p2.get("description"), str) and p2["description"].count("Status: ONGOING.") == 1,
             "P2 SMTP Execution Plane description must contain 'Status: ONGOING.' exactly once")
    incident = [item for item in relationships if p2["id"] in (item["sourceId"], item["destinationId"])]
    _require(incident, "P2 SMTP Execution Plane must have at least one incident relationship")
    for item in incident:
        item_tags = _tokens(item.get("tags"), "P2 relationship {}".format(item["id"]))
        _require("Ongoing" in item_tags and "Operational" not in item_tags,
                 "P2 relationship {} status tags are invalid".format(item["id"]))

    views = workspace["views"]
    context = _view(views, "systemContextViews", CONTEXT_KEY, "System Context View")
    container = _view(views, "containerViews", CONTAINER_KEY, "Container View")
    _require(context.get("automaticLayout") is not None, "System Context View automaticLayout must be non-null")
    _require("automaticLayout" not in container, "Container View must not contain automaticLayout")
    view_elements = _array(container, "elements", "Container View")
    view_relationships = _array(container, "relationships", "Container View")
    _require(len(view_elements) == 15, "Container View must contain exactly 15 elements")
    _require(len(view_relationships) == 19, "Container View must contain exactly 19 relationships")
    element_ids = []
    observed_rectangles = {}
    for member in view_elements:
        _require(isinstance(member, dict) and isinstance(member.get("id"), str),
                 "Container View element memberships must have string IDs")
        identifier = member["id"]
        _require(identifier in by_id, "unresolved Container View element ID: {}".format(identifier))
        _require(identifier not in element_ids, "duplicate Container View element membership: {}".format(identifier))
        name = by_id[identifier][0]["name"]
        _require(name in LAYOUT, "unexpected Container View element: {}".format(name))
        values = tuple(member.get(key) for key in ("x", "y", "width", "height"))
        _require(all(type(value) is int for value in values), "element '{}' geometry must use integers".format(name))
        x, y, width, height = values
        _require(x >= 0 and y >= 0 and width > 0 and height > 0 and x + width <= 5000 and y + height <= 2000,
                 "element '{}' rectangle {} is outside approved bounds".format(name, values))
        _require(values == LAYOUT[name], "element '{}' geometry {} does not equal approved {}".format(name, values, LAYOUT[name]))
        element_ids.append(identifier)
        observed_rectangles[name] = values
    _require(set(observed_rectangles) == set(LAYOUT), "Container View elements do not match approved layout")
    names = list(observed_rectangles)
    _require("GitHub Actions" not in names, "Container View must not include GitHub Actions")
    for index, first_name in enumerate(names):
        a = observed_rectangles[first_name]
        for second_name in names[index + 1:]:
            b = observed_rectangles[second_name]
            overlap = a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]
            _require(not overlap, "element rectangles overlap: '{}' and '{}'".format(first_name, second_name))

    observed = {}
    relationship_ids = set()
    for member in view_relationships:
        _require(isinstance(member, dict) and isinstance(member.get("id"), str),
                 "Container View relationship memberships must have string IDs")
        identifier = member["id"]
        _require(identifier not in relationship_ids, "duplicate Container View relationship membership: {}".format(identifier))
        _require(identifier in relationship_by_id, "unresolved Container View relationship ID: {}".format(identifier))
        relationship_ids.add(identifier)
        relationship = relationship_by_id[identifier]
        source_id, destination_id = relationship["sourceId"], relationship["destinationId"]
        source, destination = by_id[source_id][0]["name"], by_id[destination_id][0]["name"]
        _require(source_id in element_ids and destination_id in element_ids,
                 "relationship {} ({} -> {}) has endpoint outside Container View".format(identifier, source, destination))
        key = (source, destination)
        _require(key not in observed, "duplicate directional route {} -> {} (relationship {})".format(source, destination, identifier))
        _require(key in ROUTES, "unexpected directional route {} -> {} (relationship {})".format(source, destination, identifier))
        observed[key] = identifier
        expected_position, expected_points = ROUTES[key]
        _require(member.get("routing") == "Orthogonal",
                 "relationship {} ({} -> {}) routing must be Orthogonal".format(identifier, source, destination))
        _require(type(member.get("position")) is int and member["position"] == expected_position,
                 "relationship {} ({} -> {}) position {} does not equal approved {}".format(identifier, source, destination, member.get("position"), expected_position))
        validate_geometry(member.get("vertices"), identifier, source, destination)
        expected_vertices = [{"x": x, "y": y} for x, y in expected_points]
        _require(member["vertices"] == expected_vertices,
                 "relationship {} ({} -> {}) vertices do not equal approved ordered vertices".format(identifier, source, destination))
    missing = set(ROUTES) - set(observed)
    _require(not missing, "missing approved routes: {}".format(sorted("{} -> {}".format(*key) for key in missing)))


def validate_file(input_path):
    """Read an existing regular UTF-8 JSON file without modifying it."""
    path = Path(input_path)
    _require(not path.is_symlink(), "input path must not be a symbolic link: {}".format(path))
    _require(path.exists(), "input file does not exist: {}".format(path))
    _require(stat.S_ISREG(path.stat().st_mode), "input path is not a regular file: {}".format(path))
    _require(path.stat().st_size > 0, "input file is empty: {}".format(path))
    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise ValidationError("input is not valid UTF-8: {}".format(error))
    try:
        workspace = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValidationError("input is not valid JSON at line {}, column {}: {}".format(error.lineno, error.colno, error.msg))
    validate_workspace(workspace)


def main(argv=None):
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) != 1:
        print("Usage: python3 scripts/validate-container-layout.py WORKSPACE_JSON", file=sys.stderr)
        return 2
    try:
        validate_file(arguments[0])
    except (ValidationError, OSError) as error:
        print("Error: {}".format(error), file=sys.stderr)
        return 1
    print("Container layout validation succeeded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
