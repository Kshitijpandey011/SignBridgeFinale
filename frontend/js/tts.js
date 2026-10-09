/**
 * SIGNBRIDGE Text-To-Speech (TTS) Controller
 * Uses Browser Web Speech API for low-latency native voice synthesis with backend pyttsx3 fallback.
 */

class TTSController {
  constructor() {
    this.speakEnglishBtn = document.getElementById('speak-english-btn');
    this.speakTranslationBtn = document.getElementById('speak-translation-btn');
    this.englishInput = document.getElementById('english-output');
    this.translationOutput = document.getElementById('translation-output');
    this.langSelect = document.getElementById('language-select');

    this.synth = window.speechSynthesis;
    this.voices = [];
    this.langCodeMap = {
      "en": "en-US",
      "hi": "hi-IN",
      "ta": "ta-IN",
      "te": "te-IN",
      "kn": "kn-IN",
      "ml": "ml-IN",
      "mr": "mr-IN",
      "bn": "bn-IN",
      "gu": "gu-IN",
      "pa": "pa-IN",
      "ur": "ur-PK",
      "or": "or-IN",
      "as": "as-IN"
    };

    if (this.synth) {
      this.synth.onvoiceschanged = () => {
        this.voices = this.synth.getVoices();
      };
      this.voices = this.synth.getVoices();
    }
  }

  init() {
    if (this.speakEnglishBtn) {
      this.speakEnglishBtn.addEventListener('click', () => {
        const text = this.englishInput ? this.englishInput.value.trim() : "";
        if (text) {
          this.speak(text, "en-US", this.speakEnglishBtn);
        }
      });
    }

    if (this.speakTranslationBtn) {
      this.speakTranslationBtn.addEventListener('click', () => {
        const text = this.translationOutput ? this.translationOutput.value.trim() : "";
        const langKey = this.langSelect ? this.langSelect.value : "hi";
        const langCode = this.langCodeMap[langKey] || "hi-IN";
        if (text) {
          this.speak(text, langCode, this.speakTranslationBtn);
        }
      });
    }
  }

  speak(text, langCode, buttonEl) {
    if (!text) return;

    if (this.synth) {
      // Cancel any ongoing speech
      this.synth.cancel();

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = langCode;
      utterance.rate = 0.95;

      // Find matching voice if available
      const matchingVoice = this.voices.find(v => v.lang === langCode || v.lang.startsWith(langCode.split('-')[0]));
      if (matchingVoice) {
        utterance.voice = matchingVoice;
      }

      if (buttonEl) {
        const originalText = buttonEl.textContent;
        buttonEl.textContent = "🔊 Speaking...";
        utterance.onend = () => { buttonEl.textContent = originalText; };
        utterance.onerror = () => { buttonEl.textContent = originalText; };
      }

      this.synth.speak(utterance);
    } else {
      // Fallback to backend pyttsx3
      fetch('/api/speak', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: text,
          language_code: langCode
        })
      });
    }
  }
}

window.TTSController = TTSController;
