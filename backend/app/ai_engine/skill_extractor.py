import re
from typing import Any

from app.ai_engine.skill_dictionary import FLATTENED_SKILLS, SKILL_SYNONYMS


class SkillExtractor:
    """
    NLP and Rule-based skill extraction engine.
    Extracts explicit skills, matches synonyms, and categorizes technologies.
    """

    def __init__(self):
        # Precompile exact skill regexes sorted by length descending (longest first)
        self.all_skills = sorted(FLATTENED_SKILLS.keys(), key=lambda x: len(x), reverse=True)

    def extract_skills(self, text: str) -> list[dict[str, Any]]:
        """
        Extract unique skills from text with confidence, category, and evidence snippet.
        """
        if not text:
            return []

        text_lower = text.lower()
        extracted: dict[str, dict[str, Any]] = {}

        # 1. Check direct skill names
        for skill_key in self.all_skills:
            # Special regex to match symbols like C++, C#, .NET or word boundaries
            escaped_key = re.escape(skill_key)
            if skill_key in ["c++", "c#", ".net", "c"]:
                pattern = r"(?:^|[\s,;:\(\)\[\]/\\])" + escaped_key + r"(?:$|[\s,;:\(\)\[\]/\\])"
            else:
                pattern = r"\b" + escaped_key + r"\b"

            matches = list(re.finditer(pattern, text_lower))
            if matches:
                canonical_name = FLATTENED_SKILLS[skill_key]["name"]
                category = FLATTENED_SKILLS[skill_key]["category"]

                # Grab a short snippet of context around first occurrence
                start = max(0, matches[0].start() - 30)
                end = min(len(text), matches[0].end() + 30)
                evidence = text[start:end].replace("\n", " ").strip()

                count = len(matches)
                confidence = min(0.99, 0.75 + (0.05 * min(count, 5)))

                extracted[canonical_name] = {
                    "skill_name": canonical_name,
                    "category": category,
                    "confidence": round(confidence, 2),
                    "frequency": count,
                    "evidence": f"...{evidence}...",
                    "source": "exact",
                }

        # 2. Check synonyms & abbreviations
        for synonym, canonical in SKILL_SYNONYMS.items():
            if canonical in extracted:
                continue

            escaped_synonym = re.escape(synonym)
            pattern = r"\b" + escaped_synonym + r"\b"
            matches = list(re.finditer(pattern, text_lower))
            if matches:
                canonical_lower = canonical.lower()
                category = FLATTENED_SKILLS.get(canonical_lower, {}).get("category", "technical")

                start = max(0, matches[0].start() - 30)
                end = min(len(text), matches[0].end() + 30)
                evidence = text[start:end].replace("\n", " ").strip()

                extracted[canonical] = {
                    "skill_name": canonical,
                    "category": category,
                    "confidence": 0.85,
                    "frequency": len(matches),
                    "evidence": f"...{evidence} (synonym: {synonym})...",
                    "source": "synonym",
                }

        return list(extracted.values())

    def get_skill_names(self, text: str) -> list[str]:
        """Convenience method returning just a list of extracted canonical skill names."""
        extracted = self.extract_skills(text)
        return [item["skill_name"] for item in extracted]
