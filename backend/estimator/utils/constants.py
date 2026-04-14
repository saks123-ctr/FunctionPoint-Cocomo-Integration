"""IFPUG-style weights and COCOMO Basic coefficients."""

FP_WEIGHTS = {
    "EI": (3, 4, 6),
    "EO": (4, 5, 7),
    "EQ": (3, 4, 6),
    "ILF": (7, 10, 15),
    "EIF": (5, 7, 10),
}

GSC_LABELS = (
    "Data communications",
    "Distributed data processing",
    "Performance",
    "Heavily used configuration",
    "Transaction rate",
    "Online data entry",
    "End-user efficiency",
    "Online update",
    "Complex processing",
    "Reusability",
    "Installation ease",
    "Operational ease",
    "Multiple sites",
    "Facilitate change",
)

GSC_COUNT = len(GSC_LABELS)

COCOMO_MODES = {
    "organic": (2.4, 1.05, 2.5, 0.38),
    "semi_detached": (3.0, 1.12, 2.5, 0.35),
    "embedded": (3.6, 1.20, 2.5, 0.32),
}

FP_TO_KLOC_DIVISOR = 100
