from django.test import TestCase

from estimator.models import Project
from estimator.services.cocomo import calculate_cocomo
from estimator.services.function_point import calculate_caf, calculate_fp, calculate_ufp, ufp_breakdown
from estimator.services.pdf_service import generate_pdf_report, suggested_pdf_filename
from estimator.utils.formatters import format_cocomo_mode, format_decimal


class FunctionPointTests(TestCase):
    def test_ufp_known_vector(self):
        counts = {
            "ei": {"simple": 1, "average": 0, "complex": 0},
            "eo": {"simple": 0, "average": 1, "complex": 0},
            "eq": {"simple": 0, "average": 0, "complex": 1},
            "ilf": {"simple": 0, "average": 0, "complex": 1},
            "eif": {"simple": 1, "average": 0, "complex": 0},
        }
        # 3 + 5 + 6 + 15 + 5 = 34
        self.assertEqual(calculate_ufp(counts), 34.0)

    def test_caf_all_zeros(self):
        gsc = [0] * 14
        self.assertAlmostEqual(calculate_caf(gsc), 0.65)

    def test_caf_all_fives(self):
        gsc = [5] * 14
        self.assertAlmostEqual(calculate_caf(gsc), 0.65 + 0.01 * 70)

    def test_fp_product(self):
        counts = {
            "ei": {"simple": 2, "average": 0, "complex": 0},
            "eo": {"simple": 0, "average": 0, "complex": 0},
            "eq": {"simple": 0, "average": 0, "complex": 0},
            "ilf": {"simple": 0, "average": 0, "complex": 0},
            "eif": {"simple": 0, "average": 0, "complex": 0},
        }
        gsc = [0] * 14
        fp, ufp, caf = calculate_fp(counts, gsc)
        self.assertEqual(ufp, 6.0)
        self.assertAlmostEqual(caf, 0.65)
        self.assertAlmostEqual(fp, 3.9)

    def test_breakdown(self):
        counts = {
            "ei": {"simple": 1, "average": 0, "complex": 0},
            "eo": {"simple": 0, "average": 0, "complex": 0},
            "eq": {"simple": 0, "average": 0, "complex": 0},
            "ilf": {"simple": 0, "average": 0, "complex": 0},
            "eif": {"simple": 0, "average": 0, "complex": 0},
        }
        b = ufp_breakdown(counts)
        self.assertEqual(b["EI"], 3.0)


class CocomoTests(TestCase):
    def test_organic_fp_100(self):
        kloc, effort, tdev = calculate_cocomo(100, "organic")
        self.assertAlmostEqual(kloc, 1.0)
        self.assertAlmostEqual(effort, 2.4 * (1.0**1.05))
        self.assertGreater(tdev, 0)

    def test_zero_fp(self):
        kloc, effort, tdev = calculate_cocomo(0, "embedded")
        self.assertEqual((kloc, effort, tdev), (0.0, 0.0, 0.0))


class FormatterTests(TestCase):
    def test_format_decimal(self):
        self.assertEqual(format_decimal(3.14159), "3.14")
        self.assertEqual(format_decimal(None), "—")

    def test_format_cocomo_mode(self):
        self.assertEqual(format_cocomo_mode("semi_detached"), "Semi-detached")


class PDFServiceTests(TestCase):
    def test_generate_pdf_report(self):
        buf = generate_pdf_report(
            {
                "project_name": "Alpha",
                "ufp": 12.34,
                "caf": 1.05,
                "fp": 12.96,
                "cocomo_mode": "organic",
                "effort_pm": 4.56,
                "tdev_months": 7.89,
                "kloc": 0.13,
                "timestamp": "2026-01-15T10:00:00Z",
            }
        )
        data = buf.read()
        self.assertTrue(data.startswith(b"%PDF"))
        buf.close()

    def test_suggested_pdf_filename(self):
        name = suggested_pdf_filename(3, "My Project!")
        self.assertIn("3", name)
        self.assertTrue(name.endswith(".pdf"))


class APITests(TestCase):
    def test_calculate_fp_root_path(self):
        body = {
            "ei": {"simple": 0, "average": 0, "complex": 0},
            "eo": {"simple": 0, "average": 0, "complex": 0},
            "eq": {"simple": 0, "average": 0, "complex": 0},
            "ilf": {"simple": 0, "average": 0, "complex": 0},
            "eif": {"simple": 0, "average": 0, "complex": 0},
            "gsc": [3] * 14,
        }
        r = self.client.post("/calculate-fp/", data=body, content_type="application/json")
        self.assertEqual(r.status_code, 200)
        self.assertIn("fp", r.json())

    def test_calculate_fp_endpoint(self):
        body = {
            "ei": {"simple": 1, "average": 0, "complex": 0},
            "eo": {"simple": 0, "average": 0, "complex": 0},
            "eq": {"simple": 0, "average": 0, "complex": 0},
            "ilf": {"simple": 0, "average": 0, "complex": 0},
            "eif": {"simple": 0, "average": 0, "complex": 0},
            "gsc": [0] * 14,
        }
        r = self.client.post(
            "/api/calculate-fp/",
            data=body,
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)
        self.assertAlmostEqual(r.json()["ufp"], 3.0)

    def test_calculate_cocomo_endpoint(self):
        r = self.client.post(
            "/api/calculate-cocomo/",
            data={"fp": 100, "mode": "organic"},
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)
        j = r.json()
        self.assertIn("effort_pm", j)
        self.assertIn("tdev_months", j)

    def test_export_pdf_endpoint(self):
        p = Project.objects.create(
            name="Report Test",
            inputs={"cocomo_mode": "semi_detached"},
            outputs={
                "ufp": 20.0,
                "caf": 1.0,
                "fp": 20.0,
                "kloc": 0.2,
                "effort_pm": 1.2,
                "tdev_months": 3.4,
            },
            fp=20.0,
            effort_pm=1.2,
            tdev_months=3.4,
        )
        r = self.client.get(f"/api/export-pdf/{p.id}/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("application/pdf", r["Content-Type"])
        body = b"".join(r.streaming_content)
        self.assertTrue(body.startswith(b"%PDF"))

    def test_export_pdf_not_found(self):
        r = self.client.get("/api/export-pdf/999999/")
        self.assertEqual(r.status_code, 404)
