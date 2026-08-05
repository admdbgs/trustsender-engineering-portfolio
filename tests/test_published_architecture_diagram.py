"""Permanent checks for the published architecture Container View SVG."""

from pathlib import Path
import hashlib
import unittest
import xml.etree.ElementTree as ET


class PublishedContainerViewTests(unittest.TestCase):
    """Verify the reviewed Container View SVG and CI publication guardrails."""

    @classmethod
    def setUpClass(cls):
        cls.repo_root = Path(__file__).resolve().parents[1]
        cls.svg_path = cls.repo_root / "diagrams" / "trustsender-container-view.svg"
        cls.workflow_path = cls.repo_root / ".github" / "workflows" / "architecture-ci.yml"
        cls.approved_hash = "04730d386c49d66a1fa624e3db8a0fd077b636a3133cf8ec007f54e9090a731e"
        cls.workflow_text = cls.workflow_path.read_text(encoding="utf-8")

    def _svg_root(self):
        return ET.parse(self.svg_path).getroot()

    def test_published_container_view_exists(self):
        self.assertTrue(self.svg_path.exists())

    def test_published_container_view_is_regular_file(self):
        self.assertTrue(self.svg_path.is_file())

    def test_published_container_view_is_not_symbolic_link(self):
        self.assertFalse(self.svg_path.is_symlink())

    def test_published_container_view_is_non_empty(self):
        self.assertGreater(self.svg_path.stat().st_size, 0)

    def test_published_container_view_parses_as_xml(self):
        self.assertIsNotNone(self._svg_root())

    def test_published_container_view_root_local_name_is_svg(self):
        self.assertEqual(self._svg_root().tag.rsplit("}", 1)[-1], "svg")

    def test_published_container_view_width_is_expected(self):
        self.assertIn(self._svg_root().get("width"), {"5000", "5000px"})

    def test_published_container_view_height_is_expected(self):
        self.assertIn(self._svg_root().get("height"), {"2200", "2200px"})

    def test_published_container_view_viewbox_is_expected(self):
        view_box = self._svg_root().get("viewBox")
        self.assertEqual(" ".join(view_box.split()), "0 0 5000 2200")

    def test_published_container_view_raw_sha256_is_approved(self):
        digest = hashlib.sha256(self.svg_path.read_bytes()).hexdigest()
        self.assertEqual(digest, self.approved_hash)

    def test_workflow_contains_diagrams_glob_exactly_twice(self):
        self.assertEqual(self.workflow_text.count("diagrams/**"), 2)

    def test_workflow_excludes_diagrams_readme_path_filter(self):
        self.assertNotIn("diagrams/README.md", self.workflow_text)

    def test_workflow_contains_verify_published_container_view_step(self):
        self.assertIn("Verify published Container View", self.workflow_text)

    def test_workflow_contains_approved_container_view_hash(self):
        self.assertIn(self.approved_hash, self.workflow_text)

    def test_workflow_requires_exactly_one_timestamp_in_each_svg(self):
        self.assertIn("expected exactly one Structurizr render timestamp", self.workflow_text)
        self.assertIn("if len(matches) != 1", self.workflow_text)

    def test_workflow_contains_explicit_english_weekday_names(self):
        weekdays = "Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday"
        self.assertIn(weekdays, self.workflow_text)

    def test_workflow_contains_explicit_english_month_names(self):
        months = "January|February|March|April|May|June|July|August|September|October|November|December"
        self.assertIn(months, self.workflow_text)

    def test_workflow_contains_timestamp_replacement_token(self):
        self.assertIn("STRUCTURIZR_RENDER_TIMESTAMP", self.workflow_text)

    def test_workflow_compares_normalized_byte_sequences(self):
        self.assertIn("normalized_generated != normalized_committed", self.workflow_text)

    def test_workflow_does_not_use_raw_cmp_between_svgs(self):
        self.assertNotIn("cmp ", self.workflow_text)
        self.assertNotIn(" cmp", self.workflow_text)

    def test_workflow_uploads_one_dark_svg_artifact(self):
        self.assertEqual(self.workflow_text.count("trustsender-architecture-dark-svg"), 1)

    def test_workflow_preserves_dark_svg_artifact_path(self):
        self.assertIn("build/architecture-svg/*.svg", self.workflow_text)

    def test_workflow_excludes_retired_container_layout_artifact(self):
        self.assertNotIn("trustsender-container-layout-candidate", self.workflow_text)


if __name__ == "__main__":
    unittest.main()
