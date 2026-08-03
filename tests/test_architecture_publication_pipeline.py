import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / ".github/workflows/architecture-ci.yml").read_text(encoding="utf-8")
RENDER_SCRIPT = (ROOT / "scripts/render-architecture.sh").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")


class ArchitecturePublicationPipelineTests(unittest.TestCase):
    def test_workflow_invokes_official_render_script(self):
        self.assertIn("bash scripts/render-architecture.sh", WORKFLOW)

    def test_workflow_does_not_invoke_deleted_script(self):
        self.assertNotIn("build-container-layout-candidate.sh", WORKFLOW)

    def test_workflow_contains_official_artifact_name(self):
        self.assertEqual(WORKFLOW.count("name: trustsender-architecture-dark-svg"), 1)

    def test_workflow_does_not_contain_retired_artifact_name(self):
        self.assertNotIn("trustsender-container-layout-candidate", WORKFLOW)

    def test_workflow_uploads_exactly_four_official_svgs(self):
        self.assertIn("path: build/architecture-svg/*.svg", WORKFLOW)
        self.assertIn('if [[ "${#svg_files[@]}" -ne 4 ]]', WORKFLOW)

    def test_render_script_exports_dsl_to_source_json(self):
        self.assertIn("SOURCE_JSON_DIRECTORY=\"build/architecture-layout/source-json\"", RENDER_SCRIPT)
        self.assertRegex(RENDER_SCRIPT, r"-workspace architecture/workspace\.dsl\s+\\\n\s+-format json")

    def test_render_script_applies_container_layout(self):
        self.assertIn("python3 scripts/apply-container-layout.py", RENDER_SCRIPT)

    def test_render_script_validates_transformed_workspace_twice(self):
        self.assertIn('python3 scripts/validate-architecture-json.py "${TRANSFORMED_WORKSPACE}"', RENDER_SCRIPT)
        self.assertIn('python3 scripts/validate-container-layout.py "${TRANSFORMED_WORKSPACE}"', RENDER_SCRIPT)

    def test_render_command_uses_transformed_json_workspace(self):
        render_block = RENDER_SCRIPT.split('"${RENDER_IMAGE}"', 1)[1]
        self.assertIn('-workspace "${TRANSFORMED_WORKSPACE}"', render_block)
        self.assertNotIn("-workspace architecture/workspace.dsl", render_block)

    def test_render_script_requires_exact_canvas(self):
        self.assertIn('require_dimension("width", 5000)', RENDER_SCRIPT)
        self.assertIn('require_dimension("height", 2200)', RENDER_SCRIPT)
        self.assertIn('normalized_view_box != "0 0 5000 2200"', RENDER_SCRIPT)

    def test_render_script_protects_architecture_and_diagrams(self):
        self.assertIn("git status --porcelain=v1 -uall -- architecture diagrams", RENDER_SCRIPT)
        self.assertIn("generated content was written under architecture/ or diagrams/", RENDER_SCRIPT)

    def test_retired_script_no_longer_exists(self):
        self.assertFalse((ROOT / "scripts/build-container-layout-candidate.sh").exists())

    def test_retired_artifact_absent_from_official_contracts(self):
        retired_name = "trustsender-container-layout-" + "candidate"
        self.assertNotIn(retired_name, WORKFLOW)
        self.assertNotIn(retired_name, RENDER_SCRIPT)

    def test_readme_describes_official_transformed_layout_previews(self):
        section = README.split("## Architecture validation", 1)[1].split("## Roadmap", 1)[0]
        self.assertIn("canonical Structurizr DSL", section)
        self.assertIn("compiles it to JSON", section)
        self.assertIn("applies the reviewed deterministic Container View layout", section)
        self.assertIn("validates the transformed workspace", section)
        self.assertIn("official dark-mode architecture previews", section)
        self.assertNotRegex(section, re.compile(r"Container View SVG (?:is|has been) committed"))


if __name__ == "__main__":
    unittest.main()
