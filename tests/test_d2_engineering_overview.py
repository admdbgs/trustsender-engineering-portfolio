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
        self.assertIn('TrustSender.io Engineering Overview', self.d2)

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
        self.assertRegex(self.d2, r"composition\.core\.validation\.control\.job -> composition\.core\.validation\.execution\.p2\.smtp:[\s\S]*style\.stroke-dash: 6")

    def test_p2_styling_is_amber(self):
        self.assertRegex(self.d2, r"ongoing:[\s\S]*#f59e0b")
        self.assertRegex(self.d2, r"composition\.core\.validation\.execution\.p2\.smtp -> composition\.external\.delivery_infrastructure\.mail:[\s\S]*#f59e0b")

    def test_operational_and_ongoing_styles_are_distinct(self):
        self.assertIn("#8bb8ff", self.d2)
        self.assertIn("#f59e0b", self.d2)
        self.assertNotEqual("#8bb8ff", "#f59e0b")

    def test_postgresql_is_authoritative_data_store(self):
        self.assertIn('db: "PostgreSQL Database\\nAuthoritative data store"', self.d2)

    def test_wordpress_is_separated_from_application_authority(self):
        experience_block = self.d2.split("experience: {", 1)[1].split("\n  }\n\n  core: {", 1)[0]
        authority_block = self.d2.split("authority: {", 1)[1].split("\n\n    validation: {", 1)[0]
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


    def test_invalid_inline_amber_dashed_blocks_are_absent(self):
        self.assertNotIn('{ style.stroke: "#f59e0b" style.stroke-dash: 6 }', self.d2)

    def test_all_corrected_multiline_p2_relationship_blocks_are_present(self):
        for first_line in (
            'composition.core.validation.control.job -> composition.core.validation.execution.p2.smtp: "Will dispatch\\neligible recipients" {',
            'composition.core.validation.execution.p2.smtp -> composition.external.delivery_infrastructure.mail: "Will perform conservative\\nrecipient handshakes" {',
            'composition.core.validation.execution.p2.smtp -> composition.core.validation.control.job: "Will return typed\\nSMTP evidence" {',
        ):
            with self.subTest(first_line=first_line):
                self.assertIn(first_line, self.d2)

    def test_renderer_does_not_delete_shared_output_directory(self):
        self.assertNotIn('rm -rf "${OUTPUT_DIRECTORY}"', self.renderer)

    def test_renderer_removes_at_most_exact_d2_output_path(self):
        rm_lines = [line.strip() for line in self.renderer.splitlines() if line.strip().startswith('rm ')]
        self.assertIn('rm -f "${OUTPUT_PATH}"', rm_lines)
        self.assertEqual(['rm -f "${OUTPUT_PATH}"'], rm_lines)

    def test_renderer_preserves_preexisting_output_file_hashes(self):
        for token in ('preexisting_manifest', 'sha256sum "${preexisting_file}"', 'preexisting output file changed'):
            with self.subTest(token=token):
                self.assertIn(token, self.renderer)

    def test_renderer_does_not_require_entire_shared_svg_directory_to_contain_one_svg(self):
        self.assertNotIn('find "${OUTPUT_DIRECTORY}" -type f -name \'*.svg\'', self.renderer)
        self.assertNotIn('expected exactly one D2 SVG output', self.renderer)

    def test_renderer_requires_exactly_one_d2_overview_output(self):
        self.assertIn("-name 'trustsender-engineering-overview*.svg'", self.renderer)
        self.assertIn('expected exactly one D2 overview SVG output', self.renderer)

    def test_expected_d2_output_filename_remains(self):
        self.assertIn('trustsender-engineering-overview.svg', self.renderer)

    def test_artifact_upload_path_allows_structurizr_and_d2_previews(self):
        self.assertIn('path: build/architecture-svg/*.svg', self.workflow)

    def test_structurizr_and_d2_previews_can_coexist_in_shared_artifact_directory(self):
        expected = (
            'trustsender-container-view-key.svg',
            'trustsender-container-view.svg',
            'trustsender-engineering-overview.svg',
            'trustsender-system-context-key.svg',
            'trustsender-system-context.svg',
        )
        self.assertIn('build/architecture-svg/*.svg', self.workflow)
        self.assertIn('find "${OUTPUT_DIRECTORY}" -type f ! -name \'trustsender-engineering-overview.svg\'', self.renderer)
        for filename in expected:
            with self.subTest(filename=filename):
                if filename == 'trustsender-engineering-overview.svg':
                    self.assertIn(filename, self.renderer)
                else:
                    self.assertNotIn(f'rm -f "${{OUTPUT_DIRECTORY}}/{filename}"', self.renderer)


    def _block_between(self, start, end):
        return self.d2.split(start, 1)[1].split(end, 1)[0]

    def _relationship_lines(self):
        return [line for line in self.d2.splitlines() if " -> " in line]

    def _normalized_relationships(self):
        lines = self._relationship_lines()
        relationships = []
        index = 0
        while index < len(lines):
            line = lines[index]
            source, rest = line.split(" -> ", 1)
            destination, rest = rest.split(": ", 1)
            label = rest.split('"', 2)[1]
            relationships.append((source, destination, " ".join(label.replace("\\n", " ").split())))
            index += 1
        return relationships


    def _edge_block(self, first_line):
        start = self.d2.index(first_line)
        return self.d2[start:self.d2.index('\n}', start) + 2]

    def test_header_presentation_object_exists_once(self):
        self.assertEqual(1, self.d2.count('header: {'))

    def test_header_uses_text_shape(self):
        header_block = self._block_between('header: {', '\n}\n\nclasses:')
        self.assertIn('shape: text', header_block)

    def test_header_uses_near_top_center(self):
        header_block = self._block_between('header: {', '\n}\n\nclasses:')
        self.assertIn('near: top-center', header_block)

    def test_exact_subtitle_remains_present(self):
        self.assertIn('P1 distributed validation is operational; P2 SMTP evolution remains ONGOING.', self.d2)

    def test_old_independent_title_and_subtitle_are_absent(self):
        self.assertNotIn('title: "TrustSender.io Engineering Overview"', self.d2)
        self.assertNotIn('subtitle: "P1 distributed validation is operational; P2 SMTP evolution remains ONGOING."', self.d2)

    def test_global_direction_right_is_absent(self):
        self.assertNotRegex(self.d2, re.compile(r'^direction:\s*right\s*$', re.MULTILINE))

    def test_transparent_composition_container_exists(self):
        block = self._block_between('composition: {', '\n\n  upper: {')
        self.assertIn('label: ""', block)
        self.assertIn('grid-rows: 3', block)
        self.assertIn('style.fill: "#1E1E2E"', block)
        self.assertIn('style.stroke: transparent', block)

    def test_transparent_upper_lane_exists(self):
        block = self._block_between('upper: {', '\n\n    users: {')
        self.assertIn('label: ""', block)
        self.assertIn('style.fill: "#1E1E2E"', block)
        self.assertIn('style.stroke: transparent', block)

    def test_transparent_core_lane_exists(self):
        block = self._block_between('core: {', '\n\n    authority: {')
        self.assertIn('label: ""', block)
        self.assertIn('style.fill: "#1E1E2E"', block)
        self.assertIn('style.stroke: transparent', block)

    def test_upper_lane_uses_two_columns_and_declares_users_then_experience(self):
        block = self._block_between('upper: {', '\n  }\n\n  core: {')
        self.assertIn('grid-columns: 2', block)
        self.assertLess(block.index('label: "1. Users"'), block.index('label: "2. Experience and Routing'))

    def test_core_lane_uses_two_columns_and_declares_authority_validation(self):
        block = self._block_between('core: {', '\n  }\n\n  external: {')
        self.assertIn('grid-columns: 2', block)
        self.assertLess(block.index('label: "3. Application Authority and Data'), block.index('label: "4. Validation Control and Execution"'))

    def test_external_systems_use_two_column_three_row_grid(self):
        block = self._block_between('\n  external: {\n    label', '\n  }\n}\n\ncomposition.upper')
        self.assertIn('grid-columns: 2', block)
        self.assertIn('application_services: {', block)
        self.assertIn('delivery_infrastructure: {', block)
        for earlier, later in (("Google Identity", "Microsoft Identity"), ("Microsoft Identity", "Stripe"), ("Stripe", "Brevo"), ("Brevo", "GitHub Actions"), ("GitHub Actions", "Internet Mail Infrastructure")):
            self.assertLess(block.index(earlier), block.index(later))

    def test_users_use_vertical_two_item_grid(self):
        block = self._block_between('users: {', '\n    }\n\n    experience:')
        self.assertIn('grid-columns: 2', block)
        self.assertLess(block.index('Customer'), block.index('Platform Operator'))

    def test_application_api_appears_before_postgresql(self):
        block = self._block_between('authority: {', '\n\n    validation: {')
        self.assertLess(block.index('Application API'), block.index('PostgreSQL Database'))

    def test_p1_appears_before_p2_in_validation(self):
        block = self._block_between('validation: {', '\n\n    external: {')
        self.assertLess(block.index('Operational P1 execution'), block.index('Ongoing P2 evolution'))

    def test_every_required_leaf_node_has_explicit_width_and_height(self):
        expected = {
            'Customer': (190, 70), 'Platform Operator': (190, 70),
            'Edge and Routing': (260, 120), 'Web Application': (230, 90),
            'WordPress Blog': (270, 105), 'Application API': (320, 180),
            'PostgreSQL Database': (300, 125), 'Job Control Plane': (320, 170),
            'Distributed P1 Worker Plane': (340, 160), 'P2 SMTP Execution Plane': (340, 160),
            'Google Identity': (210, 75), 'Microsoft Identity': (210, 75),
            'Stripe': (210, 75), 'Brevo': (210, 75),
            'GitHub Actions': (270, 95), 'Internet Mail Infrastructure': (280, 110),
        }
        for name, (width, height) in expected.items():
            with self.subTest(name=name):
                pattern = re.escape(f'"{name}') + r'[\s\S]*?width: ' + str(width) + r'[\s\S]*?height: ' + str(height)
                self.assertRegex(self.d2, pattern)

    def test_no_dimensions_are_assigned_to_layout_or_area_containers(self):
        container_headers = ('composition:', 'upper:', 'lower:', 'users:', 'experience:', 'authority:', 'validation:', 'external:', 'control:', 'p1:', 'p2:')
        for line in self.d2.splitlines():
            stripped = line.strip()
            if stripped.startswith(container_headers) and stripped.endswith('{'):
                self.assertNotIn('width:', stripped)
                self.assertNotIn('height:', stripped)

    def test_exactly_twenty_logical_relationships_remain(self):
        self.assertEqual(20, len(self._relationship_lines()))

    def test_relationship_pairs_match_approved_list(self):
        expected = [
            ('composition.upper.users.customer', 'composition.upper.experience.edge'),
            ('composition.upper.users.operator', 'composition.upper.experience.edge'),
            ('composition.upper.experience.edge', 'composition.upper.experience.web'),
            ('composition.upper.experience.edge', 'composition.core.authority.api'),
            ('composition.upper.experience.edge', 'composition.upper.experience.blog'),
            ('composition.upper.experience.web', 'composition.core.authority.api'),
            ('composition.core.authority.api', 'composition.core.authority.db'),
            ('composition.core.authority.api', 'composition.core.validation.control.job'),
            ('composition.core.validation.control.job', 'composition.core.authority.db'),
            ('composition.core.validation.control.job', 'composition.core.validation.execution.p1.workers'),
            ('composition.core.validation.execution.p1.workers', 'composition.external.delivery_infrastructure.mail'),
            ('composition.core.validation.execution.p1.workers', 'composition.core.validation.control.job'),
            ('composition.core.authority.api', 'composition.external.application_services.google'),
            ('composition.core.authority.api', 'composition.external.application_services.microsoft'),
            ('composition.core.authority.api', 'composition.external.application_services.stripe'),
            ('composition.core.authority.api', 'composition.external.application_services.brevo'),
            ('composition.external.delivery_infrastructure.gha', 'composition.upper.experience.edge'),
            ('composition.core.validation.control.job', 'composition.core.validation.execution.p2.smtp'),
            ('composition.core.validation.execution.p2.smtp', 'composition.external.delivery_infrastructure.mail'),
            ('composition.core.validation.execution.p2.smtp', 'composition.core.validation.control.job'),
        ]
        observed = [(source, destination) for source, destination, _ in self._normalized_relationships()]
        self.assertEqual(expected, observed)

    def test_normalized_relationship_labels_match_previous_approved_labels(self):
        expected = [
            'Accesses', 'Accesses approved interfaces', 'Routes application traffic',
            'Routes API traffic', 'Routes blog traffic', 'Uses',
            'Reads and writes authoritative application data', 'Submits and manages jobs',
            'Reads and writes lifecycle state', 'Dispatches authorized work',
            'Queries for current P1 validation evidence', 'Returns progress, evidence, and artifacts',
            'Uses for federated authentication', 'Uses for federated authentication',
            'Coordinates checkout and signed payment events', 'Requests transactional and operational email',
            'Builds and deploys reviewed releases', 'Will dispatch eligible recipients',
            'Will perform conservative recipient handshakes', 'Will return typed SMTP evidence',
        ]
        self.assertEqual(expected, [label for _, _, label in self._normalized_relationships()])

    def test_no_invisible_or_opacity_zero_relationship_exists(self):
        for line in self._relationship_lines():
            self.assertNotIn('opacity: 0', line)
            self.assertNotIn('transparent', line)

    def test_no_spacer_or_dummy_node_exists(self):
        self.assertNotRegex(self.d2, re.compile(r'\b(spacer|dummy)\b', re.IGNORECASE))

    def test_no_remote_url_icon_image_font_or_import_exists(self):
        self.assertNotRegex(self.d2, re.compile(r'https?://|\b(icon|image|font):|\bimport\b|!include'))

    def test_p1_remains_operational(self):
        self.assertIn('Distributed P1 Worker Plane\\nOperational', self.d2)
        self.assertIn('label: "Operational P1 execution"', self.d2)

    def test_p2_remains_exactly_ongoing(self):
        self.assertEqual(2, self.d2.count('ONGOING'))
        self.assertIn('P2 SMTP Execution Plane\\nONGOING', self.d2)


    def test_explicit_root_fill_is_dark_background(self):
        self.assertIn('style.fill: "#1E1E2E"', self.d2.split('header: {', 1)[0])

    def test_composition_and_lane_fills_match_root(self):
        for marker in ('composition: {', 'upper: {', 'core: {'):
            with self.subTest(marker=marker):
                block = self._block_between(marker, '\n\n')
                self.assertIn('style.fill: "#1E1E2E"', block)
                self.assertIn('style.stroke: transparent', block)

    def test_no_layout_only_container_uses_opacity_zero(self):
        self.assertNotIn('opacity: 0', self.d2)
        self.assertNotIn('style.opacity: 0', self.d2)

    def test_header_contains_title_and_subtitle_text_children(self):
        block = self._block_between('header: {', '\n}\n\nclasses:')
        self.assertEqual(1, block.count('title_text: "TrustSender.io Engineering Overview"'))
        self.assertEqual(1, block.count('subtitle_text: "P1 distributed validation is operational; P2 SMTP evolution remains ONGOING."'))

    def test_title_text_font_size_and_style_are_correct(self):
        block = self._block_between('title_text: "TrustSender.io Engineering Overview" {', '\n  }\n  subtitle_text:')
        self.assertIn('shape: text', block)
        self.assertIn('font-size: 32', block)
        self.assertIn('bold: true', block)
        self.assertIn('font-color: "#edf3ff"', block)

    def test_subtitle_text_font_size_and_style_are_correct(self):
        block = self._block_between('subtitle_text: "P1 distributed validation is operational; P2 SMTP evolution remains ONGOING." {', '\n  }\n}\n\nclasses:')
        self.assertIn('shape: text', block)
        self.assertIn('font-size: 18', block)
        self.assertIn('bold: false', block)
        self.assertIn('font-color: "#cbd5e1"', block)

    def test_users_use_two_columns_and_customer_first(self):
        block = self._block_between('users: {', '\n    }\n\n    experience:')
        self.assertIn('grid-columns: 2', block)
        self.assertLess(block.index('customer: "Customer"'), block.index('operator: "Platform Operator"'))

    def test_validation_uses_two_rows_and_execution_second(self):
        block = self._block_between('validation: {', '\n\n    external: {')
        self.assertIn('grid-rows: 2', block)
        self.assertLess(block.index('control: {'), block.index('execution: {'))

    def test_execution_is_unlabeled_background_filled_two_column_layout(self):
        block = self._block_between('execution: {', '\n      }\n    }\n\n    external:')
        self.assertIn('label: ""', block)
        self.assertIn('grid-columns: 2', block)
        self.assertIn('style.fill: "#1E1E2E"', block)
        self.assertIn('style.stroke: transparent', block)
        self.assertLess(block.index('p1: {'), block.index('p2: {'))

    def test_application_services_uses_two_by_two_grid_and_expected_members(self):
        block = self._block_between('application_services: {', '\n    }\n    delivery_infrastructure:')
        self.assertIn('grid-columns: 2', block)
        self.assertIn('grid-rows: 2', block)
        for name in ('Google Identity', 'Microsoft Identity', 'Stripe', 'Brevo'):
            self.assertIn(name, block)
        self.assertNotIn('GitHub Actions', block)
        self.assertNotIn('Internet Mail Infrastructure', block)

    def test_delivery_infrastructure_uses_two_item_vertical_grid(self):
        block = self._block_between('delivery_infrastructure: {', '\n    }\n  }\n}')
        self.assertIn('grid-rows: 2', block)
        self.assertIn('GitHub Actions', block)
        self.assertIn('Internet Mail Infrastructure', block)
        self.assertNotIn('Google Identity', block)

    def test_required_central_node_dimensions_are_approved(self):
        expected = {
            'Edge and Routing': (260, 120), 'Application API': (320, 180),
            'PostgreSQL Database': (300, 125), 'Job Control Plane': (320, 170),
            'Distributed P1 Worker Plane': (340, 160), 'P2 SMTP Execution Plane': (340, 160),
            'Internet Mail Infrastructure': (280, 110),
        }
        for name, (width, height) in expected.items():
            with self.subTest(name=name):
                self.assertRegex(self.d2, re.escape(f'"{name}') + r'[\s\S]*?width: ' + str(width) + r'[\s\S]*?height: ' + str(height))

    def test_every_operational_edge_has_complete_approved_label_style(self):
        required = ('style.stroke: "#8bb8ff"', 'style.stroke-width: 2', 'style.font-size: 13', 'style.font-color: "#dbeafe"', 'style.fill: "#1E1E2E"', 'style.border-radius: 8', 'style.bold: false')
        for line in self._relationship_lines()[:17]:
            block = self._edge_block(line)
            with self.subTest(edge=line):
                for token in required:
                    self.assertIn(token, block)
                self.assertNotIn('style.stroke-dash', block)

    def test_every_p2_edge_has_complete_amber_dashed_label_style(self):
        required = ('style.stroke: "#f59e0b"', 'style.stroke-width: 2', 'style.stroke-dash: 6', 'style.font-size: 13', 'style.font-color: "#ffe7b0"', 'style.fill: "#1E1E2E"', 'style.border-radius: 8', 'style.bold: false')
        for line in self._relationship_lines()[17:]:
            block = self._edge_block(line)
            with self.subTest(edge=line):
                for token in required:
                    self.assertIn(token, block)

    def test_no_layout_only_connection_exists(self):
        for line in self._relationship_lines():
            self.assertNotIn('composition ->', line)
            self.assertNotIn('upper ->', line)
            self.assertNotIn('lower ->', line)
            self.assertNotIn('execution ->', line)

    def test_grid_gaps_are_declared_for_balanced_layout_groups(self):
        for marker in ('composition: {', 'upper: {', 'core: {', 'users: {', 'experience: {', 'authority: {', 'validation: {', 'execution: {', '\n  external: {\n    label', 'application_services: {', 'delivery_infrastructure: {'):
            with self.subTest(marker=marker):
                block = self.d2[self.d2.index(marker):self.d2.index(marker) + 220]
                self.assertRegex(block, r'grid-gap: (2[4-9]|[3-6][0-9]|70)')


    def test_composition_uses_three_grid_rows_for_stage_three(self):
        block = self._block_between('composition: {', '\n\n  upper: {')
        self.assertIn('grid-rows: 3', block)
        self.assertIn('grid-gap: 46', block)

    def test_direct_composition_child_order_is_upper_core_external(self):
        section = self._block_between('composition: {', '\n}\n\ncomposition.upper')
        self.assertLess(section.index('upper: {'), section.index('core: {'))
        self.assertLess(section.index('core: {'), section.index('\n  external: {\n    label'))

    def test_composition_lower_is_absent(self):
        self.assertNotIn('composition.lower', self.d2)
        self.assertNotIn('\n  lower: {', self.d2)

    def test_composition_core_exists_and_is_unlabeled(self):
        block = self._block_between('core: {', '\n\n    authority: {')
        self.assertIn('label: ""', block)

    def test_core_uses_root_fill_transparent_stroke_and_two_columns(self):
        block = self._block_between('core: {', '\n\n    authority: {')
        self.assertIn('style.fill: "#1E1E2E"', block)
        self.assertIn('style.stroke: transparent', block)
        self.assertIn('grid-columns: 2', block)
        self.assertIn('grid-gap: 52', block)

    def test_authority_declared_before_validation_in_core(self):
        block = self._block_between('core: {', '\n  }\n\n  external: {')
        self.assertLess(block.index('authority: {'), block.index('validation: {'))

    def test_external_is_direct_child_after_core_with_exact_label(self):
        section = self._block_between('composition: {', '\n}\n\ncomposition.upper')
        self.assertLess(section.index('core: {'), section.index('\n  external: {\n    label'))
        external = self._block_between('\n  external: {\n    label', '\n  }\n}\n\ncomposition.upper')
        self.assertIn('label: "5. External Services and Infrastructure\\nExternal dependencies"', self.d2)
        self.assertIn('class: area', external)

    def test_external_retains_two_presentation_groups_in_order(self):
        external = self._block_between('\n  external: {\n    label', '\n  }\n}\n\ncomposition.upper')
        self.assertEqual(1, external.count('application_services: {'))
        self.assertEqual(1, external.count('delivery_infrastructure: {'))
        self.assertLess(external.index('application_services: {'), external.index('delivery_infrastructure: {'))

    def test_no_relationship_path_contains_old_lower_prefix(self):
        for line in self._relationship_lines():
            self.assertNotIn('composition.lower', line)

    def test_relationship_paths_use_core_for_authority_and_validation(self):
        joined = '\n'.join(self._relationship_lines())
        self.assertIn('composition.core.authority.api', joined)
        self.assertIn('composition.core.validation.control.job', joined)
        self.assertNotIn('composition.lower.authority', joined)
        self.assertNotIn('composition.lower.validation', joined)

    def test_external_system_relationship_paths_use_direct_external(self):
        joined = '\n'.join(self._relationship_lines())
        self.assertIn('composition.external.application_services.google', joined)
        self.assertIn('composition.external.delivery_infrastructure.mail', joined)
        self.assertNotIn('composition.core.external', joined)

    def test_stage_three_spacing_values_are_applied(self):
        self.assertIn('grid-rows: 3', self._block_between('composition: {', '\n\n  upper: {'))
        self.assertIn('grid-gap: 40', self._block_between('authority: {', '\n\n    validation: {'))
        self.assertIn('grid-gap: 46', self._block_between('validation: {', '\n\n  external: {'))
        self.assertIn('grid-gap: 48', self._block_between('execution: {', '\n      }\n    }'))
        self.assertIn('grid-gap: 46', self._block_between('\n  external: {\n    label', '\n  }\n}\n\ncomposition.upper'))
        self.assertIn('grid-gap: 30', self._block_between('application_services: {', '\n    }\n    delivery_infrastructure:'))
        self.assertIn('grid-gap: 34', self._block_between('delivery_infrastructure: {', '\n    }\n  }'))

    def test_root_readme_does_not_yet_embed_d2_svg(self):
        self.assertNotIn("trustsender-engineering-overview.svg", self.root_readme)
        self.assertNotRegex(self.root_readme, re.compile(r"!\[[^\]]*D2", re.IGNORECASE))


if __name__ == "__main__":
    unittest.main()
