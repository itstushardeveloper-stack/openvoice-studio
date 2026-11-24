/**
 * Chatterbox Voice Studio Client Application
 */

const state = {
  serverUrl: localStorage.getItem("chatterbox_server_url") || window.location.origin,
  apiKey: localStorage.getItem("chatterbox_api_key") || "",
  supportedLanguages: {},
  profiles: [],
  currentAudioUrl: null,
};

// Preset Scripts
const PRESETS = {
  "hindi-yt": {
    title: "Hindi AI Revolution",
    lang: "hi",
    text: `नमस्ते दोस्तों! आर्टिफिशियल इंटेलिजेंस की दुनिया में आपका स्वागत है।
आज हम जानेंगे कि कैसे मॉडर्न AI हमारी ज़िंदगी को हमेशा के लिए बदल रहा है।
वीडियो को अंत तक ज़रूर देखें और चैनल को सब्सक्राइब करना न भूलें!`,
  },
  "english-doc": {
    title: "Cosmos Documentary",
    lang: "en",
    text: `Deep within the silent expanse of the universe, billions of galaxies dance across cosmic time.
Every star you see tonight is a quiet witness to the origin of matter, energy, and life itself.`,
  },
  "shorts": {
    title: "3 Productivity Tips",
    lang: "en",
    text: `Stop wasting your mornings! Here are three habits that will double your focus in thirty days.
Number one: never check your phone within the first thirty minutes. Save this Reel and start tomorrow!`,
  },
};

// Elements
const scriptInput = document.getElementById("scriptInput");
const charCount = document.getElementById("charCount");
const wordCount = document.getElementById("wordCount");
const estDuration = document.getElementById("estDuration");
const languageSelect = document.getElementById("languageSelect");
const allLanguagesGroup = document.getElementById("allLanguagesGroup");
const voiceProfileSelect = document.getElementById("voiceProfileSelect");
const profileDescription = document.getElementById("profileDescription");
const exaggerationRange = document.getElementById("exaggerationRange");
const exaggVal = document.getElementById("exaggVal");
const cfgRange = document.getElementById("cfgRange");
const cfgVal = document.getElementById("cfgVal");
const synthesizeBtn = document.getElementById("synthesizeBtn");
const synthesizeBtnText = document.getElementById("synthesizeBtnText");
const statusDot = document.getElementById("statusDot");
const statusText = document.getElementById("statusText");
const deviceTag = document.getElementById("deviceTag");
const languageWarningBox = document.getElementById("languageWarningBox");
const languageWarningText = document.getElementById("languageWarningText");
const scriptTitle = document.getElementById("scriptTitle");
const audioElement = document.getElementById("audioElement");
const downloadWavBtn = document.getElementById("downloadWavBtn");
const generationMeta = document.getElementById("generationMeta");
const waveformCanvas = document.getElementById("waveformCanvas");
const waveformPlaceholder = document.getElementById("waveformPlaceholder");

// Sliders live feedback
exaggerationRange.addEventListener("input", (e) => {
  exaggVal.textContent = e.target.value;
});

cfgRange.addEventListener("input", (e) => {
  cfgVal.textContent = e.target.value;
});

// Live Script Stats Calculation
function updateScriptStats() {
  const text = scriptInput.value || "";
  charCount.textContent = text.length;
  const words = text.trim() ? text.trim().split(/\s+/).length : 0;
  wordCount.textContent = words;
  const durationSec = Math.round(words / 2.3);
  estDuration.textContent = `${durationSec}s`;

  // Check language compatibility dynamically
  checkLanguageLive(text, languageSelect.value);
}

scriptInput.addEventListener("input", updateScriptStats);

// Preset Buttons
document.querySelectorAll(".template-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    const format = btn.dataset.format;
    const preset = PRESETS[format];
    if (preset) {
      scriptInput.value = preset.text;
      scriptTitle.value = preset.title;
      languageSelect.value = preset.lang;
      updateScriptStats();
    }
  });
});

document.getElementById("clearScriptBtn").addEventListener("click", () => {
  scriptInput.value = "";
  updateScriptStats();
});

// Live Language Checking
function checkLanguageLive(text, selectedLang) {
  if (selectedLang === "gu") {
    languageWarningBox.classList.remove("hidden");
    languageWarningText.innerHTML = `<strong>Language Limitation:</strong> Gujarati (gu) is currently <strong>not supported</strong> for voice synthesis by Chatterbox Multilingual V3 (which supports 23 languages including Hindi & English). The script will be saved, but audio generation will be safely bypassed.`;
    return;
  }

  // Gujarati Unicode characters detected in text
  if (/[\u0A80-\u0AFF]/.test(text)) {
    languageWarningBox.classList.remove("hidden");
    languageWarningText.innerHTML = `<strong>Gujarati Script Detected:</strong> Chatterbox Multilingual V3 does not yet support Gujarati audio synthesis. The script will be preserved in Gujarati script, but audio generation is not available.`;
    return;
  }

  languageWarningBox.classList.add("hidden");
}

languageSelect.addEventListener("change", () => {
  updateScriptStats();
});

// API Helper
async function apiCall(endpoint, options = {}) {
  const url = `${state.serverUrl.replace(/\/$/, "")}${endpoint}`;
  const headers = options.headers || {};
  if (state.apiKey) {
    headers["X-API-Key"] = state.apiKey;
  }
  options.headers = headers;

  const res = await fetch(url, options);
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || `HTTP Error ${res.status}`);
  }
  return res.json();
}

// Fetch Server Status
async function checkServerHealth() {
  try {
    const data = await apiCall("/health");
    statusDot.className = "w-2 h-2 rounded-full bg-emerald-400";
    statusText.textContent = data.mock_inference ? "Online (Mock Mode)" : "Online";
    deviceTag.textContent = (data.device || "cpu").toUpperCase();
  } catch (err) {
    statusDot.className = "w-2 h-2 rounded-full bg-rose-500";
    statusText.textContent = "Offline / Error";
    deviceTag.textContent = "--";
  }
}

// Load Languages and Profiles
async function loadInitialData() {
  await checkServerHealth();

  try {
    const langData = await apiCall("/v1/languages");
    state.supportedLanguages = langData.supported_languages || {};
    allLanguagesGroup.innerHTML = "";
    for (const [code, name] of Object.entries(state.supportedLanguages)) {
      if (code !== "hi" && code !== "en") {
        const opt = document.createElement("option");
        opt.value = code;
        opt.textContent = `${name} (${code})`;
        allLanguagesGroup.appendChild(opt);
      }
    }
  } catch (e) {
    console.warn("Could not load languages list:", e);
  }

  try {
    const profData = await apiCall("/v1/voices/profiles");
    state.profiles = profData.profiles || [];
    voiceProfileSelect.innerHTML = "";
    state.profiles.forEach((p) => {
      const opt = document.createElement("option");
      opt.value = p.name;
      opt.textContent = `${p.name} (${p.gender} - ${p.language_tag})`;
      voiceProfileSelect.appendChild(opt);
    });
    updateProfileDesc();
  } catch (e) {
    console.warn("Could not load profiles:", e);
  }
}

function updateProfileDesc() {
  const selected = voiceProfileSelect.value;
  const prof = state.profiles.find((p) => p.name === selected);
  if (prof) {
    profileDescription.textContent = prof.description || "";
  }
}
voiceProfileSelect.addEventListener("change", updateProfileDesc);

// Synthesis Handler
synthesizeBtn.addEventListener("click", async () => {
  const text = scriptInput.value.trim();
  if (!text) {
    alert("Please enter a script or narration text.");
    return;
  }

  synthesizeBtn.disabled = true;
  synthesizeBtnText.textContent = "Synthesizing Speech...";
  synthesizeBtn.classList.add("opacity-75");

  try {
    const selectedLang = languageSelect.value === "auto" ? null : languageSelect.value;
    const payload = {
      text: text,
      language_id: selectedLang,
      voice_profile: voiceProfileSelect.value,
      exaggeration: parseFloat(exaggerationRange.value),
      cfg_weight: parseFloat(cfgRange.value),
      title: scriptTitle.value || "narration",
    };

    const res = await apiCall("/v1/tts/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (res.audio_url) {
      const fullAudioUrl = `${state.serverUrl.replace(/\/$/, "")}${res.audio_url}`;
      audioElement.src = fullAudioUrl;
      downloadWavBtn.href = fullAudioUrl;
      downloadWavBtn.classList.remove("opacity-50", "pointer-events-none");
      generationMeta.textContent = `${res.language_name} • ${res.duration_seconds}s`;
      waveformPlaceholder.classList.add("hidden");
      drawMockWaveform();
      audioElement.play().catch(() => {});
    } else {
      alert(`Script preserved: ${res.message}`);
    }
  } catch (err) {
    alert(`Synthesis failed: ${err.message}`);
  } finally {
    synthesizeBtn.disabled = false;
    synthesizeBtnText.textContent = "Generate Voice-Over (WAV)";
    synthesizeBtn.classList.remove("opacity-75");
  }
});

function drawMockWaveform() {
  const ctx = waveformCanvas.getContext("2d");
  const width = (waveformCanvas.width = waveformCanvas.offsetWidth);
  const height = (waveformCanvas.height = waveformCanvas.offsetHeight);

  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#8b5cf6";
  const numBars = 45;
  const barWidth = width / numBars - 2;

  for (let i = 0; i < numBars; i++) {
    const h = Math.random() * (height * 0.8) + height * 0.1;
    const x = i * (barWidth + 2);
    const y = (height - h) / 2;
    ctx.fillRect(x, y, barWidth, h);
  }
}

// Clone Voice Modal
const cloneModal = document.getElementById("cloneModal");
document.getElementById("toggleCloneModalBtn").addEventListener("click", () => {
  cloneModal.classList.remove("hidden");
});
document.getElementById("closeCloneModalBtn").addEventListener("click", () => {
  cloneModal.classList.add("hidden");
});
document.getElementById("cancelCloneBtn").addEventListener("click", () => {
  cloneModal.classList.add("hidden");
});

document.getElementById("submitCloneBtn").addEventListener("click", async () => {
  const name = document.getElementById("cloneName").value.trim();
  const file = document.getElementById("cloneAudioFile").files[0];
  const authorized = document.getElementById("cloneAuthCheck").checked;

  if (!name || !file) {
    alert("Please provide both a profile name and a reference audio file.");
    return;
  }

  if (!authorized) {
    alert("You must affirm and certify voice authorization before cloning a voice.");
    return;
  }

  const formData = new FormData();
  formData.append("name", name);
  formData.append("file", file);
  formData.append("authorized", "true");
  formData.append("gender", document.getElementById("cloneGender").value);
  formData.append("language_tag", document.getElementById("cloneLang").value);

  try {
    const res = await apiCall("/v1/voices/clone", {
      method: "POST",
      body: formData,
    });
    alert(`Successfully cloned voice profile: ${res.profile.name}`);
    cloneModal.classList.add("hidden");
    loadInitialData();
  } catch (err) {
    alert(`Voice clone error: ${err.message}`);
  }
});

// Settings Modal
const settingsModal = document.getElementById("settingsModal");
document.getElementById("openSettingsBtn").addEventListener("click", () => {
  document.getElementById("settingsServerUrl").value = state.serverUrl;
  document.getElementById("settingsApiKey").value = state.apiKey;
  settingsModal.classList.remove("hidden");
});
document.getElementById("closeSettingsModalBtn").addEventListener("click", () => {
  settingsModal.classList.add("hidden");
});
document.getElementById("saveSettingsBtn").addEventListener("click", () => {
  state.serverUrl = document.getElementById("settingsServerUrl").value.trim() || window.location.origin;
  state.apiKey = document.getElementById("settingsApiKey").value.trim();
  localStorage.setItem("chatterbox_server_url", state.serverUrl);
  localStorage.setItem("chatterbox_api_key", state.apiKey);
  settingsModal.classList.add("hidden");
  loadInitialData();
});

document.getElementById("testConnectionBtn").addEventListener("click", async () => {
  const resultDiv = document.getElementById("testConnectionResult");
  resultDiv.textContent = "Testing connection...";
  resultDiv.className = "text-xs text-slate-400";
  try {
    const testUrl = document.getElementById("settingsServerUrl").value.trim() || window.location.origin;
    const res = await fetch(`${testUrl.replace(/\/$/, "")}/health`);
    if (res.ok) {
      resultDiv.textContent = "✓ Connected successfully!";
      resultDiv.className = "text-xs text-emerald-400 font-medium";
    } else {
      resultDiv.textContent = `✗ Server responded with ${res.status}`;
      resultDiv.className = "text-xs text-rose-400";
    }
  } catch (e) {
    resultDiv.textContent = `✗ Connection failed: ${e.message}`;
    resultDiv.className = "text-xs text-rose-400";
  }
});

// Initialize
loadInitialData();
