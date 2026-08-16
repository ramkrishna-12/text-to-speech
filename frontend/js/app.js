// Point this at your deployed backend. Left relative ("") assumes frontend and API
// share an origin (e.g. served behind the same ALB path routing). Override for local dev
// or cross-origin deployments, e.g. "https://api.yourdomain.com".
const API_BASE = window.TTS_API_BASE || "";

const els = {
  text: document.getElementById("text-input"),
  charCount: document.getElementById("char-count"),
  voiceSelect: document.getElementById("voice-select"),
  previewBtn: document.getElementById("preview-btn"),
  convertBtn: document.getElementById("convert-btn"),
  status: document.getElementById("status"),
  playerWrap: document.getElementById("player-wrap"),
  audioPlayer: document.getElementById("audio-player"),
  downloadLink: document.getElementById("download-link"),
  apiStatus: document.getElementById("api-status"),
};

// Cache the last generated audio so Preview -> Save doesn't re-hit the API unnecessarily
let lastRequestKey = null;
let lastResult = null;

init();

async function init() {
  els.text.addEventListener("input", () => {
    els.charCount.textContent = els.text.value.length;
  });

  els.previewBtn.addEventListener("click", () => handleGenerate({ autoplay: true }));
  els.convertBtn.addEventListener("click", () => handleGenerate({ autoplay: false }));

  await Promise.all([loadVoices(), checkHealth()]);
}

async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error();
    els.apiStatus.textContent = "API connected";
  } catch {
    els.apiStatus.textContent = "⚠ API unreachable";
  }
}

async function loadVoices() {
  try {
    const res = await fetch(`${API_BASE}/voices`);
    if (!res.ok) throw new Error("Failed to load voices");
    const voices = await res.json();

    els.voiceSelect.innerHTML = "";
    for (const v of voices) {
      const opt = document.createElement("option");
      opt.value = v.id;
      opt.textContent = v.label;
      els.voiceSelect.appendChild(opt);
    }
  } catch (err) {
    setStatus("Could not load voice list from the API.", "error");
  }
}

function setStatus(message, kind = "") {
  els.status.textContent = message;
  els.status.className = "status" + (kind ? ` status--${kind}` : "");
}

function requestKey(text, voiceId) {
  return `${voiceId}::${text}`;
}

async function handleGenerate({ autoplay }) {
  const text = els.text.value.trim();
  const voiceId = els.voiceSelect.value;

  if (!text) {
    setStatus("Please enter some text first.", "error");
    return;
  }

  const key = requestKey(text, voiceId);
  toggleButtons(true);

  try {
    let result = lastResult;
    if (key !== lastRequestKey) {
      setStatus("Generating audio…");
      const res = await fetch(`${API_BASE}/convert`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, voice_id: voiceId }),
      });

      if (!res.ok) {
        const err = await safeJson(res);
        throw new Error(err?.detail || `Request failed (${res.status})`);
      }

      result = await res.json();
      lastResult = result;
      lastRequestKey = key;
    }

    els.audioPlayer.src = `${API_BASE}${result.preview_url}`;
    els.downloadLink.href = `${API_BASE}${result.download_url}`;
    els.downloadLink.setAttribute("download", `speech-${result.audio_id}.mp3`);
    els.playerWrap.classList.remove("hidden");

    if (autoplay) {
      els.audioPlayer.play().catch(() => {
        /* autoplay can be blocked by the browser; user can hit play manually */
      });
      setStatus("Preview ready.", "success");
    } else {
      setStatus("Ready — click Save to download the .mp3.", "success");
    }
  } catch (err) {
    setStatus(err.message || "Something went wrong.", "error");
  } finally {
    toggleButtons(false);
  }
}

async function safeJson(res) {
  try {
    return await res.json();
  } catch {
    return null;
  }
}

function toggleButtons(disabled) {
  els.previewBtn.disabled = disabled;
  els.convertBtn.disabled = disabled;
}
