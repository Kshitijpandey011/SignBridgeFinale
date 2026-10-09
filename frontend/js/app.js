/**
 * SIGNBRIDGE Main Application Orchestrator
 * Integrates Camera, Recognition, Translation, TTS, and 3D Avatar subsystems.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Initialize Subsystems
  const statusMgr = new StatusManager();
  const avatarEngine = new AvatarEngine('avatar-canvas');
  const cameraMgr = new CameraManager();
  const translationCtrl = new TranslationController();
  const ttsCtrl = new TTSController();

  // Expose on window for inter-module event communication
  window.SignBridgeApp = {
    status: statusMgr,
    avatar: avatarEngine,
    camera: cameraMgr,
    translation: translationCtrl,
    tts: ttsCtrl,
    mode: "AUTO"
  };

  statusMgr.init();
  avatarEngine.init();
  cameraMgr.init();
  translationCtrl.init();
  ttsCtrl.init();

  // Mode is automatically detected now.
  function setMode(mode) {
    window.SignBridgeApp.mode = mode;
    cameraMgr.setMode(mode);

    // Clear detections for clean transition
    const hudSign = document.getElementById('hud-sign-text');
    if (hudSign) hudSign.textContent = "--";
  }

  window.SignBridgeApp.setMode = setMode;

  // --- Sentence Editing Controls ---
  const englishInput = document.getElementById('english-output');
  const deleteWordBtn = document.getElementById('delete-word-btn');
  const clearSentenceBtn = document.getElementById('clear-sentence-btn');
  const sendToAvatarBtn = document.getElementById('send-to-avatar-btn');
  const refineSentenceBtn = document.getElementById('refine-sentence-btn');

  if (refineSentenceBtn) {
    refineSentenceBtn.addEventListener('click', async () => {
      const text = englishInput ? englishInput.value.trim() : "";
      if (!text) return;
      const origText = refineSentenceBtn.textContent;
      refineSentenceBtn.textContent = "⏳ Refining...";
      refineSentenceBtn.disabled = true;

      try {
        const res = await fetch('/api/ollama/refine', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: text })
        });
        if (res.ok) {
          const data = await res.json();
          if (data.refined_text && englishInput) {
            englishInput.value = data.refined_text;
            translationCtrl.onSentenceUpdated(data.refined_text);
          }
        }
      } catch (e) {
        console.error("Refine error:", e);
      } finally {
        refineSentenceBtn.textContent = origText;
        refineSentenceBtn.disabled = false;
      }
    });
  }

  if (deleteWordBtn) {
    deleteWordBtn.addEventListener('click', async () => {
      try {
        const res = await fetch('/api/sentence/update', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: 'delete_last', mode: window.SignBridgeApp.mode })
        });
        if (res.ok) {
          const data = await res.json();
          if (englishInput) {
            englishInput.value = data.sentence;
            translationCtrl.onSentenceUpdated(data.sentence);
          }
        }
      } catch (e) {
        // Fallback manual word deletion
        if (englishInput) {
          const words = englishInput.value.trim().split(/\s+/);
          words.pop();
          englishInput.value = words.join(" ");
          translationCtrl.onSentenceUpdated(englishInput.value);
        }
      }
    });
  }

  if (clearSentenceBtn) {
    clearSentenceBtn.addEventListener('click', async () => {
      try {
        await fetch('/api/sentence/update', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: 'clear', mode: window.SignBridgeApp.mode })
        });
      } catch (e) { }

      if (englishInput) englishInput.value = "";
      const transOutput = document.getElementById('translation-output');
      if (transOutput) transOutput.value = "";
    });
  }

  if (sendToAvatarBtn) {
    sendToAvatarBtn.addEventListener('click', () => {
      const text = englishInput ? englishInput.value.trim() : "";
      if (text) {
        const avatarInput = document.getElementById('avatar-text-input');
        if (avatarInput) avatarInput.value = text;
        triggerAvatarSign(text);
      }
    });
  }

  // --- 3D Avatar Actions ---
  const avatarSubmitBtn = document.getElementById('avatar-sign-submit-btn');
  const avatarTextInput = document.getElementById('avatar-text-input');
  const avatarPlayBtn = document.getElementById('avatar-play-btn');
  const avatarPauseBtn = document.getElementById('avatar-pause-btn');
  const avatarStopBtn = document.getElementById('avatar-stop-btn');
  const speedSelect = document.getElementById('avatar-speed-select');

  async function triggerAvatarSign(text) {
    if (!text || !text.trim()) return;
    
    const englishBox = document.getElementById('english-output');
    if (englishBox) {
      const words = englishBox.value.trim() ? englishBox.value.trim().split(" ") : [];
      if (words[words.length - 1] !== text) {
          englishBox.value = (englishBox.value.trim() + " " + text).trim();
          if (window.SignBridgeApp.translation) {
              window.SignBridgeApp.translation.onSentenceUpdated(englishBox.value);
          }
      }
    }
    const btn = avatarSubmitBtn;
    if (btn) btn.disabled = true;

    try {
      const res = await fetch('/api/avatar/sign', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: text,
          mode: window.SignBridgeApp.mode
        })
      });

      if (res.ok) {
        const plan = await res.json();
        avatarEngine.playSequence(plan);
      }
    } catch (e) {
      console.error("Avatar plan request failed:", e);
    } finally {
      if (btn) btn.disabled = false;
    }
  }

  window.SignBridgeApp.triggerAvatarSign = triggerAvatarSign;

  if (avatarSubmitBtn) {
    avatarSubmitBtn.addEventListener('click', () => {
      const text = avatarTextInput ? avatarTextInput.value.trim() : "";
      triggerAvatarSign(text);
    });
  }

  if (avatarTextInput) {
    avatarTextInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        triggerAvatarSign(avatarTextInput.value.trim());
      }
    });
  }

  if (avatarPlayBtn) {
    avatarPlayBtn.addEventListener('click', () => {
      if (avatarEngine.isPaused) {
        avatarEngine.resume();
      } else {
        const text = avatarTextInput ? avatarTextInput.value.trim() : "";
        triggerAvatarSign(text);
      }
    });
  }

  if (avatarPauseBtn) avatarPauseBtn.addEventListener('click', () => avatarEngine.pause());
  if (avatarStopBtn) avatarStopBtn.addEventListener('click', () => avatarEngine.stop());

  if (speedSelect) {
    speedSelect.addEventListener('change', (e) => {
      avatarEngine.playbackSpeed = parseFloat(e.target.value) || 1.0;
    });
  }

  // Preset Sign Pills
  document.querySelectorAll('.preset-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      const text = pill.getAttribute('data-text');
      if (avatarTextInput) avatarTextInput.value = text;
      triggerAvatarSign(text);
    });
  });

  // --- Vocabulary Dialog ---
  const vocabModalBtn = document.getElementById('vocab-modal-btn');
  const vocabDialog = document.getElementById('vocab-dialog');
  const closeVocabDialog = document.getElementById('close-vocab-dialog');
  const vocabListContent = document.getElementById('vocab-list-content');
  const vocabDialogTitle = document.getElementById('vocab-dialog-title');

  if (vocabModalBtn && vocabDialog) {
    vocabModalBtn.addEventListener('click', async () => {
      const currentMode = window.SignBridgeApp.mode;
      vocabDialogTitle.textContent = `${currentMode} Sign Vocabulary & Instructions`;
      vocabListContent.innerHTML = '<p style="color: var(--text-dim);">Loading vocabulary...</p>';
      vocabDialog.showModal();

      try {
        const res = await fetch(`/api/supported-signs?mode=${currentMode}`);
        if (res.ok) {
          const data = await res.json();
          let html = `<div style="margin-bottom: 12px; font-size: 0.85rem; color: var(--text-muted);">
            Model Status: <strong style="color: ${data.model_available ? '#34d399' : '#fb7185'}">
            ${data.model_available ? 'Trained & Ready' : 'Model not trained'}</strong> · 
            ${Object.keys(data.signs).length} Signs Available
          </div>`;

          for (const [sign, info] of Object.entries(data.signs)) {
            html += `
              <div style="background: rgba(255,255,255,0.03); padding: 8px 12px; border-radius: var(--radius-sm); border: 1px solid var(--border-subtle); display: flex; justify-content: space-between; align-items: center;">
                <div>
                  <strong style="color: var(--accent-cyan);">${sign}</strong>
                  <span style="font-size: 0.75rem; color: var(--text-dim); margin-left: 6px;">(${info.hands} hand${info.hands > 1 ? 's' : ''}, ${info.type})</span>
                  <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 2px;">${info.description}</div>
                </div>
                <button class="btn btn-outline btn-sm test-sign-btn" data-sign="${sign}">Test on Avatar</button>
              </div>
            `;
          }

          vocabListContent.innerHTML = html;

          vocabListContent.querySelectorAll('.test-sign-btn').forEach(b => {
            b.addEventListener('click', () => {
              const signName = b.getAttribute('data-sign');
              vocabDialog.close();
              if (avatarTextInput) avatarTextInput.value = signName;
              triggerAvatarSign(signName);
            });
          });
        }
      } catch (err) {
        vocabListContent.innerHTML = `<p style="color: #f43f5e;">Failed to load vocabulary: ${err.message}</p>`;
      }
    });
  }

  if (closeVocabDialog && vocabDialog) {
    closeVocabDialog.addEventListener('click', () => vocabDialog.close());
  }

  // --- Keyboard Shortcuts ---
  window.addEventListener('keydown', (e) => {
    // If typing in input or textarea, don't trigger global shortcuts
    if (['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) return;

    if (e.code === 'Space') {
      e.preventDefault();
      cameraMgr.toggleCamera();
    } else if (e.key === 'c' || e.key === 'C') {
      clearSentenceBtn.click();
    } else if (e.key === 's' || e.key === 'S') {
      const speakBtn = document.getElementById('speak-english-btn');
      if (speakBtn) speakBtn.click();
    }
  });

  console.log("SIGNBRIDGE initialized successfully.");
});
