"""Persistence and queries for user-owned estimation projects."""

from __future__ import annotations

from django.contrib.auth.models import AbstractUser

from estimator.models import Project
from estimator.services.cocomo import calculate_cocomo
from estimator.services.function_point import calculate_fp, ufp_breakdown
from estimator.utils.constants import GSC_LABELS


def _counts_payload(data: dict) -> dict:
    return {k: dict(data[k]) for k in ("ei", "eo", "eq", "ilf", "eif")}


def project_to_list_item(project: Project) -> dict:
    return {
        "id": project.id,
        "name": project.name,
        "fp": project.fp,
        "effort_pm": project.effort_pm,
        "tdev_months": project.tdev_months,
        "updated_at": project.updated_at.isoformat(),
    }


def list_projects_for_user(user: AbstractUser, *, limit: int = 50) -> list[Project]:
    return list(
        Project.objects.filter(user=user).order_by("-updated_at")[:limit],
    )


def get_project_for_user(user: AbstractUser, project_id: int) -> Project | None:
    try:
        return Project.objects.get(pk=project_id, user=user)
    except Project.DoesNotExist:
        return None


def create_project_for_user(user: AbstractUser, validated_data: dict) -> Project:
    """
    validated_data: output of ProjectWriteSerializer (validated).
    """
    data = validated_data
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
    return Project.objects.create(
        user=user,
        name=data["name"],
        inputs=inputs,
        outputs=outputs,
        fp=fp,
        effort_pm=effort,
        tdev_months=tdev,
    )
