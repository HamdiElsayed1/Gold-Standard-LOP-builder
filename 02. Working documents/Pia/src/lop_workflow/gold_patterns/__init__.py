"""Gold-pattern catalog (structure, win logic, evidence gates) for LoP drafting."""

from lop_workflow.gold_patterns.loader import (
    GoldCatalog,
    SectionGoldPattern,
    get_section_pattern,
    load_gold_catalog,
)

__all__ = ["GoldCatalog", "SectionGoldPattern", "get_section_pattern", "load_gold_catalog"]
