from __future__ import annotations

import logging

from django.http import FileResponse
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from estimator.api.serializers import (
    CalculateCOCOMOSerializer,
    CalculateFPSerializer,
    ProjectWriteSerializer,
    gsc_with_labels,
)
from estimator.models import Project
from estimator.services.cocomo import calculate_cocomo
from estimator.services.function_point import calculate_fp, ufp_breakdown
from estimator.services.pdf_service import (
    build_project_report_data,
    generate_pdf_report,
    suggested_pdf_filename,
)
from estimator.utils.constants import COCOMO_MODES, GSC_LABELS

logger = logging.getLogger(__name__)


def _counts_payload(data: dict) -> dict:
    return {k: dict(data[k]) for k in ("ei", "eo", "eq", "ilf", "eif")}


class CalculateFPView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        ser = CalculateFPSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        counts = _counts_payload(data)
        gsc = list(data["gsc"])
        fp, ufp, caf = calculate_fp(counts, gsc)
        breakdown = ufp_breakdown(counts)
        return Response(
            {
                "ufp": round(ufp, 4),
                "caf": round(caf, 4),
                "fp": round(fp, 4),
                "ufp_breakdown": {k: round(v, 4) for k, v in breakdown.items()},
                "gsc_detail": gsc_with_labels(gsc),
            }
        )


class CalculateCOCOMOView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        ser = CalculateCOCOMOSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        fp = ser.validated_data["fp"]
        mode = ser.validated_data["mode"]
        kloc, effort, tdev = calculate_cocomo(fp, mode)
        a, b, c, d = COCOMO_MODES[mode]
        return Response(
            {
                "mode": mode,
                "fp": fp,
                "kloc": round(kloc, 6),
                "effort_pm": round(effort, 4),
                "tdev_months": round(tdev, 4),
                "coefficients": {"a": a, "b": b, "c": c, "d": d},
            }
        )


class ProjectListCreateView(APIView):
    """Optional: persist estimation snapshots."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        qs = Project.objects.order_by("-updated_at")[:50]
        return Response(
            [
                {
                    "id": p.id,
                    "name": p.name,
                    "fp": p.fp,
                    "effort_pm": p.effort_pm,
                    "tdev_months": p.tdev_months,
                    "updated_at": p.updated_at.isoformat(),
                }
                for p in qs
            ]
        )

    def post(self, request):
        ser = ProjectWriteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        counts = _counts_payload(data)
        gsc = list(data["gsc"])
        mode = data["cocomo_mode"]
        fp, ufp, caf = calculate_fp(counts, gsc)
        kloc, effort, tdev = calculate_cocomo(fp, mode)
        inputs = {
            **counts,
            "gsc": gsc,
            "gsc_labels": list(GSC_LABELS),
            "cocomo_mode": mode,
        }
        outputs = {
            "ufp": ufp,
            "caf": caf,
            "fp": fp,
            "ufp_breakdown": ufp_breakdown(counts),
            "kloc": kloc,
            "effort_pm": effort,
            "tdev_months": tdev,
        }
        p = Project.objects.create(
            name=data["name"],
            inputs=inputs,
            outputs=outputs,
            fp=fp,
            effort_pm=effort,
            tdev_months=tdev,
        )
        return Response({"id": p.id}, status=status.HTTP_201_CREATED)


class GSCMetaView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {
                "factors": [{"id": i, "label": GSC_LABELS[i]} for i in range(len(GSC_LABELS))],
                "cocomo_modes": list(COCOMO_MODES.keys()),
            }
        )


class ExportProjectPDFView(APIView):
    """Download a PDF report for a saved project snapshot."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, project_id: int):
        try:
            project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            return Response({"detail": "Project not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            payload = build_project_report_data(project)
            buffer = generate_pdf_report(payload)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            logger.exception("PDF generation failed for project_id=%s", project_id)
            return Response(
                {"detail": "Failed to generate PDF."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        filename = suggested_pdf_filename(project.id, project.name)
        return FileResponse(
            buffer,
            as_attachment=True,
            filename=filename,
            content_type="application/pdf",
        )
