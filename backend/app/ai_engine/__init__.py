"""
TalentMatch AI Engine — Core AI/NLP components for resume parsing,
skill extraction, semantic matching, and candidate scoring.
"""

from app.ai_engine.embeddings import EmbeddingService
from app.ai_engine.insights import CandidateInsights
from app.ai_engine.interview_questions import InterviewQuestionGenerator
from app.ai_engine.matching_engine import MatchingEngine
from app.ai_engine.skill_dictionary import SKILL_DICTIONARY, SKILL_SYNONYMS
from app.ai_engine.skill_extractor import SkillExtractor

__all__ = [
    "SKILL_DICTIONARY",
    "SKILL_SYNONYMS",
    "CandidateInsights",
    "EmbeddingService",
    "InterviewQuestionGenerator",
    "MatchingEngine",
    "SkillExtractor",
]
