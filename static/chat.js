(function () {
  const chat = document.getElementById("chat");
  if (!chat) return;

  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const sendBtn = document.getElementById("send-btn");
  const messages = document.getElementById("messages");
  const typing = document.getElementById("typing");
  const errorBox = document.getElementById("error");
  const voiceToggle = document.getElementById("voice-toggle");
  const headIcon = document.querySelector(".chat-head .trainer-icon");

  const postUrl = chat.dataset.postUrl;
  const language = chat.dataset.language;
  const trainerId = chat.dataset.trainer;
  const trainerIcon = headIcon.textContent;

  /* =====================================================
     Trainer voice (browser text-to-speech, free, no key)
     ===================================================== */
  const synth = window.speechSynthesis;
  const voiceSupported = !!synth && "SpeechSynthesisUtterance" in window;

  // Each trainer gets its own speed and pitch. Some browser voices ignore
  // pitch or rate, so the difference can be small on those voices.
  const VOICE_STYLES = {
    male_human:   { rate: 0.95, pitch: 0.9,  gender: "male" },
    female_human: { rate: 0.95, pitch: 1.05, gender: "female" },
    dog:          { rate: 1.05, pitch: 1.25, gender: "male" },
    cat:          { rate: 0.95, pitch: 1.45, gender: "female" },
    cartoon:      { rate: 1.1,  pitch: 1.6,  gender: "any" },
  };
  const DEFAULT_STYLE = { rate: 1, pitch: 1, gender: "any" };
  const MALE_HINTS = ["david", "mark", "ravi", "prabhat", "guy", "george", "james", "ryan", "male"];
  const FEMALE_HINTS = ["zira", "heera", "neerja", "jenny", "aria", "samantha", "hazel", "susan", "female"];

  let chosenVoice = null;

  function scoreVoice(v, style) {
    const lang = (v.lang || "").toLowerCase().replace("_", "-");
    const name = (v.name || "").toLowerCase();
    let score = 0;

    // Prefer Indian English, then British, then any English.
    // A matching gender (+25) outweighs the accent preference.
    if (lang === "en-in") score += 30;
    else if (lang === "en-gb") score += 15;
    else if (lang.startsWith("en")) score += 10;

    const isFemale = FEMALE_HINTS.some(function (h) { return name.indexOf(h) !== -1; });
    const isMale = !isFemale && MALE_HINTS.some(function (h) { return name.indexOf(h) !== -1; });
    if (style.gender === "female" && isFemale) score += 25;
    if (style.gender === "male" && isMale) score += 25;

    // "Natural" / "Online" voices usually sound much better
    if (name.indexOf("natural") !== -1 || name.indexOf("online") !== -1) score += 5;
    return score;
  }

  function pickVoice() {
    if (chosenVoice) return chosenVoice;
    const style = VOICE_STYLES[trainerId] || DEFAULT_STYLE;
    const english = synth.getVoices().filter(function (v) {
      return (v.lang || "").toLowerCase().indexOf("en") === 0;
    });
    if (!english.length) return null;
    english.sort(function (a, b) { return scoreVoice(b, style) - scoreVoice(a, style); });
    chosenVoice = english[0];
    return chosenVoice;
  }

  function setSpeaking(on) {
    headIcon.classList.toggle("speaking", on);
  }

  function speak(text) {
    if (!voiceSupported || !text) return;
    synth.cancel();
    // A short delay avoids a Chrome quirk where speech started right after cancel() is dropped
    setTimeout(function () {
      const style = VOICE_STYLES[trainerId] || DEFAULT_STYLE;
      const u = new SpeechSynthesisUtterance(text);
      u.rate = style.rate;
      u.pitch = style.pitch;
      const v = pickVoice();
      if (v) { u.voice = v; u.lang = v.lang; } else { u.lang = "en-IN"; }
      u.onstart = function () { setSpeaking(true); };
      u.onend = function () { setSpeaking(false); };
      u.onerror = function () { setSpeaking(false); };
      synth.speak(u);
    }, 60);
  }

  function stopSpeaking() {
    if (voiceSupported) synth.cancel();
    setSpeaking(false);
  }

  function loadVoicePref() {
    try { return localStorage.getItem("speakup_voice") !== "off"; }
    catch (e) { return true; }
  }
  function saveVoicePref(on) {
    try { localStorage.setItem("speakup_voice", on ? "on" : "off"); }
    catch (e) { /* storage not available: ignore */ }
  }

  if (!voiceSupported) {
    document.body.classList.add("no-voice");
  } else {
    // Voices load a moment after the page opens in some browsers
    if (typeof synth.onvoiceschanged !== "undefined") {
      synth.onvoiceschanged = function () { chosenVoice = null; };
    }
    if (voiceToggle) {
      voiceToggle.checked = loadVoicePref();
      voiceToggle.addEventListener("change", function () {
        saveVoicePref(voiceToggle.checked);
        if (!voiceToggle.checked) stopSpeaking();
      });
    }
    window.addEventListener("beforeunload", stopSpeaking);
  }

  // One handler for every 🔊 button, including ones added later
  function onSpeakClick(e) {
    const btn = e.target.closest(".speak-btn");
    if (btn) speak(btn.dataset.speak);
  }
  messages.addEventListener("click", onSpeakClick);
  const retryBar = document.getElementById("retry-bar");
  if (retryBar) retryBar.addEventListener("click", onSpeakClick);

  /* =====================================================
     Chat
     ===================================================== */
  function scrollDown() {
    window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
  }

  // Build an element and set its text safely (no HTML injection)
  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function makeSpeakBtn(text) {
    const b = el("button", "speak-btn", "🔊");
    b.type = "button";
    b.title = "Listen";
    b.setAttribute("aria-label", "Listen");
    b.dataset.speak = text;
    return b;
  }

  function row(label, value, bold) {
    const r = el("div", "fb-row");
    if (label) {
      r.appendChild(el("span", "fb-label", label));
      r.appendChild(document.createTextNode(" "));
    }
    r.appendChild(bold ? el("strong", "", value) : document.createTextNode(value));
    return r;
  }

  function addUserBubble(text) {
    const wrap = el("div", "msg user");
    wrap.appendChild(el("div", "bubble user-bubble", text));
    messages.appendChild(wrap);
  }

  function addTrainerBubble(text) {
    const wrap = el("div", "msg trainer");
    wrap.appendChild(el("div", "trainer-icon small-icon", trainerIcon));
    wrap.appendChild(el("div", "bubble", text));
    wrap.appendChild(makeSpeakBtn(text));
    messages.appendChild(wrap);
  }

  function addFeedback(fb) {
    if (!fb) return;
    if (fb.has_mistake) {
      const card = el("div", "feedback");
      card.appendChild(el("div", "fb-title", "💡 Suggestion"));
      if (fb.original) card.appendChild(row("You said:", fb.original));
      const tryRow = row("Try:", fb.corrected, true);
      tryRow.appendChild(makeSpeakBtn(fb.corrected));
      card.appendChild(tryRow);
      if (fb.explanation_english) card.appendChild(row("Why:", fb.explanation_english));
      if (fb.explanation_native) card.appendChild(row("In " + language + ":", fb.explanation_native));
      messages.appendChild(card);
    } else if (fb.better_version) {
      const card = el("div", "feedback tip");
      card.appendChild(el("div", "fb-title", "✨ Nice! A more natural way to say it:"));
      const r = row("", fb.better_version, true);
      r.appendChild(makeSpeakBtn(fb.better_version));
      card.appendChild(r);
      messages.appendChild(card);
    }
  }

  function showError(msg) {
    errorBox.textContent = msg;
    errorBox.hidden = false;
  }

  /* =====================================================
     Retry loop
     ===================================================== */
  const retryTarget = document.getElementById("retry-target");
  const retrySpeak = document.getElementById("retry-speak");
  const skipBtn = document.getElementById("skip-btn");
  const skipUrl = chat.dataset.skipUrl;
  const defaultPlaceholder = input ? input.placeholder : "";

  // target = the corrected sentence, or "" to leave retry mode
  function setRetry(target) {
    if (!retryBar) return;
    if (target) {
      retryTarget.textContent = target;
      retrySpeak.dataset.speak = target;
      retryBar.hidden = false;
      input.placeholder = "Type the corrected sentence...";
    } else {
      retryBar.hidden = true;
      input.placeholder = defaultPlaceholder;
    }
  }

  function addNote(text, ok) {
    messages.appendChild(el("div", "retry-note " + (ok ? "ok" : "miss"), text));
  }

  function showReply(reply) {
    if (!reply) return;
    addTrainerBubble(reply);
    if (voiceSupported && voiceToggle && voiceToggle.checked) speak(reply);
  }

  function handleResponse(data) {
    if (data.mode === "needs_retry") {
      addFeedback(data.feedback);
      setRetry(data.target);
      if (voiceSupported && voiceToggle && voiceToggle.checked) speak(data.target);
    } else if (data.mode === "retry_again") {
      addNote(data.note, false);
    } else if (data.mode === "retry_passed" || data.mode === "retry_gave_up") {
      addNote(data.note, data.mode === "retry_passed");
      setRetry("");
      showReply(data.reply);
    } else {
      addFeedback(data.feedback);
      showReply(data.reply);
    }
  }

  if (skipBtn) {
    skipBtn.addEventListener("click", async function () {
      skipBtn.disabled = true;
      try {
        const res = await fetch(skipUrl, { method: "POST" });
        const data = await res.json().catch(function () { return {}; });
        if (res.ok) {
          addNote("Skipped. This mistake stays in your list to practice later.", false);
          setRetry("");
          showReply(data.reply);
        } else {
          showError(data.error || "Could not skip. Please try again.");
        }
      } catch (e) {
        showError("Could not reach the server. Check your connection and try again.");
      } finally {
        skipBtn.disabled = false;
        scrollDown();
      }
    });
  }

  if (chat.dataset.retryTarget) setRetry(chat.dataset.retryTarget);

  async function send() {
    const text = input.value.trim();
    if (!text) return;

    stopSpeaking();
    errorBox.hidden = true;
    addUserBubble(text);
    input.value = "";
    input.disabled = true;
    sendBtn.disabled = true;
    typing.hidden = false;
    scrollDown();

    try {
      const res = await fetch(postUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: text }),
      });
      const data = await res.json().catch(function () { return {}; });

      if (!res.ok) {
        // Remove the bubble we just added, give the text back, show the reason
        messages.removeChild(messages.lastElementChild);
        input.value = text;
        showError(data.error || "Something went wrong. Please try again.");
      } else {
        handleResponse(data);
      }
    } catch (e) {
      messages.removeChild(messages.lastElementChild);
      input.value = text;
      showError("Could not reach the server. Check your connection and try again.");
    } finally {
      typing.hidden = true;
      input.disabled = false;
      sendBtn.disabled = false;
      input.focus();
      scrollDown();
    }
  }

  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      send();
    });
    // Enter sends, Shift+Enter makes a new line
    input.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        send();
      }
    });
    input.focus();
  }

  scrollDown();
})();