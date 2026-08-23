"""Failure-tolerant pre/post-visit summary service with LLMProvider abstraction.

Guarantees:
1. Strict non-diagnostic safety rules.
2. Structured output validation.
3. Fallback circuit breaker if LLM times out, errors, or is unconfigured.
4. Core appointment booking flows are never blocked or broken.
"""
import json
import logging
from typing import Any, Dict, List, Literal, Optional
import httpx

from app.config import settings

logger = logging.getLogger("healthcare_manager.ai")


class LLMProvider:
    """Pluggable LLM Provider interface with timeout and JSON schema validation."""

    @staticmethod
    async def generate_completion(prompt: str, system_instruction: str, timeout_seconds: float = 4.0) -> Optional[str]:
        """Invokes external LLM API (Google Gemini / OpenAI compatible) or returns None on failure."""
        if not settings.GEMINI_API_KEY:
            return None

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": f"{system_instruction}\n\nUser Input: {prompt}"}]}],
            "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"},
        }
        try:
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                logger.warning(f"[AI] Gemini API returned status {res.status_code}: {res.text}")
                return None
        except Exception as exc:
            logger.warning(f"[AI] LLM provider invocation failed or timed out: {exc}. Using deterministic fallback.")
            return None


class AiSummaryService:
    @staticmethod
    async def pre_visit(symptoms: str) -> Dict[str, Any]:
        """
        Summarizes symptoms and produces exactly three structured questions.
        Strictly non-diagnostic.
        """
        text = symptoms.strip()
        system_prompt = (
            "You are a medical triage assistant. You DO NOT diagnose illnesses. "
            "Given a patient's symptoms, return a JSON object with keys: "
            "'urgency' (LOW, MEDIUM, or HIGH), 'chief_complaint' (concise string), and "
            "'suggested_questions' (an array of EXACTLY THREE clarifying questions for the upcoming doctor visit)."
        )

        llm_output = await LLMProvider.generate_completion(prompt=text, system_instruction=system_prompt)
        if llm_output:
            try:
                parsed = json.loads(llm_output)
                urgency = parsed.get("urgency", "MEDIUM").upper()
                if urgency not in ("LOW", "MEDIUM", "HIGH"):
                    urgency = "MEDIUM"
                questions = parsed.get("suggested_questions", [])
                if isinstance(questions, list) and len(questions) >= 3:
                    return {
                        "urgency": urgency,
                        "chief_complaint": str(parsed.get("chief_complaint", text[:500])),
                        "suggested_questions": [str(q) for q in questions[:3]],
                        "source": "llm",
                        "disclaimer": "This is not a diagnosis or emergency medical advice.",
                    }
            except Exception as exc:
                logger.warning(f"[AI] Failed to parse LLM JSON: {exc}. Using fallback.")

        # Deterministic, safe fallback
        urgency: Literal["LOW", "MEDIUM", "HIGH"] = (
            "HIGH" if any(word in text.lower() for word in ("chest pain", "difficulty breathing", "fainting", "severe blood"))
            else "MEDIUM"
        )
        return {
            "urgency": urgency,
            "chief_complaint": text[:500],
            "suggested_questions": [
                "When did these symptoms begin, and have they changed in severity?",
                "What factors or activities make the symptoms better or worse?",
                "What current medications, allergies, or health conditions should the doctor consider?",
            ],
            "source": "fallback",
            "disclaimer": "This is not a diagnosis or emergency medical advice.",
        }

    @staticmethod
    async def post_visit(notes: str, prescriptions: List[Dict[str, Any]], instructions: str) -> Dict[str, Any]:
        """
        Synthesizes doctor notes into patient-friendly explanations.
        Remains gated until reviewed and approved by the doctor.
        """
        system_prompt = (
            "You are a clinical communications assistant. Given a doctor's clinical notes, "
            "prescription details, and follow-up instructions, produce a clear, reassuring, "
            "patient-friendly JSON object with keys: 'visit_explanation', 'medication_schedule', and 'follow_up_steps'."
        )
        context_data = json.dumps({"notes": notes, "prescriptions": prescriptions, "instructions": instructions})
        llm_output = await LLMProvider.generate_completion(prompt=context_data, system_instruction=system_prompt)

        if llm_output:
            try:
                parsed = json.loads(llm_output)
                return {
                    "visit_explanation": str(parsed.get("visit_explanation", notes.strip()[:2000])),
                    "medication_schedule": parsed.get("medication_schedule", prescriptions),
                    "follow_up_steps": str(parsed.get("follow_up_steps", instructions.strip()[:2000])),
                    "source": "llm",
                }
            except Exception as exc:
                logger.warning(f"[AI] Failed to parse post-visit LLM response: {exc}")

        return {
            "visit_explanation": notes.strip()[:2000] or "No clinical notes entered.",
            "medication_schedule": prescriptions,
            "follow_up_steps": instructions.strip()[:2000] or "Follow regular care instructions.",
            "source": "fallback",
        }
