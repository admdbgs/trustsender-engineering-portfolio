"""Permanent synthetic tests for the Container View layout transformer."""

import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock


SCRIPT = Path(__file__).parents[1] / "scripts" / "apply-container-layout.py"
SPEC = importlib.util.spec_from_file_location("apply_container_layout", SCRIPT)
layout = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(layout)


PREVIOUS_ROUTES = {
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
    ("Job Control Plane", "Distributed P1 Worker Plane"): (
        45, [(3330, 1650), (3330, 1050)]),
    ("Distributed P1 Worker Plane", "Internet Mail Infrastructure"): (
        55, [(4130, 1050), (4130, 1400)]),
    ("Distributed P1 Worker Plane", "Job Control Plane"): (
        65, [(3270, 1050), (3270, 1650)]),
    ("Job Control Plane", "P2 SMTP Execution Plane"): (35, [(3330, 1680)]),
    ("P2 SMTP Execution Plane", "Internet Mail Infrastructure"): (
        45, [(4210, 1750), (4210, 1400)]),
    ("P2 SMTP Execution Plane", "Job Control Plane"): (55, [(3330, 1760)]),
}


def fixture():
    """Return a sanitized workspace using deliberately arbitrary generated IDs."""
    people = [
        {"id": "person-z91", "name": "Customer", "relationships": []},
        {"id": "person-a07", "name": "Platform Operator", "relationships": []},
    ]
    external_names = [
        "Google Identity", "Microsoft Identity", "Stripe", "Brevo",
        "Internet Mail Infrastructure", "GitHub Actions",
    ]
    systems = [
        {"id": "external-{}".format(index), "name": name, "relationships": []}
        for index, name in enumerate(external_names, 41)
    ]
    container_names = [
        "Edge and Routing", "Web Application", "Application API",
        "PostgreSQL Database", "Job Control Plane",
        "Distributed P1 Worker Plane", "P2 SMTP Execution Plane",
        "WordPress Blog",
    ]
    containers = []
    for index, name in enumerate(container_names, 301):
        record = {"id": "container-q{}".format(index), "name": name,
                  "description": "Synthetic public test description.",
                  "tags": "Operational", "relationships": []}
        if name == "P2 SMTP Execution Plane":
            record["description"] = "Status: ONGOING. Synthetic public test description."
            record["tags"] = "Ongoing"
        containers.append(record)
    internal = {"id": "system-internal-808", "name": "TrustSender.io",
                "containers": containers, "relationships": []}
    systems.append(internal)

    visible = people + containers + systems[:5]
    route_names = list(layout.ROUTES)
    relationship_pairs = []
    for source_name, destination_name in route_names:
        source = next(item for item in visible if item["name"] == source_name)
        destination = next(item for item in visible if item["name"] == destination_name)
        tags = ("Ongoing" if "P2 SMTP Execution Plane" in
                (source["name"], destination["name"]) else "Operational")
        relationship_pairs.append((source, destination, tags))
    relationships = []
    for index, (source, destination, tags) in enumerate(relationship_pairs, 701):
        relationship = {
            "id": "relationship-r{}".format(index),
            "sourceId": source["id"], "destinationId": destination["id"],
            "tags": tags,
        }
        source["relationships"].append(relationship)
        relationships.append(relationship)

    context = {
        "key": "trustsender-system-context", "automaticLayout": {"rankDirection": "LeftRight"},
        "elements": [{"id": item["id"]} for item in people + systems],
        "relationships": [], "title": "Synthetic context",
    }
    container_view = {
        "key": "trustsender-container-view", "automaticLayout": {"rankDirection": "LeftRight"},
        "dimensions": {"width": 2000, "height": 2000},
        "elements": [{"id": item["id"], "x": -1, "y": -1} for item in visible],
        "relationships": [
            {"id": item["id"], "routing": "Direct", "position": -99,
             "vertices": [{"x": 9, "y": 8}], "opacity": 73}
            for item in relationships
        ],
        "title": "Synthetic containers", "paperSize": "A4_Landscape",
    }
    return {
        "id": 1234,
        "model": {"people": people, "softwareSystems": systems},
        "views": {"systemContextViews": [context], "containerViews": [container_view],
                  "configuration": {"branding": {}}},
    }


def named(workspace, name):
    for person in workspace["model"]["people"]:
        if person["name"] == name:
            return person
    for system in workspace["model"]["softwareSystems"]:
        if system["name"] == name:
            return system
        for container in system.get("containers", []):
            if container["name"] == name:
                return container
    raise AssertionError("missing synthetic element {}".format(name))


def container_view(workspace):
    return workspace["views"]["containerViews"][0]


def model_relationship(workspace, identifier):
    owners = list(workspace["model"]["people"])
    for system in workspace["model"]["softwareSystems"]:
        owners.append(system)
        owners.extend(system.get("containers", []))
    for owner in owners:
        for relationship in owner.get("relationships", []):
            if relationship["id"] == identifier:
                return relationship
    raise AssertionError("missing synthetic relationship {}".format(identifier))


class LayoutTransformerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def write(self, workspace=None, name="input.json"):
        path = self.directory / name
        path.write_text(json.dumps(fixture() if workspace is None else workspace), encoding="utf-8")
        return path

    def assert_rejected(self, workspace, pattern):
        source = self.write(workspace)
        with self.assertRaisesRegex(layout.LayoutError, pattern):
            layout.apply_layout(source, self.directory / "output.json")

    def test_positive_transformation_and_preservation(self):
        original = fixture()
        expected_input = copy.deepcopy(original)
        source = self.write(original)
        original_bytes = source.read_bytes()
        first = self.directory / "first.json"
        second = self.directory / "second.json"
        layout.apply_layout(source, first)
        layout.apply_layout(source, second)
        transformed = json.loads(first.read_text(encoding="utf-8"))
        original_container = container_view(original)
        result_container = container_view(transformed)

        self.assertEqual(original["model"], transformed["model"])
        self.assertEqual(original["views"]["systemContextViews"],
                         transformed["views"]["systemContextViews"])
        self.assertEqual([item["id"] for item in original_container["elements"]],
                         [item["id"] for item in result_container["elements"]])
        self.assertEqual([item["id"] for item in original_container["relationships"]],
                         [item["id"] for item in result_container["relationships"]])
        self.assertNotIn("automaticLayout", result_container)
        self.assertEqual({"width": 5000, "height": 2200},
                         result_container["dimensions"])
        self.assertIn("automaticLayout", transformed["views"]["systemContextViews"][0])
        id_to_name = {named(original, name)["id"]: name for name in layout.LAYOUT}
        for member in result_container["elements"]:
            expected = layout.LAYOUT[id_to_name[member["id"]]]
            self.assertEqual(expected, (member["x"], member["y"],
                                        member["width"], member["height"]))
        for source_member, result_member in zip(original_container["relationships"],
                                                result_container["relationships"]):
            relationship = model_relationship(original, source_member["id"])
            route_key = (next(name for name in layout.LAYOUT
                              if named(original, name)["id"] == relationship["sourceId"]),
                         next(name for name in layout.LAYOUT
                              if named(original, name)["id"] == relationship["destinationId"]))
            position, vertices = layout.ROUTES[route_key]
            self.assertEqual("Orthogonal", result_member["routing"])
            self.assertEqual(position, result_member["position"])
            self.assertEqual([{"x": x, "y": y} for x, y in vertices],
                             result_member["vertices"])
            self.assertEqual(73, result_member["opacity"])
            self.assertEqual({key: value for key, value in source_member.items()
                              if key not in {"routing", "position", "vertices"}},
                             {key: value for key, value in result_member.items()
                              if key not in {"routing", "position", "vertices"}})
        self.assertEqual(first.read_bytes(), second.read_bytes())
        third = self.directory / "third.json"
        layout.apply_layout(first, third)
        self.assertEqual(first.read_bytes(), third.read_bytes())
        self.assertTrue(first.read_bytes().endswith(b"\n"))
        self.assertFalse(first.read_bytes().endswith(b"\n\n"))
        self.assertEqual(original_bytes, source.read_bytes())
        self.assertEqual(expected_input, original)

    def test_source_dimensions_with_extra_field_are_replaced(self):
        value = fixture()
        container_view(value)["dimensions"]["units"] = "px"
        transformed = layout.transform(value)
        self.assertEqual({"width": 5000, "height": 2200},
                         container_view(transformed)["dimensions"])

    def test_boolean_source_dimensions_are_replaced(self):
        value = fixture()
        container_view(value)["dimensions"] = {"width": True, "height": False}
        transformed = layout.transform(value)
        self.assertEqual({"width": 5000, "height": 2200},
                         container_view(transformed)["dimensions"])

    def test_preservation_gate_rejects_unrelated_container_view_change(self):
        real_deepcopy = copy.deepcopy

        def altered_deepcopy(value):
            result = real_deepcopy(value)
            container_view(result)["title"] = "Unauthorized title change"
            return result

        with mock.patch.object(layout.copy, "deepcopy", side_effect=altered_deepcopy):
            with self.assertRaisesRegex(
                    layout.LayoutError,
                    "preservation gate failed: unrelated Container View field changed"):
                layout.transform(fixture())

    def test_unexpected_directional_relationship_pair(self):
        value = fixture()
        relationship = model_relationship(value, container_view(value)["relationships"][0]["id"])
        relationship["destinationId"] = named(value, "Web Application")["id"]
        self.assert_rejected(value, "unexpected:.*Customer -> Web Application")

    def test_reversed_directional_relationship(self):
        value = fixture()
        identifier = container_view(value)["relationships"][0]["id"]
        relationship = model_relationship(value, identifier)
        relationship["sourceId"], relationship["destinationId"] = (relationship["destinationId"],
                                                                    relationship["sourceId"])
        self.assert_rejected(value, "unexpected:.*Edge and Routing -> Customer")

    def test_duplicate_directional_relationship_pair(self):
        value = fixture()
        first = model_relationship(value, container_view(value)["relationships"][0]["id"])
        second = model_relationship(value, container_view(value)["relationships"][1]["id"])
        second["sourceId"] = first["sourceId"]
        second["destinationId"] = first["destinationId"]
        self.assert_rejected(value, "duplicate directional relationship Customer -> Edge and Routing")

    def test_missing_expected_directional_relationship(self):
        value = fixture()
        relationship = model_relationship(value, container_view(value)["relationships"][0]["id"])
        relationship["destinationId"] = named(value, "Web Application")["id"]
        self.assert_rejected(value, "missing:.*Customer -> Edge and Routing")

    def test_route_registry_structural_integrity(self):
        self.assertEqual(19, len(layout.ROUTES))
        for key, (position, vertices) in layout.ROUTES.items():
            self.assertEqual(2, len(key))
            self.assertTrue(all(isinstance(name, str) and name for name in key))
            self.assertNotIn("GitHub Actions", key)
            self.assertIn(position, {35, 45, 55, 60, 65, 76, 78})
            self.assertGreaterEqual(len(vertices), 1)
            for vertex in vertices:
                self.assertEqual(2, len(vertex))
                self.assertTrue(all(type(coordinate) is int for coordinate in vertex))
                x, y = vertex
                for left, top, width, height in layout.LAYOUT.values():
                    self.assertFalse(left < x < left + width and top < y < top + height)

    def test_microsoft_identity_route_position_and_vertices(self):
        self.assertEqual(
            (60, [(2180, 500), (2110, 500)]),
            layout.ROUTES[("Application API", "Microsoft Identity")],
        )

    def test_stripe_route_position_and_vertices(self):
        self.assertEqual(
            (78, [(2380, 440), (2610, 440)]),
            layout.ROUTES[("Application API", "Stripe")],
        )

    def test_brevo_route_position_and_vertices(self):
        self.assertEqual(
            (76, [(2480, 500), (3110, 500)]),
            layout.ROUTES[("Application API", "Brevo")],
        )

    def test_google_identity_route_position_and_vertices(self):
        self.assertEqual(
            (65, [(2080, 560), (1610, 560)]),
            layout.ROUTES[("Application API", "Google Identity")],
        )

    def test_only_three_external_label_positions_changed_from_previous_routes(self):
        expected_position_changes = {
            ("Application API", "Microsoft Identity"): (35, 60),
            ("Application API", "Stripe"): (45, 78),
            ("Application API", "Brevo"): (55, 76),
        }

        self.assertEqual(19, len(PREVIOUS_ROUTES))
        self.assertEqual(19, len(layout.ROUTES))
        self.assertEqual(set(PREVIOUS_ROUTES), set(layout.ROUTES))

        position_changes = {
            key: (PREVIOUS_ROUTES[key][0], layout.ROUTES[key][0])
            for key in PREVIOUS_ROUTES
            if PREVIOUS_ROUTES[key][0] != layout.ROUTES[key][0]
        }
        vertex_changes = {
            key for key in PREVIOUS_ROUTES
            if PREVIOUS_ROUTES[key][1] != layout.ROUTES[key][1]
        }
        self.assertEqual(expected_position_changes, position_changes)
        self.assertEqual(set(), vertex_changes)

        google_key = ("Application API", "Google Identity")
        self.assertEqual(PREVIOUS_ROUTES[google_key], layout.ROUTES[google_key])
        unchanged_keys = set(PREVIOUS_ROUTES) - set(expected_position_changes)
        self.assertEqual(16, len(unchanged_keys))
        self.assertEqual(
            {key: PREVIOUS_ROUTES[key] for key in unchanged_keys},
            {key: layout.ROUTES[key] for key in unchanged_keys},
        )

    def test_invalid_json(self):
        source = self.directory / "input.json"
        source.write_text("{not json", encoding="utf-8")
        with self.assertRaisesRegex(layout.LayoutError, "not valid JSON"):
            layout.apply_layout(source, self.directory / "output.json")

    def test_missing_container_view(self):
        value = fixture()
        value["views"]["containerViews"] = []
        self.assert_rejected(value, "exactly one Container View")

    def test_duplicate_required_name(self):
        value = fixture()
        named(value, "GitHub Actions")["name"] = "Customer"
        self.assert_rejected(value, "Customer.*exactly once")

    def test_incorrect_person_type(self):
        value = fixture()
        named(value, "Customer")["name"] = "Former Customer"
        named(value, "GitHub Actions")["name"] = "Customer"
        self.assert_rejected(value, "Customer.*must be a Person")

    def test_incorrect_external_software_system_type(self):
        value = fixture()
        named(value, "Google Identity")["name"] = "Former Google"
        named(value, "WordPress Blog")["name"] = "Google Identity"
        self.assert_rejected(value, "Google Identity.*SoftwareSystem")

    def test_incorrect_internal_container_type(self):
        value = fixture()
        internal = named(value, "TrustSender.io")
        edge = named(value, "Edge and Routing")
        internal["containers"].remove(edge)
        internal["containers"].append({"id": "replacement-edge-owner",
                                       "name": "Replacement Container",
                                       "relationships": [], "components": [edge]})
        self.assert_rejected(value, "Edge and Routing.*Container")

    def test_internal_container_owned_by_another_system(self):
        value = fixture()
        internal = named(value, "TrustSender.io")
        edge = named(value, "Edge and Routing")
        internal["containers"].remove(edge)
        internal["containers"].append({"id": "placeholder-19", "name": "Placeholder",
                                       "relationships": []})
        named(value, "GitHub Actions")["containers"] = [edge]
        self.assert_rejected(value, "Edge and Routing.*directly owned")

    def test_eighteen_container_view_relationships(self):
        value = fixture()
        container_view(value)["relationships"].pop()
        self.assert_rejected(value, "exactly 19 relationships")

    def test_twenty_container_view_relationships(self):
        value = fixture()
        container_view(value)["relationships"].append({"id": "relationship-r701"})
        self.assert_rejected(value, "exactly 19 relationships")

    def test_unresolved_container_view_element_id(self):
        value = fixture()
        container_view(value)["elements"][0]["id"] = "missing-element-999"
        self.assert_rejected(value, "unresolved Container View element ID")

    def test_unresolved_container_view_relationship_id(self):
        value = fixture()
        container_view(value)["relationships"][0]["id"] = "missing-relationship-999"
        self.assert_rejected(value, "unresolved Container View relationship ID")

    def test_duplicate_container_view_relationship_id(self):
        value = fixture()
        records = container_view(value)["relationships"]
        records[1]["id"] = records[0]["id"]
        self.assert_rejected(value, "duplicate Container View relationship membership")

    def test_github_actions_in_container_view(self):
        value = fixture()
        container_view(value)["elements"][0]["id"] = named(value, "GitHub Actions")["id"]
        self.assert_rejected(value, "must not include the GitHub Actions")

    def test_missing_github_actions_software_system(self):
        value = fixture()
        named(value, "GitHub Actions")["name"] = "Arbitrary Seventh System"
        self.assert_rejected(value, "GitHub Actions.*exactly once")

    def test_container_view_relationship_source_outside_view(self):
        value = fixture()
        identifier = container_view(value)["relationships"][0]["id"]
        github_id = named(value, "GitHub Actions")["id"]
        model_relationship(value, identifier)["sourceId"] = github_id
        self.assert_rejected(
            value, "relationship {} has endpoint {} outside".format(identifier, github_id))

    def test_container_view_relationship_destination_outside_view(self):
        value = fixture()
        identifier = container_view(value)["relationships"][0]["id"]
        github_id = named(value, "GitHub Actions")["id"]
        model_relationship(value, identifier)["destinationId"] = github_id
        self.assert_rejected(
            value, "relationship {} has endpoint {} outside".format(identifier, github_id))

    def test_p2_missing_ongoing_tag(self):
        value = fixture()
        named(value, "P2 SMTP Execution Plane")["tags"] = ""
        self.assert_rejected(value, "must have the Ongoing tag")

    def test_p2_containing_operational_tag(self):
        value = fixture()
        named(value, "P2 SMTP Execution Plane")["tags"] = "Ongoing,Operational"
        self.assert_rejected(value, "must not have the Operational tag")

    def test_p2_description_missing_marker(self):
        value = fixture()
        named(value, "P2 SMTP Execution Plane")["description"] = "ONGOING"
        self.assert_rejected(value, "description must contain.*exactly once")

    def test_p2_description_marker_twice(self):
        value = fixture()
        named(value, "P2 SMTP Execution Plane")["description"] = (
            "Status: ONGOING. Synthetic. Status: ONGOING.")
        self.assert_rejected(value, "description must contain.*exactly once")

    def test_p2_relationship_missing_ongoing(self):
        value = fixture()
        p2 = named(value, "P2 SMTP Execution Plane")
        p2["relationships"][0]["tags"] = ""
        self.assert_rejected(value, "P2 relationship.*must have the Ongoing")

    def test_p2_relationship_containing_operational(self):
        value = fixture()
        p2 = named(value, "P2 SMTP Execution Plane")
        p2["relationships"][0]["tags"] = "Ongoing,Operational"
        self.assert_rejected(value, "P2 relationship.*must not have the Operational")

    def test_identical_input_and_output_paths(self):
        source = self.write()
        with self.assertRaisesRegex(layout.LayoutError, "must be different"):
            layout.apply_layout(source, source)

    def test_symbolic_link_input(self):
        source = self.write()
        link = self.directory / "input-link.json"
        try:
            link.symlink_to(source)
        except (NotImplementedError, OSError) as error:
            self.skipTest("symbolic links are unavailable: {}".format(error))
        with self.assertRaisesRegex(layout.LayoutError, "input path must not be a symbolic link"):
            layout.apply_layout(link, self.directory / "output.json")

    def test_symbolic_link_output(self):
        source = self.write()
        target = self.directory / "target.json"
        target.write_text("existing", encoding="utf-8")
        link = self.directory / "output-link.json"
        try:
            link.symlink_to(target)
        except (NotImplementedError, OSError) as error:
            self.skipTest("symbolic links are unavailable: {}".format(error))
        with self.assertRaisesRegex(layout.LayoutError, "output path must not be a symbolic link"):
            layout.apply_layout(source, link)


if __name__ == "__main__":
    unittest.main()
