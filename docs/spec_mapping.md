# ESSA Safety Spec ↔ FinGuard Rule 매핑

| rule_id | 카테고리 | ESSA spec 참조 | 검증 레벨 | 상태 |
|---|---|---|---|---|
| FIN-INV-001~007 | investment | Finance & Banking / investment-* | surface | 앵커 <확인 필요> |
| FIN-INS-001~007 | insurance | Finance & Banking / insurance-* | surface | 앵커 <확인 필요> |
| FIN-PII-001~006 | pii | Finance & Banking / pii-* | surface | 앵커 <확인 필요> |
| FIN-HAL-001~006 | hallucination | Finance & Banking / claims-* | surface | 앵커 <확인 필요> |
| FIN-HAL-1xx (예약) | hallucination | 동일 | **grounding** | RAG+Judge 단계 |

※ spec_source 앵커는 ESSA 원문 섹션명 확인 후 확정한다.
※ surface = 표현 수준 탐지 (사실성 판단 아님) / grounding = 응답-근거 대조 (이후 단계)
