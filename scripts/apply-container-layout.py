#!/usr/bin/env python3
"""Apply the approved manual element layout to the public Container View."""

import copy
import json
import os
import pathlib
import sys
import tempfile
from typing import Any, Dict, Iterator, List, Tuple


SYSTEM_CONTEXT_KEY = "trustsender-system-context"
CONTAINER_VIEW_KEY = "trustsender-container-view"
LAYOUTS = {
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


class LayoutError(Exception):
    """An expected workspace or filesystem invariant was not satisfied."""


def require_object(value: Any, location: str) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise LayoutError("{} must be an object".format(location))
    return value


def require_array(value: Any, location: str) -> List[Any]:
    if not isinstance(value, list):
        raise LayoutError("{} must be an array".format(location))
    return value


def model_elements(value: Any) -> Iterator[Tuple[Dict[str, Any], str]]:
    """Yield recursively nested model elements and their inferred element type."""
    if not isinstance(value, dict):
        return
    collections = (
        ("people", "Person"),
        ("softwareSystems", "SoftwareSystem"),
        ("containers", "Container"),
        ("components", "Component"),
    )
    for collection, element_type in collections:
        if collection not in value:
            continue
        entries = require_array(value[collection], "model.{}".format(collection))
        for index, entry_value in enumerate(entries):
            entry = require_object(
                entry_value, "model.{}[{}]".format(collection, index)
            )
            yield entry, element_type
            yield from model_elements(entry)


def relationship_count(value: Any) -> int:
    if isinstance(value, dict):
        count = 0
        for key, child in value.items():
            if key == "relationships":
                relationships = require_array(child, "model relationships")
                count += len(relationships)
            else:
                count += relationship_count(child)
        return count
    if isinstance(value, list):
        return sum(relationship_count(child) for child in value)
    return 0


def keyed_view(views: Dict[str, Any], collection: str, key: str) -> Dict[str, Any]:
    entries = require_array(views.get(collection), "views.{}".format(collection))
    matches = []
    for index, value in enumerate(entries):
        view = require_object(value, "views.{}[{}]".format(collection, index))
        if view.get("key") == key:
            matches.append(view)
    if len(matches) != 1:
        raise LayoutError(
            "views.{} must contain exactly one view with key {!r}; found {}".format(
                collection, key, len(matches)
            )
        )
    return matches[0]


def transform(workspace: Any) -> Dict[str, Any]:
    source = require_object(workspace, "root")
    model = require_object(source.get("model"), "model")
    views = require_object(source.get("views"), "views")

    indexed = list(model_elements(model))
    by_id = {}
    by_name = {}
    type_counts = {"Person": 0, "SoftwareSystem": 0}
    for element, element_type in indexed:
        element_id = element.get("id")
        name = element.get("name")
        if not isinstance(element_id, str) or not element_id:
            raise LayoutError("every model element must have a non-empty string id")
        if not isinstance(name, str) or not name:
            raise LayoutError("every model element must have a non-empty string name")
        if element_id in by_id:
            raise LayoutError("duplicate model element id {!r}".format(element_id))
        by_id[element_id] = (element, element_type)
        by_name.setdefault(name, []).append((element, element_type))
        if element_type in type_counts:
            type_counts[element_type] += 1

    if type_counts["Person"] != 2:
        raise LayoutError("model must contain exactly 2 people")
    if type_counts["SoftwareSystem"] != 7:
        raise LayoutError("model must contain exactly 7 software systems")
    trustsender_matches = by_name.get("TrustSender.io", [])
    if len(trustsender_matches) != 1 or trustsender_matches[0][1] != "SoftwareSystem":
        raise LayoutError("model must contain exactly one software system named 'TrustSender.io'")
    trustsender = trustsender_matches[0][0]
    containers = require_array(trustsender.get("containers"), "TrustSender.io containers")
    if len(containers) != 8:
        raise LayoutError("TrustSender.io must contain exactly 8 containers")

    for required_name in LAYOUTS:
        matches = by_name.get(required_name, [])
        if len(matches) != 1:
            raise LayoutError(
                "required model name {!r} must occur exactly once; found {}".format(
                    required_name, len(matches)
                )
            )

    source_context = keyed_view(views, "systemContextViews", SYSTEM_CONTEXT_KEY)
    source_container = keyed_view(views, "containerViews", CONTAINER_VIEW_KEY)
    source_elements = require_array(source_container.get("elements"), "Container View elements")
    source_relationships = require_array(
        source_container.get("relationships"), "Container View relationships"
    )
    if len(source_elements) != 15:
        raise LayoutError("Container View must contain exactly 15 visible elements")

    visible_names = []
    visible_ids = []
    for index, value in enumerate(source_elements):
        view_element = require_object(value, "Container View elements[{}]".format(index))
        element_id = view_element.get("id")
        if not isinstance(element_id, str) or element_id not in by_id:
            raise LayoutError(
                "Container View element at index {} has unresolved id {!r}".format(
                    index, element_id
                )
            )
        visible_ids.append(element_id)
        visible_names.append(by_id[element_id][0]["name"])
    if len(set(visible_ids)) != len(visible_ids):
        raise LayoutError("Container View contains duplicate element membership")
    if "GitHub Actions" in visible_names:
        raise LayoutError("GitHub Actions must be absent from the Container View")
    if set(visible_names) != set(LAYOUTS) or len(visible_names) != len(LAYOUTS):
        missing = sorted(set(LAYOUTS) - set(visible_names))
        unexpected = sorted(set(visible_names) - set(LAYOUTS))
        raise LayoutError(
            "Container View names do not match the required set (missing: {}; unexpected: {})".format(
                missing, unexpected
            )
        )

    result = copy.deepcopy(source)
    result_views = require_object(result["views"], "views")
    result_container = keyed_view(result_views, "containerViews", CONTAINER_VIEW_KEY)
    result_container.pop("automaticLayout", None)
    for view_element in result_container["elements"]:
        name = by_id[view_element["id"]][0]["name"]
        x, y, width, height = LAYOUTS[name]
        view_element.update(x=x, y=y, width=width, height=height)

    result_context = keyed_view(result_views, "systemContextViews", SYSTEM_CONTEXT_KEY)
    if result["model"] != model:
        raise LayoutError("preservation gate failed: model changed")
    if result_context != source_context:
        raise LayoutError("preservation gate failed: System Context View changed")
    if result_container["relationships"] != source_relationships:
        raise LayoutError("preservation gate failed: Container View relationships changed")
    if [entry["id"] for entry in result_container["elements"]] != visible_ids:
        raise LayoutError("preservation gate failed: Container View membership changed")
    if len(result_container["relationships"]) != len(source_relationships):
        raise LayoutError("preservation gate failed: relationship membership changed")
    if len(list(model_elements(result["model"]))) != len(indexed):
        raise LayoutError("preservation gate failed: model element count changed")
    if relationship_count(result["model"]) != relationship_count(model):
        raise LayoutError("preservation gate failed: model relationship count changed")
    return result


def write_atomic(path: pathlib.Path, workspace: Dict[str, Any]) -> None:
    parent = path.parent
    if not parent.is_dir():
        raise LayoutError("output directory does not exist: {}".format(parent))
    descriptor = None
    temporary_name = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".{}-".format(path.name), suffix=".tmp", dir=str(parent)
        )
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as output_file:
            descriptor = None
            json.dump(workspace, output_file, ensure_ascii=False, indent=2)
            output_file.write("\n")
            output_file.flush()
            os.fsync(output_file.fileno())
        os.replace(temporary_name, str(path))
        temporary_name = None
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary_name is not None:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass


def run(input_path: pathlib.Path, output_path: pathlib.Path) -> None:
    if input_path.is_symlink():
        raise LayoutError("input path must not be a symbolic link: {}".format(input_path))
    if not input_path.exists():
        raise LayoutError("input file does not exist: {}".format(input_path))
    if not input_path.is_file():
        raise LayoutError("input path is not a regular file: {}".format(input_path))
    if output_path.is_symlink():
        raise LayoutError("output path must not be a symbolic link: {}".format(output_path))
    if input_path.resolve() == output_path.resolve():
        raise LayoutError("input and output paths must be different")
    if input_path.stat().st_size == 0:
        raise LayoutError("input file is empty: {}".format(input_path))
    try:
        with input_path.open("r", encoding="utf-8") as input_file:
            workspace = json.load(input_file)
    except UnicodeDecodeError as error:
        raise LayoutError("input is not valid UTF-8: {}".format(error))
    except json.JSONDecodeError as error:
        raise LayoutError(
            "input contains invalid JSON at line {}, column {}: {}".format(
                error.lineno, error.colno, error.msg
            )
        )
    write_atomic(output_path, transform(workspace))


def main() -> int:
    if len(sys.argv) != 3:
        print(
            "Error: usage: python3 scripts/apply-container-layout.py INPUT_JSON OUTPUT_JSON",
            file=sys.stderr,
        )
        return 2
    try:
        run(pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]))
    except (LayoutError, OSError) as error:
        print("Error: {}".format(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
