"""Table vs prose numeric co-occurrence within a section."""

from __future__ import annotations

from decimal import Decimal

from lop_eval.models import EvalConfig, EvalIssue, IssueSeverity, ProposalDocument, TableBlock
from lop_eval.normalize import extract_normalized_numbers, numbers_close
from lop_eval.text_extract import section_narrative_text


def check_claim_support(doc: ProposalDocument, config: EvalConfig) -> list[EvalIssue]:
    issues: list[EvalIssue] = []
    max_cells = 20

    for sec in doc.sections:
        table_nums: list[Decimal] = []
        n_cells = 0
        for block in sec.blocks:
            if isinstance(block, TableBlock):
                for row in block.rows:
                    for cell in row:
                        if n_cells >= max_cells:
                            break
                        n_cells += 1
                        for nn in extract_normalized_numbers(cell):
                            if nn.value is not None:
                                table_nums.append(nn.value)
                    if n_cells >= max_cells:
                        break
                if n_cells >= max_cells:
                    break

        if not table_nums:
            continue

        prose = section_narrative_text(sec)
        prose_vals: list[Decimal] = []
        for nn in extract_normalized_numbers(prose):
            if nn.value is not None:
                prose_vals.append(nn.value)

        if not prose_vals:
            issues.append(
                EvalIssue(
                    type="claim_support_table_prose_gap",
                    severity=IssueSeverity.minor,
                    description=f"Section '{sec.id}' has numeric table cells but no numbers in narrative/caption.",
                    offending_text=str(table_nums[:5]),
                    expected_text_or_rule="Echo key table figures in supporting prose when the section summarizes the table.",
                    checker_id="claim_support",
                )
            )
            continue

        unmatched: list[Decimal] = []
        for tv in table_nums:
            if not any(
                numbers_close(tv, pv, config.numeric_relative_tolerance) for pv in prose_vals
            ):
                unmatched.append(tv)

        if unmatched:
            issues.append(
                EvalIssue(
                    type="claim_support_table_prose_gap",
                    severity=IssueSeverity.minor,
                    description=f"Section '{sec.id}' has table figures not clearly echoed in narrative/caption.",
                    offending_text=str(unmatched[:5]),
                    expected_text_or_rule="Key table values should appear in supporting prose when narrative summarizes the table.",
                    checker_id="claim_support",
                )
            )
    return issues
