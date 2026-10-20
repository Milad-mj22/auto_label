from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DefectItem:
    name: str
    description: str
    confidence: Optional[float] = None


@dataclass
class AnalysisResult:
    summary: str
    defects: list[DefectItem] = field(default_factory=list)
    raw_text: str = ""


class AIProviderError(Exception):
    pass


class AIProvider(ABC):
    @abstractmethod
    def analyze_image(self, image_path: str, prompt: str, industry: str) -> AnalysisResult:
        ...

    @abstractmethod
    def answer_question(self, image_path: str, context: str, question: str) -> str:
        ...