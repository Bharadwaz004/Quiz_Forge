"""
Quiz Generator Service — Qwen2.5-3B-Instruct with DEBUG prints
===============================================================
Uses HuggingFace transformers with Qwen2.5's native chat template.
Qwen2.5-Instruct uses ChatML format and is excellent at structured JSON output.
"""

import json
import re
import time
import traceback
from typing import List, Dict, Optional

from app.core.config import settings
from app.services.vector_store import VectorStoreService

MAX_GENERATION_RETRIES = 2


def _build_messages(context: str, topic: str, num_questions: int = 3) -> List[Dict]:
    """
    Build chat messages for Qwen2.5-Instruct.
    Uses the model's native chat format via tokenizer.apply_chat_template.
    """
    # Keep context manageable for CPU inference speed
    if len(context) > 1500:
        context = context[:1500]

    system_msg = (
        "You are a quiz generator. You MUST respond with ONLY valid JSON, no other text. "
        "Generate questions ONLY from the provided context. Never use outside knowledge."
    )

    user_msg = f"""Create exactly {num_questions} multiple-choice quiz questions about "{topic}" using ONLY this context:

---
{context}
---

Respond with ONLY this JSON format, nothing else:
{{"questions": [{{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "answer": "A) ..."}}]}}"""

    return [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]


def _extract_json(text: str) -> Optional[Dict]:
    """Robustly extract JSON from LLM output."""
    print(f"[DEBUG _extract_json] Input length: {len(text) if text else 0}")
    print(f"[DEBUG _extract_json] First 500 chars:\n{repr(text[:500]) if text else 'EMPTY'}")

    if not text or not text.strip():
        print("[DEBUG _extract_json] FAIL: text is empty")
        return None

    if "INSUFFICIENT_CONTEXT" in text.upper():
        print("[DEBUG _extract_json] Found INSUFFICIENT_CONTEXT signal")
        return None

    # Try direct parse
    try:
        result = json.loads(text.strip())
        print(f"[DEBUG _extract_json] SUCCESS: direct parse")
        return result
    except json.JSONDecodeError as e:
        print(f"[DEBUG _extract_json] Direct parse failed: {e}")

    # Strip markdown code fences
    cleaned = re.sub(r"```(?:json)?\s*", "", text)
    cleaned = re.sub(r"```\s*$", "", cleaned)
    try:
        result = json.loads(cleaned.strip())
        print(f"[DEBUG _extract_json] SUCCESS: markdown-stripped parse")
        return result
    except json.JSONDecodeError as e:
        print(f"[DEBUG _extract_json] Markdown-stripped parse failed: {e}")

    # Find JSON object via regex
    match = re.search(r'\{[\s\S]*"questions"\s*:\s*\[[\s\S]*\]\s*\}', text)
    if match:
        print(f"[DEBUG _extract_json] Regex match found, length={len(match.group())}")
        try:
            result = json.loads(match.group())
            print(f"[DEBUG _extract_json] SUCCESS: regex extraction")
            return result
        except json.JSONDecodeError as e:
            print(f"[DEBUG _extract_json] Regex match parse failed: {e}")
    else:
        print("[DEBUG _extract_json] No regex match for 'questions' pattern")

    # Last resort: first { to last }
    first = text.find("{")
    last = text.rfind("}")
    print(f"[DEBUG _extract_json] Brace positions: first={first}, last={last}")
    if first != -1 and last > first:
        snippet = text[first : last + 1]
        print(f"[DEBUG _extract_json] Brace snippet:\n{snippet[:500]}")
        try:
            result = json.loads(snippet)
            print(f"[DEBUG _extract_json] SUCCESS: brace extraction")
            return result
        except json.JSONDecodeError as e:
            print(f"[DEBUG _extract_json] Brace extraction failed: {e}")

    print("[DEBUG _extract_json] ALL EXTRACTION METHODS FAILED")
    print(f"[DEBUG _extract_json] FULL RAW TEXT:\n{text}\n--- END ---")
    return None


def _validate_quiz(data: Dict) -> Optional[List[Dict]]:
    """Validate quiz JSON structure."""
    print(f"[DEBUG _validate_quiz] Input type: {type(data)}")

    if not isinstance(data, dict):
        print(f"[DEBUG _validate_quiz] FAIL: not a dict")
        return None

    if "questions" not in data:
        print(f"[DEBUG _validate_quiz] FAIL: no 'questions' key. Keys: {list(data.keys())}")
        return None

    questions = data["questions"]
    print(f"[DEBUG _validate_quiz] questions count: {len(questions) if isinstance(questions, list) else 'NOT A LIST'}")

    if not isinstance(questions, list) or len(questions) == 0:
        print("[DEBUG _validate_quiz] FAIL: not a list or empty")
        return None

    validated = []
    for i, q in enumerate(questions):
        if not isinstance(q, dict):
            print(f"  Q{i} SKIP: not a dict")
            continue

        missing = [k for k in ["question", "options", "answer"] if k not in q]
        if missing:
            print(f"  Q{i} SKIP: missing {missing}")
            continue

        if not isinstance(q["options"], list):
            print(f"  Q{i} SKIP: options is {type(q['options'])}")
            continue

        if len(q["options"]) != 4:
            print(f"  Q{i} SKIP: {len(q['options'])} options instead of 4")
            continue

        if not q["question"].strip() or not q["answer"].strip():
            print(f"  Q{i} SKIP: empty question or answer")
            continue

        print(f"  Q{i} PASS: '{q['question'][:60]}...'")
        validated.append({
            "question": q["question"].strip(),
            "options": [opt.strip() for opt in q["options"]],
            "answer": q["answer"].strip(),
        })

    print(f"[DEBUG _validate_quiz] Result: {len(validated)}/{len(questions)} valid")
    return validated if validated else None


class QuizGenerator:
    """Generates quizzes using Qwen2.5-3B-Instruct via HuggingFace transformers."""

    def __init__(self):
        self._model = None
        self._tokenizer = None
        print(f"[DEBUG QuizGenerator.__init__] Created (model will lazy-load)")

    def _load_model(self):
        """Lazy-load the model and tokenizer."""
        if self._model is not None:
            return

        print(f"\n[DEBUG _load_model] Loading: {settings.LLM_MODEL}")
        print(f"[DEBUG _load_model] Device: {settings.LLM_DEVICE}")
        print(f"[DEBUG _load_model] Max new tokens: {settings.LLM_MAX_NEW_TOKENS}")

        t0 = time.time()

        from transformers import AutoModelForCausalLM, AutoTokenizer

        print(f"[DEBUG _load_model] Loading tokenizer...")
        self._tokenizer = AutoTokenizer.from_pretrained(
            settings.LLM_MODEL,
            trust_remote_code=True,
        )
        print(f"[DEBUG _load_model] Tokenizer loaded")

        print(f"[DEBUG _load_model] Loading model (this downloads ~6GB first time)...")
        self._model = AutoModelForCausalLM.from_pretrained(
            settings.LLM_MODEL,
            torch_dtype="auto",
            device_map=settings.LLM_DEVICE,
            trust_remote_code=True,
        )
        self._model.eval()

        elapsed = time.time() - t0
        print(f"[DEBUG _load_model] Model loaded in {elapsed:.1f}s")

    def _generate(self, messages: List[Dict]) -> str:
        """Generate text using Qwen2.5's native chat template."""
        self._load_model()

        print(f"[DEBUG _generate] Applying chat template...")
        text = self._tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        print(f"[DEBUG _generate] Formatted prompt ({len(text)} chars):")
        print(f"{text[:400]}...")

        print(f"[DEBUG _generate] Tokenizing...")
        inputs = self._tokenizer([text], return_tensors="pt").to(self._model.device)
        input_len = inputs["input_ids"].shape[1]
        print(f"[DEBUG _generate] Input tokens: {input_len}")

        print(f"[DEBUG _generate] Generating (max_new_tokens={settings.LLM_MAX_NEW_TOKENS})...")
        t0 = time.time()

        import torch
        with torch.no_grad():
            output_ids = self._model.generate(
                **inputs,
                max_new_tokens=settings.LLM_MAX_NEW_TOKENS,
                temperature=settings.LLM_TEMPERATURE,
                do_sample=True,
                top_p=0.9,
                repetition_penalty=1.1,
            )

        elapsed = time.time() - t0
        new_tokens = output_ids.shape[1] - input_len
        tps = new_tokens / elapsed if elapsed > 0 else 0
        print(f"[DEBUG _generate] Generated {new_tokens} tokens in {elapsed:.1f}s ({tps:.1f} tok/s)")

        # Decode only the new tokens
        response = self._tokenizer.decode(
            output_ids[0][input_len:],
            skip_special_tokens=True,
        )
        print(f"[DEBUG _generate] Decoded response ({len(response)} chars)")
        return response

    def generate_quiz(
        self,
        session_id: str,
        topic: str,
        num_questions: int = 5,
    ) -> Dict:
        print(f"\n{'='*60}")
        print(f"[DEBUG generate_quiz] START")
        print(f"[DEBUG generate_quiz] session={session_id}, topic='{topic}', n={num_questions}")
        print(f"{'='*60}")

        # --- Step 1: Retrieve context ---
        print(f"\n[DEBUG generate_quiz] STEP 1: Retrieving context...")
        vs = VectorStoreService.get_instance()
        chunks, distances = vs.retrieve_context(session_id, topic)

        print(f"[DEBUG generate_quiz] Chunks: {len(chunks)}, Distances: {[round(d, 3) for d in distances]}")

        if not chunks:
            print(f"[DEBUG generate_quiz] NO CHUNKS — returning INSUFFICIENT_CONTEXT")
            return {
                "status": "INSUFFICIENT_CONTEXT",
                "message": "No relevant content found in the uploaded document for this topic.",
                "questions": [],
                "source_chunks_used": 0,
            }

        for i, chunk in enumerate(chunks):
            print(f"[DEBUG generate_quiz] Chunk {i} ({len(chunk)} chars): {chunk[:80]}...")

        context = "\n\n---\n\n".join(chunks)

        # Cap at 3 questions for CPU speed — Qwen2.5-3B can do it well
        actual_num = min(num_questions, 3)
        print(f"[DEBUG generate_quiz] Requesting {actual_num} questions (capped from {num_questions} for CPU speed)")

        # --- Step 2: Build messages ---
        messages = _build_messages(context, topic, actual_num)
        print(f"[DEBUG generate_quiz] Messages built: {len(messages)} messages")

        # --- Step 3: Generate with retries ---
        for attempt in range(1, MAX_GENERATION_RETRIES + 1):
            print(f"\n[DEBUG generate_quiz] ===== ATTEMPT {attempt}/{MAX_GENERATION_RETRIES} =====")

            try:
                raw_text = self._generate(messages)
                print(f"\n[DEBUG generate_quiz] === RAW LLM OUTPUT START ===")
                print(raw_text)
                print(f"[DEBUG generate_quiz] === RAW LLM OUTPUT END ===\n")

                if "INSUFFICIENT_CONTEXT" in raw_text.upper():
                    print(f"[DEBUG generate_quiz] LLM said INSUFFICIENT_CONTEXT")
                    return {
                        "status": "INSUFFICIENT_CONTEXT",
                        "message": "The LLM determined there is not enough context.",
                        "questions": [],
                        "source_chunks_used": len(chunks),
                    }

                print(f"[DEBUG generate_quiz] Extracting JSON...")
                parsed = _extract_json(raw_text)
                if parsed is None:
                    print(f"[DEBUG generate_quiz] JSON extraction FAILED — will retry")
                    continue

                print(f"[DEBUG generate_quiz] Validating quiz...")
                validated = _validate_quiz(parsed)
                if validated is None:
                    print(f"[DEBUG generate_quiz] Validation FAILED — will retry")
                    continue

                validated = validated[:num_questions]
                print(f"\n[DEBUG generate_quiz] SUCCESS! {len(validated)} questions")
                return {
                    "status": "success",
                    "questions": validated,
                    "source_chunks_used": len(chunks),
                }

            except Exception as e:
                print(f"[DEBUG generate_quiz] EXCEPTION: {type(e).__name__}: {e}")
                traceback.print_exc()
                continue

        print(f"\n[DEBUG generate_quiz] ALL RETRIES EXHAUSTED — using fallback")
        return self._fallback_questions(chunks, topic)

    def _fallback_questions(self, chunks: List[str], topic: str) -> Dict:
        """Fallback: generate questions directly from chunks without LLM."""
        print(f"[DEBUG _fallback_questions] Building from {len(chunks)} chunks")
        questions = []
        for i, chunk in enumerate(chunks[:5]):
            sentences = [s.strip() for s in chunk.split(".") if len(s.strip()) > 20]
            if sentences:
                stmt = sentences[0]
                questions.append({
                    "question": f"Based on the document, is this statement about {topic} correct? \"{stmt}.\"",
                    "options": [
                        "A) True - this is stated in the document",
                        "B) False - this is not in the document",
                        "C) Partially true - some details differ",
                        "D) Cannot be determined from the document",
                    ],
                    "answer": "A) True - this is stated in the document",
                })

        print(f"[DEBUG _fallback_questions] Generated {len(questions)} fallback questions")

        if not questions:
            return {
                "status": "INSUFFICIENT_CONTEXT",
                "message": "Could not generate quiz questions after multiple attempts.",
                "questions": [],
                "source_chunks_used": len(chunks),
            }

        return {
            "status": "success",
            "questions": questions,
            "source_chunks_used": len(chunks),
            "note": "Generated using fallback method.",
        }


# Module-level singleton
_generator: Optional[QuizGenerator] = None


def get_quiz_generator() -> QuizGenerator:
    global _generator
    if _generator is None:
        print("[DEBUG get_quiz_generator] Creating QuizGenerator...")
        _generator = QuizGenerator()
    return _generator