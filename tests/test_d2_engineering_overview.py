"""Tests for the D2 engineering overview preview source and CI integration."""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
D2_SOURCE = ROOT / "visuals" / "trustsender-engineering-overview.d2"
RENDERER = ROOT / "scripts" / "render-d2-overview.sh"
WORKFLOW = ROOT / ".github" / "workflows" / "architecture-ci.yml"
VISUALS_README = ROOT / "visuals" / "README.md"
ROOT_README = ROOT / "README.md"


class D2EngineeringOverviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d2 = D2_SOURCE.read_text(encoding="utf-8") if D2_SOURCE.exists() else ""
        cls.renderer = RENDERER.read_text(encoding="utf-8") if RENDERER.exists() else ""
        cls.workflow = WORKFLOW.read_text(encoding="utf-8") if WORKFLOW.exists() else ""
        cls.visuals_readme = VISUALS_README.read_text(encoding="utf-8") if VISUALS_README.exists() else ""
        cls.root_readme = ROOT_README.read_text(encoding="utf-8") if ROOT_README.exists() else ""

    def test_d2_source_exists(self):
        self.assertTrue(D2_SOURCE.exists())

    def test_d2_source_is_regular_file(self):
        self.assertTrue(D2_SOURCE.is_file())

    def test_d2_source_is_not_symbolic_link(self):
        self.assertFalse(D2_SOURCE.is_symlink())

    def test_d2_source_is_non_empty(self):
        self.assertGreater(D2_SOURCE.stat().st_size, 0)

    def test_exact_diagram_title_is_present(self):
        self.assertIn('title: "TrustSender.io Engineering Overview"', self.d2)

    def test_exact_canonical_operational_container_names_are_present(self):
        for name in (
            "Edge and Routing", "Web Application", "Application API",
            "PostgreSQL Database", "Job Control Plane",
            "Distributed P1 Worker Plane", "WordPress Blog",
        ):
            with self.subTest(name=name):
                self.assertIn(name, self.d2)

    def test_p2_smtp_execution_plane_is_present(self):
        self.assertIn("P2 SMTP Execution Plane", self.d2)

    def test_ongoing_is_present(self):
        self.assertIn("ONGOING", self.d2)

    def test_p2_styling_is_dashed(self):
        self.assertRegex(self.d2, r"ongoing:[\s\S]*stroke-dash: 6")
        self.assertRegex(self.d2, r"validation\.control\.job -> validation\.p2\.smtp:[\s\S]*style\.stroke-dash: 6")

    def test_p2_styling_is_amber(self):
        self.assertRegex(self.d2, r"ongoing:[\s\S]*#f59e0b")
        self.assertRegex(self.d2, r"validation\.p2\.smtp -> external\.mail:[\s\S]*#f59e0b")

    def test_operational_and_ongoing_styles_are_distinct(self):
        self.assertIn("#8bb8ff", self.d2)
        self.assertIn("#f59e0b", self.d2)
        self.assertNotEqual("#8bb8ff", "#f59e0b")

    def test_postgresql_is_authoritative_data_store(self):
        self.assertIn('db: "PostgreSQL Database\\nAuthoritative data store"', self.d2)

    def test_wordpress_is_separated_from_application_authority(self):
        experience_block = self.d2.split("experience: {", 1)[1].split("\nauthority: {", 1)[0]
        authority_block = self.d2.split("authority: {", 1)[1].split("\nvalidation: {", 1)[0]
        self.assertIn("WordPress Blog", experience_block)
        self.assertNotIn("WordPress Blog", authority_block)
        self.assertIn("isolated from application authority", self.d2)

    def test_no_remote_image_or_icon_url_is_used(self):
        self.assertNotRegex(self.d2, r"https?://")
        self.assertNotRegex(self.d2, r"\b(icon|image):")

    def test_no_private_repository_name_is_present(self):
        self.assertNotIn("admdbgs/trustsender", self.d2)

    def test_renderer_uses_strict_bash_mode(self):
        self.assertIn("set -euo pipefail", self.renderer)

    def test_renderer_uses_pinned_d2_version(self):
        self.assertRegex(self.renderer, r'D2_VERSION="v\d+\.\d+\.\d+"')
        self.assertIn('oss.terrastruct.com/d2@${D2_VERSION}', self.renderer)

    def test_renderer_does_not_use_latest(self):
        self.assertNotIn("latest", self.renderer.lower())

    def test_renderer_writes_to_expected_build_path(self):
        self.assertIn("build/architecture-svg", self.renderer)
        self.assertIn("trustsender-engineering-overview.svg", self.renderer)

    def test_renderer_does_not_write_to_diagrams(self):
        write_like_lines = [line for line in self.renderer.splitlines() if "OUTPUT" in line or "mkdir" in line or "rm -rf" in line]
        self.assertNotIn("diagrams/", "\n".join(write_like_lines))

    def test_workflow_contains_visuals_path_exactly_twice(self):
        self.assertEqual(2, self.workflow.count("visuals/**"))

    def test_workflow_contains_d2_render_step(self):
        self.assertIn("Render D2 engineering overview preview", self.workflow)
        self.assertIn("bash scripts/render-d2-overview.sh", self.workflow)

    def test_d2_render_step_is_after_published_container_view_verification(self):
        self.assertLess(
            self.workflow.index("Verify published Container View"),
            self.workflow.index("Render D2 engineering overview preview"),
        )

    def test_d2_render_step_is_before_artifact_upload(self):
        self.assertLess(
            self.workflow.index("Render D2 engineering overview preview"),
            self.workflow.index("Upload dark-mode SVG previews"),
        )

    def test_exactly_one_artifact_upload_remains(self):
        self.assertEqual(1, self.workflow.count("actions/upload-artifact@"))

    def test_artifact_name_remains(self):
        self.assertIn("name: trustsender-architecture-dark-svg", self.workflow)

    def test_upload_path_remains(self):
        self.assertIn("path: build/architecture-svg/*.svg", self.workflow)

    def test_retired_artifact_name_remains_absent(self):
        self.assertNotIn("trustsender-container-layout-candidate", self.workflow)

    def test_visuals_readme_documents_preview_only_publication_status(self):
        for phrase in (
            "Structurizr DSL remains the canonical",
            "D2 is used only as the presentation layer",
            "temporary CI preview artifact only",
            "Generated output must not be committed automatically",
            "Publication requires visual inspection, public-safety inspection",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.visuals_readme)

    def test_root_readme_does_not_yet_embed_d2_svg(self):
        self.assertNotIn("trustsender-engineering-overview.svg", self.root_readme)
        self.assertNotRegex(self.root_readme, re.compile(r"!\[[^\]]*D2", re.IGNORECASE))


if __name__ == "__main__":
    unittest.main()
