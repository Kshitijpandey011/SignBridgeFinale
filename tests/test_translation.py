import pytest
from backend.translation.translator import TranslationManager
from backend.ollama.ollama_client import OllamaService
from backend.translation.offline_dictionary import OFFLINE_DICTIONARY

@pytest.mark.asyncio
async def test_offline_dictionary_coverage():
    ollama_svc = OllamaService()
    translator = TranslationManager(ollama_svc)

    # Test exact word lookup
    res_hi = await translator.translate("HELLO", "hi")
    assert res_hi["translated_text"] == "नमस्ते"
    assert res_hi["source"] == "offline_dict"

    res_ta = await translator.translate("THANK_YOU", "ta")
    assert res_ta["translated_text"] == "நன்றி"

    res_te = await translator.translate("WATER", "te")
    assert res_te["translated_text"] == "నీరు"

    # Test English identity
    res_en = await translator.translate("HELLO HOW ARE YOU", "en")
    assert res_en["translated_text"] == "HELLO HOW ARE YOU"
    assert res_en["source"] == "identity"

@pytest.mark.asyncio
async def test_offline_composition_fallback():
    ollama_svc = OllamaService()
    translator = TranslationManager(ollama_svc)

    res = await translator.translate("HELLO WATER", "hi")
    assert "नमस्ते" in res["translated_text"]
    assert "पानी" in res["translated_text"]
