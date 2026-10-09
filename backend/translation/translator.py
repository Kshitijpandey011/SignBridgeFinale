from typing import Dict, Any, Optional
from backend.config import SUPPORTED_LANGUAGES
from backend.translation.offline_dictionary import get_offline_translation, OFFLINE_DICTIONARY
from backend.ollama.ollama_client import OllamaService

class TranslationManager:
    """
    Unifies Ollama neural translation (primary) and offline dictionary (fallback).
    Prioritizes the local Ollama LLM for natural, contextual translation across all languages.
    """

    def __init__(self, ollama_service: OllamaService):
        self.ollama = ollama_service
        self.languages = SUPPORTED_LANGUAGES

    def get_supported_languages(self) -> Dict[str, Any]:
        return self.languages

    async def translate(self, text: str, target_lang: str) -> Dict[str, Any]:
        """
        Translates English text to the requested Indian language.
        Priority:
        1. If target is English, return original identity.
        2. PRIMARY: Query local Ollama neural LLM (llama3.2:1b).
        3. FALLBACK: If Ollama is offline or fails, use offline sign dictionary.
        """
        cleaned = text.strip()
        if not cleaned:
            return {"translated_text": "", "source": "empty", "lang": target_lang}

        target_lang = target_lang.lower()
        if target_lang not in self.languages:
            return {"translated_text": cleaned, "error": f"Unsupported language: {target_lang}", "source": "error"}

        if target_lang == "en":
            return {"translated_text": cleaned, "source": "identity", "lang": "en"}

        lang_meta = self.languages[target_lang]
        lang_name = lang_meta["name"]

        # Step 1: Exact sign vocabulary match in offline dictionary
        offline_match = get_offline_translation(cleaned, target_lang)
        if offline_match:
            return {
                "translated_text": offline_match,
                "source": "offline_dict",
                "lang": target_lang,
                "lang_name": lang_name
            }

        # Step 2: Telegraphic sign tokens sequence (e.g. HELLO WATER)
        words = cleaned.split()
        if len(words) > 1 and all(get_offline_translation(w, target_lang) for w in words):
            translated_words = [get_offline_translation(w, target_lang) for w in words]
            return {
                "translated_text": " ".join(translated_words),
                "source": "offline_dict",
                "lang": target_lang,
                "lang_name": lang_name
            }

        # Step 3: Local Ollama Neural Translation for fluent natural sentences
        health = await self.ollama.check_health()
        if health.get("running"):
            ollama_res = await self.ollama.translate_text(cleaned, lang_name, target_lang)
            if ollama_res.get("translated_text") and not ollama_res.get("error"):
                return {
                    "translated_text": ollama_res["translated_text"],
                    "source": "ollama",
                    "model": ollama_res.get("model", self.ollama.model),
                    "lang": target_lang,
                    "lang_name": lang_name,
                    "latency_ms": ollama_res.get("latency_ms", 0)
                }

        # Step 4: Fallback to token-by-token composition
        translated_words = []
        all_found = True
        for w in words:
            trans_w = get_offline_translation(w, target_lang)
            if trans_w:
                translated_words.append(trans_w)
            else:
                translated_words.append(w)
                all_found = False

        return {
            "translated_text": " ".join(translated_words) if translated_words else cleaned,
            "source": "offline_composition" if all_found else "partial_fallback",
            "lang": target_lang,
            "lang_name": lang_name,
            "notice": "Ollama offline. Using offline vocabulary fallback."
        }

        return {
            "translated_text": cleaned,
            "source": "fallback",
            "lang": target_lang,
            "lang_name": lang_name
        }
