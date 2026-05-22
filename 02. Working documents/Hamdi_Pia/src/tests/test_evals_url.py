"""URL query-param helpers for Evals deep link (mirrors app.py logic)."""


def _normalize_qp(raw) -> str:
    if isinstance(raw, list):
        raw = raw[0] if raw else ""
    return str(raw).lower().strip()


def evals_qp_means_scroll(params: dict) -> bool:
    if "evals" not in params:
        return False
    s = _normalize_qp(params.get("evals"))
    return s in ("", "1", "true", "yes")


def test_evals_param_truthy():
    assert evals_qp_means_scroll({"evals": "1"})
    assert evals_qp_means_scroll({"evals": "true"})
    assert evals_qp_means_scroll({"evals": ""})


def test_evals_param_absent_or_off():
    assert not evals_qp_means_scroll({})
    assert not evals_qp_means_scroll({"evals": "0"})
    assert not evals_qp_means_scroll({"evals": "false"})
