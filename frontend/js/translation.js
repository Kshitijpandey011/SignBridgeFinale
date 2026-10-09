/**
 * SIGNBRIDGE Translation Controller
 * Handles Indian language selection, automatic debounced translation, and caching indicators.
 */

class TranslationController {
  constructor() {
    this.langSelect = document.getElementById('language-select');
    this.englishInput = document.getElementById('english-output');
    this.translationOutput = document.getElementById('translation-output');
    this.sourceTag = document.getElementById('trans-source-tag');
    this.retranslateBtn = document.getElementById('retranslate-btn');
    this.copyBtn = document.getElementById('copy-translation-btn');

    this.debounceTimer = null;
    this.currentText = "";
  }

  init() {
    if (this.langSelect) {
      this.langSelect.addEventListener('change', () => this.translateCurrent());
    }

    if (this.englishInput) {
      this.englishInput.addEventListener('input', () => {
        this.onSentenceUpdated(this.englishInput.value);
      });
    }

    if (this.retranslateBtn) {
      this.retranslateBtn.addEventListener('click', () => this.translateCurrent(true));
    }

    if (this.copyBtn) {
      this.copyBtn.addEventListener('click', () => this.copyTranslation());
    }
  }

  onSentenceUpdated(text) {
    this.currentText = text;
    clearTimeout(this.debounceTimer);
    this.debounceTimer = setTimeout(() => {
      this.translateCurrent();
    }, 450);
  }

  async translateCurrent(force = false) {
    const text = (this.englishInput ? this.englishInput.value : this.currentText).trim();
    if (!text) {
      if (this.translationOutput) this.translationOutput.value = "";
      if (this.sourceTag) this.sourceTag.textContent = "Ready";
      return;
    }

    const targetLang = this.langSelect ? this.langSelect.value : "hi";

    if (this.sourceTag) this.sourceTag.textContent = "Translating...";

    try {
      const res = await fetch('/api/translate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: text,
          target_language: targetLang
        })
      });

      if (res.ok) {
        const data = await res.json();
        if (this.translationOutput) {
          this.translationOutput.value = data.translated_text || "";
        }

        if (this.sourceTag) {
          if (data.source === "ollama") {
            this.sourceTag.className = "pill-badge active-green";
            const latency = data.latency_ms ? ` · ${data.latency_ms}ms` : '';
            this.sourceTag.innerHTML = `🤖 Ollama (${data.model || 'llama3.2:1b'})${latency}`;
          } else if (data.source === "cache") {
            this.sourceTag.className = "pill-badge active-green";
            this.sourceTag.textContent = "⚡ Ollama (Cached)";
          } else if (data.source === "offline_dict" || data.source === "offline_composition") {
            this.sourceTag.className = "pill-badge active-yellow";
            this.sourceTag.textContent = "Fast Dictionary (Fallback)";
          } else {
            this.sourceTag.className = "pill-badge";
            this.sourceTag.textContent = "Direct";
          }
        }
      }
    } catch (e) {
      console.error("Translation failed:", e);
      if (this.sourceTag) {
        this.sourceTag.className = "pill-badge active-red";
        this.sourceTag.textContent = "Error";
      }
    }
  }

  copyTranslation() {
    if (!this.translationOutput || !this.translationOutput.value) return;
    navigator.clipboard.writeText(this.translationOutput.value).then(() => {
      const origText = this.copyBtn.textContent;
      this.copyBtn.textContent = "✓ Copied!";
      setTimeout(() => {
        this.copyBtn.textContent = origText;
      }, 1500);
    });
  }
}

window.TranslationController = TranslationController;
