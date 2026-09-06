from server.schemas import Evidence

SYSTEM_PROMPT = (
    "당신은 금융소비자 보호 원칙을 준수하는 한국어 금융 안내 AI입니다.\n"
    "규칙:\n"
    "1. 수익 보장, 무손실, 무조건 보장 같은 단정 표현을 절대 사용하지 않는다.\n"
    "2. 제공된 [참고 문서] 범위 안에서만 답하고, 문서에 없는 수치나 조건을 지어내지 않는다.\n"
    "3. 확실하지 않은 내용은 '공식 채널 확인이 필요합니다'라고 안내한다.\n"
    "4. 투자 관련 답변에는 원금 손실 가능성을 함께 안내한다.\n"
    "5. 답변은 3~5문장으로 간결하게 작성한다."
)


def build_messages(query: str, spec_context: list[Evidence],
                   evidence: list[Evidence]) -> list[dict]:
    """system / spec / evidence / user query를 구분해 메시지로 조립.
    각 블록은 명시적 헤더로 분리되어 포함 여부를 테스트할 수 있다."""
    parts = []
    if spec_context:
        rules = "\n".join(f"- ({e.doc_id}) {e.title}" for e in spec_context)
        parts.append(f"[적용 안전 규칙]\n{rules}")
    if evidence:
        docs = "\n\n".join(f"[참고 문서 {e.doc_id}] {e.title}\n{e.content}"
                           for e in evidence)
        parts.append(docs)
    parts.append(f"[질문]\n{query}")

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "\n\n".join(parts)},
    ]
