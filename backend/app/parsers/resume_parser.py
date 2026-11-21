import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from app.ai_engine.skill_extractor import SkillExtractor


class ResumeParser:
    """
    Intelligent Information Extraction from Resume Plain Text.
    Extracts contact info, education, work experience, skills, and projects.
    """

    def __init__(self):
        self.skill_extractor = SkillExtractor()

    def parse(self, text: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """Parse raw resume text into structured candidate profile."""
        if not text:
            return self._empty_profile(filename)

        lines = [line.strip() for line in text.splitlines() if line.strip()]

        name = self._extract_name(lines, filename)
        email = self._extract_email(text)
        phone = self._extract_phone(text)
        location = self._extract_location(text)
        education = self._extract_education(text)
        experience_items, total_exp = self._extract_experience(text)
        skills_extracted = self.skill_extractor.extract_skills(text)
        projects = self._extract_projects(text)
        certifications = self._extract_certifications(text)

        # Compute parsing confidence based on completeness of extracted attributes
        conf = 0.0
        if name and name != "Candidate":
            conf += 0.20
        if email:
            conf += 0.20
        if phone:
            conf += 0.15
        if skills_extracted:
            conf += 0.20
        if experience_items or total_exp > 0:
            conf += 0.15
        if education:
            conf += 0.10
        parsing_confidence = round(min(1.0, conf), 2)

        return {
            "name": name,
            "email": email,
            "phone": phone,
            "location": location,
            "total_experience_years": total_exp,
            "education": education,
            "experience": experience_items,
            "projects": projects,
            "certifications": certifications,
            "skills": skills_extracted,
            "parsing_confidence": parsing_confidence,
            "extracted_at": datetime.now(timezone.utc).isoformat(),
        }

    def _empty_profile(self, filename: Optional[str]) -> Dict[str, Any]:
        fallback_name = "Candidate"
        if filename:
            cleaned = re.sub(r"\.(pdf|docx|doc|txt)$", "", filename, flags=re.IGNORECASE)
            fallback_name = cleaned.replace("_", " ").replace("-", " ").title()
        return {
            "name": fallback_name,
            "email": None,
            "phone": None,
            "location": "Not specified",
            "total_experience_years": 0.0,
            "education": [],
            "experience": [],
            "projects": [],
            "certifications": [],
            "skills": [],
            "parsing_confidence": 0.0,
            "extracted_at": datetime.now(timezone.utc).isoformat(),
        }

    def _extract_email(self, text: str) -> Optional[str]:
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
        match = re.search(email_pattern, text)
        return match.group(0).lower() if match else None

    def _extract_phone(self, text: str) -> Optional[str]:
        # Matches formats: +1-555-555-5555, (555) 555-5555, +91 9876543210, 555.555.5555, +1 234 567 8900
        phone_pattern = r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
        matches = re.findall(phone_pattern, text)
        for m in matches:
            cleaned = re.sub(r"\D", "", m)
            if 10 <= len(cleaned) <= 15:
                return m.strip()
        return None

    def _extract_name(self, lines: List[str], filename: Optional[str]) -> str:
        # Check for explicit "Name: <Candidate Name>"
        for line in lines[:10]:
            name_prefix = re.search(r"^(?:name|candidate name|full name)\s*[:\-]\s*([A-Z][a-zA-Z.'-]+(?:\s+[A-Z][a-zA-Z.'-]+){1,3})", line, flags=re.IGNORECASE)
            if name_prefix:
                return name_prefix.group(1).strip()

        # Check first 6 lines for a clean candidate name
        ignored_keywords = [
            "resume", "curriculum vitae", "cv", "page", "contact",
            "email", "phone", "address", "portfolio", "github", "linkedin",
            "summary", "profile", "objective", "experience", "education",
            "skills", "projects", "certifications", "technologies"
        ]

        for line in lines[:6]:
            clean_line = line.strip()
            # If line is 2 to 4 words, alphabetic, title case or all caps
            if 2 <= len(clean_line) <= 50:
                lower = clean_line.lower()
                if any(kw in lower for kw in ignored_keywords):
                    continue
                if re.match(r"^[A-Z][a-zA-Z.'-]+(?:\s+[A-Z][a-zA-Z.'-]+){1,3}$", clean_line):
                    return clean_line
                if clean_line.isupper() and 2 <= len(clean_line.split()) <= 4:
                    return clean_line.title()

        # Fallback to filename if available
        if filename:
            cleaned = re.sub(r"\.(pdf|docx|doc|txt)$", "", filename, flags=re.IGNORECASE)
            cleaned = re.sub(r"(resume|cv|_|-|\d+)", " ", cleaned, flags=re.IGNORECASE).strip()
            if cleaned:
                return cleaned.title()

        return "Candidate"

    def _extract_location(self, text: str) -> str:
        # Common locations / format (City, State / Country)
        loc_pattern = r"\b([A-Z][a-zA-Z]+(?:[\s-][A-Z][a-zA-Z]+)?),\s*([A-Z]{2}|[A-Z][a-zA-Z]+)\b"
        matches = re.findall(loc_pattern, text[:1500])
        for city, state_or_country in matches:
            if city.lower() not in ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december", "experience", "education", "skills", "projects"]:
                return f"{city}, {state_or_country}"
        return "Remote / Flexible"

    def _extract_education(self, text: str) -> List[Dict[str, Any]]:
        education_records = []
        edu_keywords = [
            r"\b(Ph\.?D\.?|Doctor of Philosophy)\b",
            r"\b(Master(?:'s)? of [A-Za-z\s]+|M\.?S\.?|M\.?Tech\.?|M\.?B\.?A\.?|M\.?A\.?)\b",
            r"\b(Bachelor(?:'s)? of [A-Za-z\s]+|B\.?S\.?|B\.?Tech\.?|B\.?E\.?|B\.?A\.?|B\.?Sc\.?)\b",
            r"\b(Associate(?:'s)? Degree|Diploma)\b"
        ]

        text_lower = text.lower()
        years = re.findall(r"\b(19\d{2}|20\d{2})\b", text)

        for pat in edu_keywords:
            matches = re.finditer(pat, text, flags=re.IGNORECASE)
            for m in matches:
                degree = m.group(0).strip()
                # Find nearby year
                grad_year = None
                start_pos = max(0, m.start() - 50)
                end_pos = min(len(text), m.end() + 100)
                snippet = text[start_pos:end_pos]
                year_match = re.search(r"\b(20\d{2}|19\d{2})\b", snippet)
                if year_match:
                    grad_year = year_match.group(0)

                # Find institution keyword
                institution = "University / College"
                inst_match = re.search(r"([A-Z][a-zA-Z\s]+(?:University|College|Institute|Polytechnic|Academy))", snippet)
                if inst_match:
                    institution = inst_match.group(0).strip()

                education_records.append({
                    "degree": degree,
                    "institution": institution,
                    "year": grad_year
                })

        # Deduplicate
        unique_records = []
        seen = set()
        for r in education_records:
            key = (r["degree"].lower(), r.get("institution", "").lower())
            if key not in seen:
                seen.add(key)
                unique_records.append(r)

        return unique_records

    def _extract_experience(self, text: str) -> (List[Dict[str, Any]], float):
        experience_items = []

        # 1. Search for explicit mentions like "5+ years of experience", "4 years experience"
        exp_mention = re.search(r"(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)(?:\s*of)?\s*(?:relevant\s*)?experience", text, flags=re.IGNORECASE)
        explicit_years = float(exp_mention.group(1)) if exp_mention else 0.0

        # Month lookup map
        month_map = {
            "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
            "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
            "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
            "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12
        }

        # 2. Extract date ranges: e.g. "Jan 2019 - Present", "05/2020 - 08/2023", "2018 - 2022"
        date_pattern = r"(?:([A-Za-z]+|\d{1,2})[\s\/\.-]+)?(20\d{2}|19\d{2})\s*[-–—to]+\s*(?:([A-Za-z]+|\d{1,2})[\s\/\.-]+)?(20\d{2}|19\d{2}|Present|Current|Now)"
        matches = list(re.finditer(date_pattern, text, flags=re.IGNORECASE))

        intervals = []
        now = datetime.now()
        current_year = now.year
        current_month = now.month

        for m in matches:
            start_m_raw = m.group(1).lower().strip() if m.group(1) else None
            start_yr = int(m.group(2))
            end_m_raw = m.group(3).lower().strip() if m.group(3) else None
            end_val = m.group(4).lower().strip()

            # Determine start month
            if start_m_raw and start_m_raw in month_map:
                start_m = month_map[start_m_raw]
            elif start_m_raw and start_m_raw.isdigit() and 1 <= int(start_m_raw) <= 12:
                start_m = int(start_m_raw)
            else:
                start_m = 1

            # Determine end month & year
            if any(p in end_val for p in ["present", "current", "now"]):
                end_yr = current_year
                end_m = current_month
            else:
                end_yr = int(end_val) if end_val.isdigit() else current_year
                if end_m_raw and end_m_raw in month_map:
                    end_m = month_map[end_m_raw]
                elif end_m_raw and end_m_raw.isdigit() and 1 <= int(end_m_raw) <= 12:
                    end_m = int(end_m_raw)
                else:
                    end_m = 12

            start_dec = start_yr + (start_m - 1) / 12.0
            end_dec = end_yr + (end_m - 1) / 12.0

            duration = max(0.2, end_dec - start_dec)
            if 0 < duration <= 45.0:  # reasonable cap
                intervals.append((start_dec, end_dec))

                # Look for surrounding role title context
                start_context = max(0, m.start() - 80)
                context = text[start_context:m.start()].strip().split("\n")[-1]
                title = context.strip() if 3 < len(context.strip()) < 50 else "Professional Role"

                experience_items.append({
                    "title": title,
                    "duration": f"{m.group(2)} - {m.group(4)}",
                    "years": round(duration, 1)
                })

        # Merge overlapping date intervals to prevent double-counting parallel roles
        if intervals:
            intervals.sort(key=lambda x: x[0])
            merged = [intervals[0]]
            for current in intervals[1:]:
                prev_start, prev_end = merged[-1]
                if current[0] <= prev_end:
                    merged[-1] = (prev_start, max(prev_end, current[1]))
                else:
                    merged.append(current)
            calculated_years = sum(max(0.2, end - start) for start, end in merged)
        else:
            calculated_years = 0.0

        total_years = max(explicit_years, calculated_years)
        return experience_items, round(min(total_years, 35.0), 1)

    def _extract_projects(self, text: str) -> List[Dict[str, str]]:
        projects = []
        proj_section = re.search(r"(?:projects|key projects|academic projects)\s*[:\n](.*?)(?=(?:experience|education|skills|certifications|awards|\Z))", text, flags=re.IGNORECASE | re.DOTALL)
        if proj_section:
            snippet = proj_section.group(1).strip()
            # Split into project bullets or blocks
            blocks = [b.strip() for b in re.split(r"\n(?=[•\-\*]|\d+\.|\b[A-Z][A-Za-z0-9\s]{3,30}:)", snippet) if b.strip()]
            for b in blocks[:5]:
                first_line = b.splitlines()[0][:60]
                projects.append({"name": first_line, "description": b[:250]})
        return projects

    def _extract_certifications(self, text: str) -> List[str]:
        certifications = []
        cert_matches = re.findall(r"(?:AWS Certified|Azure Certified|GCP Certified|PMP|Scrum Master|CKA|CKAD|CISSP|CompTIA\s+[A-Za-z0-9+]+|TensorFlow Developer|Google Cloud Certified)", text, flags=re.IGNORECASE)
        for c in cert_matches:
            if c not in certifications:
                certifications.append(c.strip())
        return certifications
