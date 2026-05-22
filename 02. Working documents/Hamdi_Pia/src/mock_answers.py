"""
Mock answer generator — invokes the Mock Partner Agent (Hamdi/agents/mock-partner-agent.md)
to seed plausible, intentionally uneven partner answers for the Gate A question list.

The agent intelligence (system prompt + output schema) lives in the markdown spec.
This module just packages the question list as input and validates the response.
"""

import json

from orchestrator import run_agent
from schemas import Answer, AnswerList, QuestionList


def generate_mock_answers(question_list: QuestionList) -> AnswerList:
    """
    Call the Mock Partner Agent to generate one plausible answer per question.
    Returns an AnswerList with one Answer per question (in original question order).
    Any question that comes back without an answer falls back to a placeholder.
    """
    questions_payload = [
        {
            "id": q.id,
            "chapter": q.chapter,
            "question": q.question,
            "why_asked": q.why_asked,
            "expected_answer_type": q.expected_answer_type,
        }
        for q in question_list.questions
    ]

    user_msg = (
        "Generate mock partner answers for the following questions from a "
        "Letter of Proposal pre-call briefing. Return one answer per question, "
        "with intentional quality variation as specified in your instructions.\n\n"
        f"Questions:\n{json.dumps(questions_payload, indent=2)}"
    )

    result = run_agent(
        "mock-partner-agent",
        user_message=user_msg,
        files=None,
    )

    raw_answers = result.get("answers", []) or []
    answer_map = {
        a.get("question_id"): a.get("answer_text", "")
        for a in raw_answers
        if isinstance(a, dict) and a.get("question_id")
    }

    answers = [
        Answer(
            question_id=q.id,
            answer_text=answer_map.get(q.id) or "No answer provided.",
        )
        for q in question_list.questions
    ]

    return AnswerList(answers=answers)
