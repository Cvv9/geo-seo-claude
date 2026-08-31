"""Regression contracts for the PDF report template installation and output."""

from pathlib import Path
import unittest


REPOSITORY = Path(__file__).resolve().parents[1]


class TestReportTemplateInstallation(unittest.TestCase):
    """Both supported installers must make the report template assets available."""

    def test_installers_copy_and_verify_report_templates(self):
        for installer_name in ("install.sh", "install-win.sh"):
            installer = (REPOSITORY / installer_name).read_text(encoding="utf-8")
            with self.subTest(installer=installer_name):
                self.assertIn("$INSTALL_DIR/templates", installer)
                self.assertIn(
                    'cp -r "$SOURCE_DIR/templates/"* "$INSTALL_DIR/templates/"',
                    installer,
                )
                self.assertIn("geo-report-template.html", installer)


class TestReportTemplateClientIsolation(unittest.TestCase):
    """A report without metadata must never inherit another client's details."""

    def test_templates_have_neutral_footer_and_no_sample_client_defaults(self):
        template = (REPOSITORY / "templates" / "geo-report-template.html").read_text(
            encoding="utf-8"
        )
        stylesheet = (REPOSITORY / "templates" / "geo-report-style.css").read_text(
            encoding="utf-8"
        )

        self.assertIn("footer_text", template)
        self.assertIn("GEO Audit", stylesheet)
        for sample_value in (
            "Alexa Media Solutions",
            "alexamediasolutions.com",
            "Raleigh",
            "AIOSEO",
            "Digital Marketing Agency",
            "May 3, 2026",
        ):
            with self.subTest(sample_value=sample_value):
                self.assertNotIn(sample_value, template + stylesheet)

        for metadata_field in ("date", "business_type", "locations", "platform"):
            with self.subTest(metadata_field=metadata_field):
                self.assertIn(f"$if({metadata_field})$", template)

