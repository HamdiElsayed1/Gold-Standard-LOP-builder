"""
Voice answer pipeline — turns a partner's consolidated voice memo into the
same `AnswerList` shape that `mock_answers.generate_mock_answers` produces.

Two stages:
  1. whisper-1 transcribes the raw audio (via voice_transcription.transcribe_audio)
  2. voice-splitter-agent maps transcript segments → one answer per question_id

The output preserves the original question order and guarantees one Answer per
question (empty string when the transcript did not address it), so the rest of
the pipeline (edit UI, validation, dot-dash) does not need to know whether the
answers came from voice, mocks, or typed input.
"""

import json

from orchestrator import run_agent
from schemas import Answer, AnswerList, QuestionList
from voice_transcription import transcribe_audio


def transcribe_and_map(
    audio_bytes: bytes,
    filename: str,
    question_list: QuestionList,
) -> tuple[str, AnswerList]:
    """
    Transcribe `audio_bytes` with whisper-1, then ask the voice-splitter-agent
    to map the transcript onto `question_list`.

    Returns
    -------
    (transcript, answer_list)
        The raw whisper-1 transcript (so the UI can show it for review) and an
        `AnswerList` containing one `Answer` per input question, in the same
        order. Questions the transcript did not address come back with an
        empty `answer_text`.
    """
    transcript = transcribe_audio(audio_bytes, filename)

    if not transcript:
        # Whisper returned nothing; surface empty answers rather than failing,
        # so the partner can fall back to typing in the edit UI.
        return "", AnswerList(
            answers=[Answer(question_id=q.id, answer_text="") for q in question_list.questions]
        )

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
        "Map this consolidated partner voice-memo transcript onto the question "
        "list. Return one answer per question_id, in the same order as the "
        "questions. Use only the partner's own words, lightly cleaned. Leave "
        "answer_text empty for any question the transcript does not address.\n\n"
        f"Transcript:\n\"\"\"\n{transcript}\n\"\"\"\n\n"
        f"Questions:\n{json.dumps(questions_payload, indent=2)}"
    )

    result = run_agent(
        "voice-splitter-agent",
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
            answer_text=(answer_map.get(q.id) or ""),
        )
        for q in question_list.questions
    ]

    return transcript, AnswerList(answers=answers)
