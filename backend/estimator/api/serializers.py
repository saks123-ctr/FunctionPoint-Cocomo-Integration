from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import serializers

from estimator.utils.constants import COCOMO_MODES, GSC_COUNT, GSC_LABELS

User = get_user_model()


class ComplexityCountsSerializer(serializers.Serializer):
    simple = serializers.IntegerField(min_value=0, default=0)
    average = serializers.IntegerField(min_value=0, default=0)
    complex = serializers.IntegerField(min_value=0, default=0)


def _zero_counts() -> dict:
    return {"simple": 0, "average": 0, "complex": 0}


def _default_gsc() -> list[int]:
    return [3] * GSC_COUNT


class CalculateFPSerializer(serializers.Serializer):
    ei = ComplexityCountsSerializer(required=False, default=_zero_counts)
    eo = ComplexityCountsSerializer(required=False, default=_zero_counts)
    eq = ComplexityCountsSerializer(required=False, default=_zero_counts)
    ilf = ComplexityCountsSerializer(required=False, default=_zero_counts)
    eif = ComplexityCountsSerializer(required=False, default=_zero_counts)
    gsc = serializers.ListField(
        child=serializers.IntegerField(min_value=0, max_value=5),
        required=False,
        default=_default_gsc,
        min_length=GSC_COUNT,
        max_length=GSC_COUNT,
    )

    def validate_gsc(self, value: list[int]) -> list[int]:
        if len(value) != GSC_COUNT:
            raise serializers.ValidationError(f"Provide exactly {GSC_COUNT} GSC scores (0–5).")
        return value

    def validate(self, attrs: dict) -> dict:
        for key in ("ei", "eo", "eq", "ilf", "eif"):
            if key not in attrs or attrs[key] is None:
                attrs[key] = _zero_counts()
        if "gsc" not in attrs or attrs["gsc"] is None:
            attrs["gsc"] = _default_gsc()
        return attrs


class CalculateCOCOMOSerializer(serializers.Serializer):
    fp = serializers.FloatField(min_value=0)
    mode = serializers.ChoiceField(choices=list(COCOMO_MODES.keys()))


class ProjectWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    ei = ComplexityCountsSerializer(required=False, default=_zero_counts)
    eo = ComplexityCountsSerializer(required=False, default=_zero_counts)
    eq = ComplexityCountsSerializer(required=False, default=_zero_counts)
    ilf = ComplexityCountsSerializer(required=False, default=_zero_counts)
    eif = ComplexityCountsSerializer(required=False, default=_zero_counts)
    gsc = serializers.ListField(
        child=serializers.IntegerField(min_value=0, max_value=5),
        required=False,
        default=_default_gsc,
        min_length=GSC_COUNT,
        max_length=GSC_COUNT,
    )
    cocomo_mode = serializers.ChoiceField(choices=list(COCOMO_MODES.keys()), default="organic")

    def validate(self, attrs: dict) -> dict:
        for key in ("ei", "eo", "eq", "ilf", "eif"):
            if key not in attrs or attrs[key] is None:
                attrs[key] = _zero_counts()
        if "gsc" not in attrs or attrs["gsc"] is None:
            attrs["gsc"] = _default_gsc()
        return attrs


def gsc_with_labels(values: list[int]) -> list[dict]:
    return [{"id": i, "label": GSC_LABELS[i], "value": values[i]} for i in range(len(values))]


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, trim_whitespace=True)
    email = serializers.EmailField(required=False, allow_blank=True, default="")
    password = serializers.CharField(write_only=True, min_length=8, max_length=128)
    password_confirm = serializers.CharField(write_only=True, min_length=8, max_length=128)

    def validate_username(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError("Username may not be empty.")
        if User.objects.filter(username__iexact=value.strip()).exists():
            raise serializers.ValidationError("That username is already taken.")
        return value.strip()

    def validate(self, attrs: dict) -> dict:
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs
