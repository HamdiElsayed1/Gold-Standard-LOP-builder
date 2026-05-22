"""LLM-as-a-judge prompt template and response parsing."""

from __future__ import annotations

import re
from dataclasses import dataclass

LLM_AS_A_JUDGE_PROMPT_TEMPLATE = """
You are an expert evaluator tasked with judging the quality of a response.

# Evaluation Criteria
{criteria}

# Reference Answer
{reference}

# Response to Evaluate
{response}

# Instructions
Carefully compare the response against the reference answer based on the evaluation criteria provided above.
It's OK if the response has more details than the reference answer, as long as it meets the criteria.

You must provide:
1. A binary score: 1 if the response meets the criteria (PASS), or 0 if it does not (FAIL)
2. A brief explanation for your decision

Your response MUST follow this exact format:
Score: [0 or 1]
Reasoning: [Your explanation here]

Now evaluate the response:
"""

_SCORE_RE = re.compile(r"Score:\s*([01])\b", re.I)
_REASON_RE = re.compile(r"Reasoning:\s*(.+)", re.I | re.S)


@dataclass(frozen=True)
class JudgeVerdict:
    score: int
    reasoning: str
    raw: str


def format_judge_prompt(*, criteria: str, reference: str, response: str) -> str:
    return LLM_AS_A_JUDGE_PROMPT_TEMPLATE.format(
        criteria=criteria.strip(),
        reference=reference.strip(),
        response=response.strip(),
    )


def parse_judge_response(text: str) -> JudgeVerdict | None:
    if not text or not text.strip():
        return None
    score_m = _SCORE_RE.search(text)
    reason_m = _REASON_RE.search(text)
    if not score_m:
        return None
    score = int(score_m.group(1))
    reasoning = reason_m.group(1).strip() if reason_m else ""
    return JudgeVerdict(score=score, reasoning=reasoning, raw=text.strip())
