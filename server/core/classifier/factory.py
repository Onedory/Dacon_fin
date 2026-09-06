from server.config import Settings
from server.core.classifier.base import BaseClassifier
from server.core.classifier.keyword_classifier import KeywordClassifier


def create_classifier(settings: Settings) -> BaseClassifier:
    if settings.classifier_backend == "keyword":
        return KeywordClassifier(settings.domain_keywords_path)
    # 향후: "ml", "llm" 백엔드 등록 지점
    raise ValueError(f"Unknown CLASSIFIER_BACKEND: {settings.classifier_backend}")
