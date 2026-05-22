# Test case catalog

Structured fixtures live in `fixtures/*.json`. Expected signals:

| Fixture | Expect issues | Notes |
|---------|---------------|--------|
| `positive_numeric.json` | none (numeric) | Same revenue figure twice |
| `negative_numeric_revenue.json` | `numeric_conflict`, critical | EUR 100 vs 120 under revenue |
| `negative_stock_year.json` | `numeric_year_inconsistency`, major | Same price, different FY |
| `positive_terminology.json` | none (terminology) | Single label bucket |
| `negative_term_drift.json` | `terminology_drift`, major | transformation + sprint |
| `terminology_bridge_minor.json` | `terminology_drift`, minor | equivalence wording present |
| `negative_scope.json` | `scope_drift`, major | EMEA only vs global |
| `negative_timeline.json` | `timeline_phase_month_conflict`, major | Phase 2 March vs May |
| `negative_units.json` | `unit_currency_mixing`, major | USD + EUR same section |
| `negative_formatting.json` | `representation_percent_vs_decimal`, major | 10% + bare 0.1 |
| `negative_claim_support.json` | `claim_support_table_prose_gap`, minor | table EUR 42 not in prose |
| `negative_comparative.json` | `comparative_conflict`, major | fastest vs slowest same topic |
| `negative_abbreviation.json` | `abbreviation_conflict`, major | two IBM expansions |
| `faithfulness_missing.json` | `faithfulness_missing_fact`, major when SoT passed in test | see integration test |

Scores and `passed` depend on `EvalConfig` — tests assert **presence/absence of issue types**, not only pass/fail.
