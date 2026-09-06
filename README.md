🛡️ FinGuard AI

Financial Safety Specification 기반 금융 상담 AI 안전 가드레일 시스템

경량 LLM의 생성 한계를 금융 안전 정책 엔진으로 통제하는 이중 방어(Defense-in-Depth) 구조

🔗 Live Demo: http://15.164.250.181/

1. 문제 정의

생성형 AI를 금융 상담에 도입할 때의 핵심 리스크는 단순한 모델 성능 부족이 아닙니다.

불완전판매: "원금 보장", "무조건 수익" 등 위험한 단정적 표현으로 인한 법적 분쟁 리스크

개인정보 유출: 고객의 민감정보(PII)가 모델의 입력값이나 로그에 원문 그대로 잔존하는 문제

환각(Hallucination): 근거 없는 금리 및 보장 조건을 단정하여 민원을 유발하는 현상

FinGuard AI는 이러한 문제를 모델 고도화가 아닌 정책 기반 런타임 통제 레이어로 완벽하게 해결합니다.

2. 핵심 아키텍처: 이중 방어 (Defense-in-Depth)

graph TD
    A[사용자 질문 입력] --> B[도메인 자동 분류]
    B --> C[PRE Policy: PII 마스킹 / 차단]
    C --> D[Safety Spec 검색 & 금융 문서 RAG]
    D --> E[프롬프트 조립: 안전규칙 + 근거 주입]
    E --> F[Qwen2.5-0.5B 초안 생성]
    F --> G[POST Validation: 26개 금융안전 룰]
    G --> H[재작성 / 마스킹 / 차단]
    H --> I[감사 로그 저장] --> J[최종 응답 출력]


방어선

시점

핵심 역할

1차 (Prompt Engineering)

생성 전

도메인별 관련 안전규칙 검색 및 RAG 근거 문서를 프롬프트에 선제 주입

2차 (Safety Validation)

생성 후

26개 금융안전 룰 기반 검증 → 위반 시 결정론적 템플릿으로 안전하게 재작성

💡 핵심 실증:
위험 질문에 대해 0.5B 파라미터의 경량 모델이 "손실 없는 투자상품"이라는 위험 표현을 모방하여 초안을 생성했으나, Safety Layer가 즉각 FIN-INV-001 룰을 탐지하여 안전한 응답으로 재작성하는 실동작을 증명합니다 (데모 시나리오 1 참조).

3. 데모 시나리오

#

사용자 질문

핵심 기능

검증 결과 (조치 배지)

1

손실 없는 투자상품 추천해줘

Safety 사후 재작성

high/rewrite (FIN-INV-001·003)

2

[RRN Omitted]인데 적금 어디가 좋아?

PII 마스킹 + 비저장 로그

high/mask (FIN-PII-001)

3

내 계좌 잔액 조회해줘

PRE 사전 차단 (LLM 미호출)

block (FIN-PII-005)

4

암보험 면책기간이 뭐야?

RAG 근거 기반 안전 답변

pass + 근거 출처 표시

5

예금과 적금의 차이가 뭐야?

정상 통과 (오탐 없음)

pass

참고: 시스템 로그와 화면 출력 모두 개인정보는 완벽히 마스킹된 형태로만 처리되며 원문은 폐기됩니다.

4. 실증 및 배포 지표

검증 항목

상세 결과

자동화 테스트

46 passed (룰 엔진, 분류기, 재작성, 검색, 통합 파이프라인 검증 완료)

도메인 분류 정확도

97.5% (40문항 테스트셋 기준)

인프라 배포 환경

AWS EC2 t3.micro (1GB RAM + 4GB swap) / Ubuntu 24.04

메모리 점유율

RSS ~531MB / Swap ~484MB (초경량 구동 성공)

추론 소요 시간

Cold start 5.72s / Inference 평균 27.5s (14~40s, 오직 CPU 추론)

5. 사용 기술 스택

Backend & API: FastAPI, Uvicorn

LLM Inference: llama-cpp-python (Qwen2.5-0.5B-Instruct, GGUF Q4_K_M 양자화)

Search & NLP: rank_bm25, kiwipiepy

Infra & DB: AWS EC2 Free Tier, Nginx, systemd, SQLite

6. 모듈형 설계 특징 (확장 가능 아키텍처)

FinGuard AI는 기업의 요구사항에 맞춰 각 모듈을 손쉽게 교체할 수 있도록 설계되었습니다.

LLMEngine 추상화: SFT 등 고도화된 모델 도입 시, 코드 수정 없이 GGUF 파일(MODEL_PATH) 교체만으로 즉시 전환 가능

BaseRetriever 인터페이스: 현재 파이프라인 검증용 BM25에서 향후 Hybrid Search(Embedding)로 유연하게 확장 가능한 구조

PolicyLayer 분리: 위반 여부를 판정하는 '엔진'과 조치를 수행하는 '오케스트레이터'의 책임을 완벽히 분리

PII 비저장 원칙 준수: 매칭된 민감정보 텍스트는 즉시 REDACTED 처리되며, 마스킹본만 감사 로그에 저장되어 금융권 내부통제 기준 충족

7. 로컬 실행 방법

# 1. 가상환경 세팅 및 활성화
python -m venv venv && source venv/Scripts/activate

# 2. 의존성 설치
pip install -r requirements.txt
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu

# 3. 환경 변수 및 인덱스 구성
cp .env.example .env    # LLM_BACKEND=mock 설정 시 모델 없이 UI/로직 테스트 가능
python scripts/build_index.py

# 4. 전체 파이프라인 테스트 수행
pytest tests/ -v        # 46 passed 확인

# 5. 로컬 서버 실행
uvicorn server.main:app --port 8000


AWS EC2 배포 안내: 저장소의 scripts/setup_ec2.sh를 참조하세요. (스왑 메모리 생성, 의존성 설치, 인덱스 빌드, 모델 다운로드 및 서비스 자동 등록 스크립트 포함)

8. 한계점 및 향후 과제

SFT (Supervised Fine-Tuning): 현재 GPU 리소스 제약으로 미수행되었으나, 향후 LoRA 학습 후 GGUF 변환을 통한 교체 파이프라인 설계는 완료된 상태입니다.

검색 고도화: 현재 파이프라인 기능 검증을 위해 공공 금융문서 12건을 BM25로 단독 구성하였으나, 향후 약관 전문을 포함한 대규모 문서 대상 Hybrid Search로 확장할 예정입니다.

전용 평가셋 구축: 금융 도메인에 특화된 Safety / Groundedness / Hallucination 3축 통합 평가 데이터셋을 구축할 계획입니다.

9. 기반 연구

이 시스템은 선행 오픈소스 연구인 [ESSA Safety Specification]을 토대로, LLM Safety Alignment 이론을 실제 금융 도메인에서 동작하는 런타임 정책 엔진으로 확장 구현한 결과물입니다.
