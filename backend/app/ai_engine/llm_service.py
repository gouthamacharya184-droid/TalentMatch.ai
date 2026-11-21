import os
import json
import logging
from typing import List, Dict, Any, Optional
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """
    Unified LLM Service supporting Google Gemini, OpenAI, and Groq.
    Provides intelligent chatbot responses, interview question generation, and recruiter insights.
    Includes automated model fallback and graceful offline/quota resilience.
    """

    def __init__(self):
        self.enabled = getattr(settings, "LLM_ENABLED", False)
        self.api_key = getattr(settings, "LLM_API_KEY", "") or os.environ.get("LLM_API_KEY", "")
        self.model = getattr(settings, "LLM_MODEL", "gemini-flash-lite-latest") or "gemini-flash-lite-latest"

    def is_available(self) -> bool:
        if os.environ.get("PYTEST_CURRENT_TEST"):
            return False
        return bool(self.enabled and self.api_key and self.api_key.strip() and self.api_key.strip() != "PASTE_YOUR_API_KEY_HERE")

    def _detect_provider(self) -> str:
        key = (self.api_key or "").strip()
        model_lower = (self.model or "").lower()
        if key.startswith("AIzaSy") or "gemini" in model_lower or "gemma" in model_lower:
            return "gemini"
        elif key.startswith("gsk_") or "groq" in model_lower:
            return "groq"
        elif key.startswith("sk-") or "gpt" in model_lower:
            return "openai"
        return "gemini"

    def _candidate_gemini_models(self) -> List[str]:
        primary = self.model.replace("models/", "")
        fallbacks = ["gemini-2.5-flash"]
        models = [primary]
        for f in fallbacks:
            if f not in models:
                models.append(f)
        return models

    def generate_chat_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        max_tokens: int = 1500
    ) -> Optional[str]:
        """Generate conversational markdown response from messages."""
        if not self.is_available():
            return None

        provider = self._detect_provider()
        if provider == "gemini":
            return self._call_gemini_chat(messages, system_prompt, max_tokens)
        elif provider == "groq":
            return self._call_openai_chat(messages, system_prompt, "https://api.groq.com/openai/v1/chat/completions", max_tokens)
        else:
            return self._call_openai_chat(messages, system_prompt, "https://api.openai.com/v1/chat/completions", max_tokens)

    def _call_gemini_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        max_tokens: int
    ) -> Optional[str]:
        """Send chat messages to Gemini API with model fallback on rate-limits."""
        contents = []
        for msg in messages:
            role = "user" if msg.get("role") == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg.get("content", "")}]
            })

        payload = {
            "systemInstruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": contents,
            "generationConfig": {
                "temperature": 0.35,
                "maxOutputTokens": max_tokens
            }
        }

        for model_name in self._candidate_gemini_models():
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key.strip()}"
            try:
                with httpx.Client(timeout=8.0) as client:
                    resp = client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            text_parts = [p.get("text", "") for p in parts if "text" in p and not p.get("thought", False)]
                            return "".join(text_parts).strip() if text_parts else parts[0].get("text", "").strip()
                    elif resp.status_code in (400, 401, 403):
                        logger.warning(f"Gemini API authentication/key rejected ({resp.status_code}): {resp.text[:150]}. Breaking to fallback.")
                        break
                    elif resp.status_code == 429:
                        logger.warning(f"Model {model_name} rate limited (429). Attempting fallback...")
                        continue
                    else:
                        logger.warning(f"Gemini {model_name} returned status {resp.status_code}: {resp.text[:200]}")
            except Exception as e:
                logger.error(f"Error calling Gemini {model_name}: {e}")

        return None

    def _call_openai_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        base_url: str,
        max_tokens: int
    ) -> Optional[str]:
        """Send chat messages to OpenAI or Groq endpoint."""
        api_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            api_messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })

        headers = {
            "Authorization": f"Bearer {self.api_key.strip()}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": api_messages,
            "temperature": 0.35,
            "max_tokens": max_tokens
        }

        try:
            with httpx.Client(timeout=25.0) as client:
                resp = client.post(base_url, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"].strip()
                else:
                    logger.warning(f"OpenAI/Groq returned {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            logger.error(f"Error calling OpenAI/Groq: {e}")
        return None

    def generate_json(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Dispatch prompt to configured provider and parse JSON output."""
        if not self.is_available():
            return None

        provider = self._detect_provider()
        raw_text = None

        if provider == "gemini":
            for model_name in self._candidate_gemini_models():
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key.strip()}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.3,
                        "maxOutputTokens": 4096,
                        "responseMimeType": "application/json"
                    }
                }
                try:
                    with httpx.Client(timeout=8.0) as client:
                        resp = client.post(url, json=payload)
                        if resp.status_code == 200:
                            data = resp.json()
                            candidates = data.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                text_parts = [p.get("text", "") for p in parts if "text" in p and not p.get("thought", False)]
                                raw_text = "".join(text_parts).strip() if text_parts else parts[0].get("text", "").strip()
                                break
                        elif resp.status_code in (400, 401, 403):
                            logger.warning(f"Gemini API key rejected in JSON generation ({resp.status_code}). Breaking to fallback.")
                            break
                        elif resp.status_code == 429:
                            logger.warning(f"JSON generation on {model_name} rate-limited. Trying fallback...")
                            continue
                        else:
                            logger.warning(f"Gemini {model_name} returned {resp.status_code}: {resp.text[:200]}")
                except Exception as e:
                    logger.error(f"Error calling Gemini {model_name}: {e}")
        else:
            base_url = "https://api.groq.com/openai/v1/chat/completions" if provider == "groq" else "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key.strip()}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are an expert technical recruiter assistant. Always respond in valid JSON format."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 1024,
                "response_format": {"type": "json_object"}
            }
            try:
                with httpx.Client(timeout=25.0) as client:
                    resp = client.post(base_url, headers=headers, json=payload)
                    if resp.status_code == 200:
                        raw_text = resp.json()["choices"][0]["message"]["content"]
            except Exception as e:
                logger.error(f"Error calling {provider}: {e}")

        if not raw_text:
            return None

        try:
            clean = raw_text.strip()
            if clean.startswith("```"):
                lines = clean.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                clean = "\n".join(lines).strip()
            return json.loads(clean)
        except Exception as e:
            logger.warning(f"Failed to parse LLM JSON: {e}")
            return None

    def generate_interview_questions(
        self,
        job_title: str,
        matched_skills: List[str],
        missing_skills: List[str],
        experience_years: float,
        candidate_projects: List[Dict[str, Any]]
    ) -> Optional[List[Dict[str, Any]]]:
        """Generate tailored interview questions via LLM."""
        if not self.is_available():
            return None

        prompt = f"""
You are an executive technical interviewer. Generate 4 structured, highly specific interview questions for a candidate applying for '{job_title}'.

Candidate Profile:
- Total Experience: {experience_years} years
- Matched Core Skills: {', '.join(matched_skills[:6]) if matched_skills else 'General technical skills'}
- Missing / Unverified Skills from Job: {', '.join(missing_skills[:4]) if missing_skills else 'None'}
- Projects Summary: {json.dumps(candidate_projects[:2]) if candidate_projects else 'Standard engineering projects'}

Return a JSON object with this exact structure:
{{
  "questions": [
    {{
      "type": "Core Technical",
      "skill": "<Skill Name>",
      "question": "<Tailored question>",
      "evaluation_criteria": "<What to listen for in candidate response>",
      "difficulty": "Advanced" | "Intermediate" | "Senior"
    }},
    {{
      "type": "Skill Gap Verification",
      "skill": "<Missing Skill>",
      "question": "<Question probing familiarity or aptitude with missing skill>",
      "evaluation_criteria": "<Criteria>",
      "difficulty": "Intermediate"
    }},
    {{
      "type": "Architecture & System Design",
      "skill": "System Design",
      "question": "<System design or scale question tailored to {job_title}>",
      "evaluation_criteria": "<Criteria>",
      "difficulty": "Senior"
    }},
    {{
      "type": "Project Deep-Dive",
      "skill": "Technical Delivery",
      "question": "<Deep dive question based on projects or production troubleshooting>",
      "evaluation_criteria": "<Criteria>",
      "difficulty": "Advanced"
    }}
  ]
}}
"""
        result = self.generate_json(prompt)
        if result and isinstance(result, dict) and "questions" in result:
            qs = result["questions"]
            if isinstance(qs, list) and len(qs) >= 2:
                return qs
        return None

    def generate_candidate_insights(
        self,
        candidate_name: str,
        overall_score: float,
        matched_skills: List[Dict[str, Any]],
        missing_skills: List[str],
        experience_years: float,
        min_experience_required: float
    ) -> Optional[Dict[str, Any]]:
        """Generate structured recruiter insights & checklist via LLM."""
        if not self.is_available():
            return None

        matched_names = [m.get("skill", "") if isinstance(m, dict) else str(m) for m in matched_skills]
        prompt = f"""
You are an expert talent acquisition consultant. Analyze this candidate match and provide executive recruiter insights.

Job Requirements Context:
- Minimum Experience Required: {min_experience_required} years

Candidate Match Data:
- Candidate Name: {candidate_name}
- Overall Match Score: {overall_score}/100
- Recorded Experience: {experience_years} years
- Aligned Skills: {', '.join(matched_names[:8])}
- Missing / Gap Skills: {', '.join(missing_skills[:6]) if missing_skills else 'None'}

Return a JSON object with this exact schema:
{{
  "tier": "<Strong Candidate | Solid Contender | Potential Match | Requires Review>",
  "verdict": "<Actionable recommendation sentence, e.g. Recommended for Immediate Screening>",
  "color": "<emerald | blue | amber | rose>",
  "summary": "<2-3 sentence executive assessment summarizing qualification fit, core strengths, and primary gap>",
  "verification_checklist": [
    "<Actionable point for interviewer to probe 1>",
    "<Actionable point for interviewer to probe 2>",
    "<Actionable point for interviewer to probe 3>"
  ],
  "key_highlights": [
    "<Highlight 1>",
    "<Highlight 2>",
    "<Highlight 3>"
  ]
}}
"""
        result = self.generate_json(prompt)
        if result and isinstance(result, dict) and "summary" in result and "verification_checklist" in result:
            return result
        return None
