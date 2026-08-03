"""Independent synthetic tests for the final Container View validator."""

import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).parents[1] / "scripts" / "validate-container-layout.py"
SPEC = importlib.util.spec_from_file_location("validate_container_layout", SCRIPT)
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)

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
ROUTES = [
    ("Customer", "Edge and Routing", 35, [(560, 900), (560, 1190)]),
    ("Platform Operator", "Edge and Routing", 45, [(620, 1700), (620, 1310)]),
    ("Edge and Routing", "Web Application", 55, [(1230, 1180), (1230, 800)]),
    ("Edge and Routing", "Application API", 65, [(1600, 1250)]),
    ("Edge and Routing", "WordPress Blog", 35, [(1290, 1320), (1290, 1650)]),
    ("Web Application", "Application API", 45, [(1930, 800), (1930, 1180)]),
    ("Application API", "PostgreSQL Database", 55, [(2630, 1250), (2630, 810)]),
    ("Application API", "Google Identity", 65, [(2080, 560), (1610, 560)]),
    ("Application API", "Microsoft Identity", 60, [(2180, 500), (2110, 500)]),
    ("Application API", "Stripe", 78, [(2380, 440), (2610, 440)]),
    ("Application API", "Brevo", 76, [(2480, 500), (3110, 500)]),
    ("Application API", "Job Control Plane", 65, [(2280, 1450), (2980, 1450)]),
    ("Job Control Plane", "PostgreSQL Database", 35, [(3050, 1235)]),
    ("Job Control Plane", "Distributed P1 Worker Plane", 45, [(3330, 1650), (3330, 1050)]),
    ("Distributed P1 Worker Plane", "Internet Mail Infrastructure", 55, [(4130, 1050), (4130, 1400)]),
    ("Distributed P1 Worker Plane", "Job Control Plane", 65, [(3270, 1050), (3270, 1650)]),
    ("Job Control Plane", "P2 SMTP Execution Plane", 35, [(3330, 1680)]),
    ("P2 SMTP Execution Plane", "Internet Mail Infrastructure", 45, [(4210, 1750), (4210, 1400)]),
    ("P2 SMTP Execution Plane", "Job Control Plane", 55, [(3330, 1760)]),
]


def fixture(prefix="alpha"):
    people = [{"id": prefix + "-p1", "name": "Customer", "relationships": []},
              {"id": prefix + "-p2", "name": "Platform Operator", "relationships": []}]
    externals = ["Google Identity", "Microsoft Identity", "Stripe", "Brevo",
                 "Internet Mail Infrastructure", "GitHub Actions"]
    systems = [{"id": "{}-s{}".format(prefix, index), "name": name, "relationships": []}
               for index, name in enumerate(externals)]
    container_names = ["Edge and Routing", "Web Application", "Application API",
                       "PostgreSQL Database", "Job Control Plane", "Distributed P1 Worker Plane",
                       "P2 SMTP Execution Plane", "WordPress Blog"]
    containers = []
    for index, name in enumerate(container_names):
        containers.append({"id": "{}-c{}".format(prefix, index), "name": name,
                           "description": ("Status: ONGOING. Will execute conservative SMTP "
                                           "recipient-handshake stages for eligible recipients "
                                           "and return typed evidence to the central control plane."
                                           if name == "P2 SMTP Execution Plane" else "Synthetic."),
                           "tags": "Ongoing" if name == "P2 SMTP Execution Plane" else "Operational",
                           "relationships": [], "components": []})
    internal = {"id": prefix + "-internal", "name": "TrustSender.io",
                "containers": containers, "relationships": []}
    systems.append(internal)
    all_named = {item["name"]: item for item in people + systems + containers}
    relationships = []
    for index, (source, destination, position, points) in enumerate(ROUTES):
        record = {"id": "{}-r{}".format(prefix, index),
                  "sourceId": all_named[source]["id"], "destinationId": all_named[destination]["id"],
                  "tags": "Ongoing" if "P2 SMTP Execution Plane" in (source, destination) else "Operational"}
        all_named[source]["relationships"].append(record)
        relationships.append((record, position, points))
    visible = [all_named[name] for name in LAYOUT]
    return {"model": {"people": people, "softwareSystems": systems},
            "views": {"systemContextViews": [{"key": "trustsender-system-context",
                                                "softwareSystemId": internal["id"],
                                                "automaticLayout": {"rankDirection": "LeftRight"}}],
                      "containerViews": [{"key": "trustsender-container-view",
                          "softwareSystemId": internal["id"],
                          "dimensions": {"width": 5000, "height": 2200},
                          "elements": [{"id": item["id"], "x": LAYOUT[item["name"]][0],
                                        "y": LAYOUT[item["name"]][1], "width": LAYOUT[item["name"]][2],
                                        "height": LAYOUT[item["name"]][3]} for item in visible],
                          "relationships": [{"id": record["id"], "routing": "Orthogonal", "position": position,
                                             "vertices": [{"x": x, "y": y} for x, y in points]}
                                            for record, position, points in relationships]}]}}


def named(value, name):
    for item in value["model"]["people"] + value["model"]["softwareSystems"]:
        if item["name"] == name:
            return item
        for child in item.get("containers", []):
            if child["name"] == name:
                return child
    raise AssertionError(name)


def view(value):
    return value["views"]["containerViews"][0]


def relationship_membership(value, source_name, destination_name):
    source_id = named(value, source_name)["id"]
    destination_id = named(value, destination_name)["id"]
    model_matches = [
        relationship
        for relationship in named(value, source_name).get("relationships", [])
        if relationship["sourceId"] == source_id
        and relationship["destinationId"] == destination_id
    ]
    if len(model_matches) != 1:
        raise AssertionError(
            "expected one {} -> {} model relationship".format(
                source_name, destination_name))
    relationship_id = model_matches[0]["id"]
    membership_matches = [
        member for member in view(value)["relationships"]
        if member["id"] == relationship_id
    ]
    if len(membership_matches) != 1:
        raise AssertionError(
            "expected one {} -> {} Container View membership".format(
                source_name, destination_name))
    return membership_matches[0]


class ContainerLayoutValidatorTests(unittest.TestCase):
    def reject(self, value, pattern):
        with self.assertRaisesRegex(validator.ValidationError, pattern):
            validator.validate_workspace(value)

    def test_valid_canonical_fixture(self):
        validator.validate_workspace(fixture())

    def test_valid_different_generated_ids(self):
        validator.validate_workspace(fixture("unrelated-zeta-904"))

    def test_valid_reordered_memberships(self):
        value = fixture()
        view(value)["elements"].reverse()
        view(value)["relationships"].reverse()
        validator.validate_workspace(value)

    def test_invalid_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text("{bad", encoding="utf-8")
            with self.assertRaisesRegex(validator.ValidationError, "not valid JSON"):
                validator.validate_file(path)

    def test_symbolic_link_input(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target.json"
            target.write_text(json.dumps(fixture()), encoding="utf-8")
            link = Path(directory) / "link.json"
            link.symlink_to(target)
            with self.assertRaisesRegex(validator.ValidationError, "symbolic link"):
                validator.validate_file(link)

    def test_missing_container_view(self):
        value = fixture(); value["views"]["containerViews"] = []
        self.reject(value, "exactly one Container View")

    def test_container_automatic_layout(self):
        value = fixture(); view(value)["automaticLayout"] = {}
        self.reject(value, "must not contain automaticLayout")

    def test_missing_dimensions(self):
        value = fixture(); del view(value)["dimensions"]
        self.reject(value, "dimensions must be an object")

    def test_dimensions_not_an_object(self):
        value = fixture(); view(value)["dimensions"] = "5000x2200"
        self.reject(value, "dimensions must be an object")

    def test_dimensions_missing_width(self):
        value = fixture(); del view(value)["dimensions"]["width"]
        self.reject(value, "exactly width and height")

    def test_dimensions_missing_height(self):
        value = fixture(); del view(value)["dimensions"]["height"]
        self.reject(value, "exactly width and height")

    def test_incorrect_dimensions_width(self):
        value = fixture(); view(value)["dimensions"]["width"] = 4999
        self.reject(value, "width 4999 must equal 5000")

    def test_incorrect_dimensions_height(self):
        value = fixture(); view(value)["dimensions"]["height"] = 2199
        self.reject(value, "height 2199 must equal 2200")

    def test_boolean_dimensions_width(self):
        value = fixture(); view(value)["dimensions"]["width"] = True
        self.reject(value, "width True must equal 5000")

    def test_boolean_dimensions_height(self):
        value = fixture(); view(value)["dimensions"]["height"] = False
        self.reject(value, "height False must equal 2200")

    def test_extra_dimensions_field(self):
        value = fixture(); view(value)["dimensions"]["units"] = "px"
        self.reject(value, "exactly width and height")

    def test_context_automatic_layout_missing(self):
        value = fixture(); del value["views"]["systemContextViews"][0]["automaticLayout"]
        self.reject(value, "automaticLayout must be non-null")

    def test_wrong_element_count(self):
        value = fixture(); view(value)["elements"].pop()
        self.reject(value, "exactly 15 elements")

    def test_wrong_relationship_count(self):
        value = fixture(); view(value)["relationships"].pop()
        self.reject(value, "exactly 19 relationships")

    def test_duplicate_element_membership(self):
        value = fixture(); view(value)["elements"][-1] = copy.deepcopy(view(value)["elements"][0])
        self.reject(value, "duplicate Container View element")

    def test_unresolved_element_membership(self):
        value = fixture(); view(value)["elements"][0]["id"] = "unknown"
        self.reject(value, "unresolved Container View element")

    def test_missing_required_model_element(self):
        value = fixture(); named(value, "Customer")["name"] = "Absent"
        self.reject(value, "Customer.*exactly once")

    def test_incorrect_c4_type(self):
        value = fixture(); named(value, "Customer")["name"] = "Former"; named(value, "GitHub Actions")["name"] = "Customer"
        self.reject(value, "must be a Person")

    def test_incorrect_container_ownership(self):
        value = fixture(); item = named(value, "WordPress Blog"); named(value, "TrustSender.io")["containers"].remove(item); named(value, "GitHub Actions")["containers"] = [item]
        self.reject(value, "directly own exactly 8")

    def test_github_actions_in_view(self):
        value = fixture(); member = view(value)["elements"][-1]; member["id"] = named(value, "GitHub Actions")["id"]
        self.reject(value, "unexpected Container View element|GitHub Actions")

    def test_invalid_p2_tags(self):
        value = fixture(); named(value, "P2 SMTP Execution Plane")["tags"] = "Operational"
        self.reject(value, "status tags are invalid")

    def test_invalid_p2_marker(self):
        value = fixture(); named(value, "P2 SMTP Execution Plane")["description"] = "Synthetic"
        self.reject(value, "exact approved ONGOING description")

    def test_p2_description_rejects_operational_appendix(self):
        value = fixture()
        named(value, "P2 SMTP Execution Plane")["description"] += " SMTP validation is fully operational."
        self.reject(value, "exact approved ONGOING description")

    def test_p2_description_rejects_noncanonical_text_with_marker(self):
        value = fixture()
        named(value, "P2 SMTP Execution Plane")["description"] = "Status: ONGOING. Different wording."
        self.reject(value, "exact approved ONGOING description")

    def test_context_view_missing_software_system_id(self):
        value = fixture()
        del value["views"]["systemContextViews"][0]["softwareSystemId"]
        self.reject(value, "trustsender-system-context.*softwareSystemId None.*TrustSender.io ID")

    def test_context_view_wrong_software_system_id(self):
        value = fixture()
        value["views"]["systemContextViews"][0]["softwareSystemId"] = named(value, "Google Identity")["id"]
        self.reject(value, "trustsender-system-context.*softwareSystemId.*TrustSender.io ID")

    def test_container_view_missing_software_system_id(self):
        value = fixture()
        del view(value)["softwareSystemId"]
        self.reject(value, "trustsender-container-view.*softwareSystemId None.*TrustSender.io ID")

    def test_container_view_wrong_software_system_id(self):
        value = fixture()
        view(value)["softwareSystemId"] = named(value, "Google Identity")["id"]
        self.reject(value, "trustsender-container-view.*softwareSystemId.*TrustSender.io ID")

    def test_relationship_endpoint_outside_view(self):
        value = fixture(); named(value, "Customer")["relationships"][0]["sourceId"] = named(value, "GitHub Actions")["id"]
        self.reject(value, "endpoint outside Container View")

    def test_reversed_directional_route(self):
        value = fixture(); item = named(value, "Customer")["relationships"][0]; item["sourceId"], item["destinationId"] = item["destinationId"], item["sourceId"]
        self.reject(value, "unexpected directional route")

    def test_duplicate_directional_route(self):
        value = fixture(); first = named(value, "Customer")["relationships"][0]; second = named(value, "Platform Operator")["relationships"][0]; second["sourceId"], second["destinationId"] = first["sourceId"], first["destinationId"]
        self.reject(value, "duplicate directional route")

    def test_non_orthogonal_routing(self):
        value = fixture(); view(value)["relationships"][0]["routing"] = "Direct"
        self.reject(value, "routing must be Orthogonal")

    def test_wrong_position(self):
        value = fixture(); view(value)["relationships"][0]["position"] = 99
        self.reject(value, "position 99")

    def test_rejects_microsoft_identity_former_position(self):
        value = fixture()
        relationship_membership(
            value, "Application API", "Microsoft Identity")["position"] = 35
        self.reject(value, "position 35 does not equal approved 60")

    def test_rejects_stripe_former_position(self):
        value = fixture()
        relationship_membership(value, "Application API", "Stripe")["position"] = 45
        self.reject(value, "position 45 does not equal approved 78")

    def test_rejects_brevo_former_position(self):
        value = fixture()
        relationship_membership(value, "Application API", "Brevo")["position"] = 55
        self.reject(value, "position 55 does not equal approved 76")

    def test_rejects_google_identity_nonapproved_position(self):
        value = fixture()
        relationship_membership(
            value, "Application API", "Google Identity")["position"] = 64
        self.reject(value, "position 64 does not equal approved 65")

    def test_missing_vertex(self):
        value = fixture(); view(value)["relationships"][0]["vertices"].pop()
        self.reject(value, "vertices do not equal")

    def test_extra_vertex(self):
        value = fixture(); view(value)["relationships"][0]["vertices"].append({"x": 560, "y": 1200})
        self.reject(value, "vertices do not equal")

    def test_reordered_vertices(self):
        value = fixture(); view(value)["relationships"][0]["vertices"].reverse()
        self.reject(value, "vertices do not equal")

    def test_changed_vertex(self):
        value = fixture(); view(value)["relationships"][0]["vertices"][0]["y"] = 901
        self.reject(value, "vertices do not equal")

    def test_non_integer_vertex(self):
        value = fixture(); view(value)["relationships"][0]["vertices"][0]["x"] = 560.0
        self.reject(value, "coordinates must be integers")

    def test_vertex_extra_field(self):
        value = fixture(); view(value)["relationships"][0]["vertices"][0]["z"] = 1
        self.reject(value, "exactly x and y")

    def test_vertex_inside_rectangle_helper(self):
        with self.assertRaisesRegex(validator.ValidationError, "lies inside"):
            validator.validate_geometry([{"x": 101, "y": 701}], "r", "A", "B")

    def test_diagonal_segment_helper(self):
        with self.assertRaisesRegex(validator.ValidationError, "diagonal"):
            validator.validate_geometry([{"x": 0, "y": 0}, {"x": 1, "y": 1}], "r", "A", "B", {})

    def test_crossing_segment_helper(self):
        rectangles = {"box": (10, 10, 20, 20)}
        with self.assertRaisesRegex(validator.ValidationError, "crosses"):
            validator.validate_geometry([{"x": 0, "y": 20}, {"x": 40, "y": 20}], "r", "A", "B", rectangles)

    def test_element_overlap_helper_via_registry_patch(self):
        value = fixture(); original = validator.LAYOUT["Platform Operator"]
        validator.LAYOUT["Platform Operator"] = validator.LAYOUT["Customer"]
        member = next(item for item in view(value)["elements"] if item["id"] == named(value, "Platform Operator")["id"])
        member.update({"x": 100, "y": 700, "width": 400, "height": 400})
        try:
            self.reject(value, "rectangles overlap")
        finally:
            validator.LAYOUT["Platform Operator"] = original

    def test_element_outside_bounds_helper_via_registry_patch(self):
        value = fixture(); original = validator.LAYOUT["Customer"]
        validator.LAYOUT["Customer"] = (-1, 700, 400, 400)
        view(value)["elements"][0]["x"] = -1
        try:
            self.reject(value, "outside approved bounds")
        finally:
            validator.LAYOUT["Customer"] = original

    def test_element_beyond_canvas(self):
        value = fixture()
        view(value)["elements"][0]["x"] = 5001
        self.reject(value, "outside approved bounds")

    def test_vertex_beyond_canvas(self):
        value = fixture()
        view(value)["relationships"][0]["vertices"][0]["x"] = 5001
        self.reject(value, "outside bounds")

    def test_wrong_argument_count(self):
        self.assertEqual(2, validator.main([]))


if __name__ == "__main__":
    unittest.main()
