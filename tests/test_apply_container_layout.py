"""Permanent synthetic tests for the Container View layout transformer."""

import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).parents[1] / "scripts" / "apply-container-layout.py"
SPEC = importlib.util.spec_from_file_location("apply_container_layout", SCRIPT)
layout = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(layout)


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
    relationship_pairs = []
    for index in range(16):
        source = visible[index % len(visible)]
        destination = visible[(index + 1) % len(visible)]
        tags = ("Ongoing" if "P2 SMTP Execution Plane" in
                (source["name"], destination["name"]) else "Operational")
        relationship_pairs.append((source, destination, tags))
    p2 = next(item for item in containers if item["name"] == "P2 SMTP Execution Plane")
    mail = next(item for item in systems if item["name"] == "Internet Mail Infrastructure")
    control = next(item for item in containers if item["name"] == "Job Control Plane")
    relationship_pairs.extend([
        (control, p2, "Ongoing"),
        (p2, mail, "Ongoing"),
        (p2, control, "Ongoing"),
    ])
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
        "elements": [{"id": item["id"], "x": -1, "y": -1} for item in visible],
        "relationships": [
            {"id": item["id"], "routing": "Direct", "vertices": [{"x": 9, "y": 8}]}
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
        self.assertEqual(original_container["relationships"], result_container["relationships"])
        self.assertEqual([item["id"] for item in original_container["elements"]],
                         [item["id"] for item in result_container["elements"]])
        self.assertEqual([item["id"] for item in original_container["relationships"]],
                         [item["id"] for item in result_container["relationships"]])
        self.assertNotIn("automaticLayout", result_container)
        self.assertIn("automaticLayout", transformed["views"]["systemContextViews"][0])
        id_to_name = {named(original, name)["id"]: name for name in layout.LAYOUT}
        for member in result_container["elements"]:
            expected = layout.LAYOUT[id_to_name[member["id"]]]
            self.assertEqual(expected, (member["x"], member["y"],
                                        member["width"], member["height"]))
        self.assertEqual(first.read_bytes(), second.read_bytes())
        self.assertTrue(first.read_bytes().endswith(b"\n"))
        self.assertFalse(first.read_bytes().endswith(b"\n\n"))
        self.assertEqual(original_bytes, source.read_bytes())
        self.assertEqual(expected_input, original)

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
