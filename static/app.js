/**
 * Frame by Frame: Animation Idea Generator — Frontend Client Application
 * Pure Vanilla ES6 JavaScript — Strict XSS Immunity (Strictly uses .textContent & .value)
 */

document.addEventListener("DOMContentLoaded", () => {
  // State
  let currentPlan = null;

  // DOM Elements - Form & Inputs
  const generatorForm = document.getElementById("generator-form");
  const ideaInput = document.getElementById("idea-input");
  const charCounter = document.getElementById("char-counter");
  const runtimeSelect = document.getElementById("runtime-select");
  const moodSelect = document.getElementById("mood-select");
  const audienceSelect = document.getElementById("audience-select");
  const dialogueSelect = document.getElementById("dialogue-select");
  const complexitySelect = document.getElementById("complexity-select");
  const generateBtn = document.getElementById("generate-btn");
  const generateSpinner = document.getElementById("generate-spinner");
  const providerBadge = document.getElementById("provider-badge");

  // DOM Elements - Output & Toolbar
  const outputSection = document.getElementById("output-section");
  const copyBtn = document.getElementById("copy-btn");
  const openRevisionBtn = document.getElementById("open-revision-btn");
  const planTitle = document.getElementById("plan-title");
  const planLogline = document.getElementById("plan-logline");
  const planTags = document.getElementById("plan-tags");
  const charactersContainer = document.getElementById("characters-container");
  const scenesContainer = document.getElementById("scenes-container");
  const planSound = document.getElementById("plan-sound");

  // DOM Elements - Revision Modal
  const revisionModal = document.getElementById("revision-modal");
  const revisionForm = document.getElementById("revision-form");
  const revisionInput = document.getElementById("revision-input");
  const modalCloseBtn = document.getElementById("modal-close-btn");
  const modalCancelBtn = document.getElementById("modal-cancel-btn");
  const submitRevisionBtn = document.getElementById("submit-revision-btn");
  const revisionSpinner = document.getElementById("revision-spinner");

  // DOM Elements - Alerts & Toasts
  const errorBanner = document.getElementById("error-banner");
  const errorMessage = document.getElementById("error-message");
  const errorCloseBtn = document.getElementById("error-close-btn");
  const toast = document.getElementById("toast");

  // -------------------------------------------------------------------------
  // 1. Initial Health Check
  // -------------------------------------------------------------------------
  async function checkProviderHealth() {
    try {
      const res = await fetch("/api/health");
      if (!res.ok) throw new Error("Health check failed");
      const data = await res.json();
      
      if (data.provider && data.provider.configured) {
        providerBadge.className = "badge badge-success";
        providerBadge.textContent = `🟢 NVIDIA NIM (${data.provider.model.split("/").pop()})`;
      } else {
        providerBadge.className = "badge badge-warning";
        providerBadge.textContent = "🟡 Dev Mode (Mock Generator Active)";
      }
    } catch (err) {
      providerBadge.className = "badge badge-neutral";
      providerBadge.textContent = "⚪ Server Offline";
    }
  }
  checkProviderHealth();

  // -------------------------------------------------------------------------
  // 2. Character Counter & Input Validation
  // -------------------------------------------------------------------------
  ideaInput.addEventListener("input", () => {
    const len = ideaInput.value.length;
    charCounter.textContent = `${len} / 500`;
    if (len >= 490) {
      charCounter.style.color = "var(--warning)";
    } else {
      charCounter.style.color = "var(--text-dim)";
    }
  });

  // -------------------------------------------------------------------------
  // 3. Alerts and Toasts
  // -------------------------------------------------------------------------
  function showError(msg) {
    errorMessage.textContent = msg;
    errorBanner.classList.remove("hidden");
    errorBanner.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  function hideError() {
    errorBanner.classList.add("hidden");
  }

  errorCloseBtn.addEventListener("click", hideError);

  function showToast(msg) {
    toast.textContent = msg;
    toast.classList.remove("hidden");
    setTimeout(() => {
      toast.classList.add("hidden");
    }, 3200);
  }

  // -------------------------------------------------------------------------
  // 4. Plan Rendering & Safe In-Browser Editing
  // -------------------------------------------------------------------------
  function renderPlan(plan) {
    currentPlan = plan;
    hideError();

    // Render Title & Logline
    planTitle.value = plan.title || "";
    planLogline.value = plan.logline || "";

    // Sync title/logline edits back to state
    planTitle.oninput = () => { currentPlan.title = planTitle.value; };
    planLogline.oninput = () => { currentPlan.logline = planLogline.value; };

    // Render Meta Badges
    planTags.replaceChildren(); // Safe clear
    const tags = [
      `⏱️ ${plan.runtime}`,
      `🎭 ${plan.mood}`,
      `👥 ${plan.audience}`,
      `⚙️ ${plan.complexity}`,
      plan.has_dialogue ? "💬 Dialogue" : "🤫 Silent / Visual",
    ];
    tags.forEach(text => {
      const tagSpan = document.createElement("span");
      tagSpan.className = "plan-tag";
      tagSpan.textContent = text;
      planTags.appendChild(tagSpan);
    });

    // Render Characters
    charactersContainer.replaceChildren();
    (plan.characters || []).forEach((char, index) => {
      const card = document.createElement("div");
      card.className = "character-card";

      const nameInput = document.createElement("input");
      nameInput.type = "text";
      nameInput.className = "character-name-input";
      nameInput.value = char.name;
      nameInput.oninput = () => { currentPlan.characters[index].name = nameInput.value; };

      const roleInput = document.createElement("input");
      roleInput.type = "text";
      roleInput.className = "character-role-input";
      roleInput.value = char.role;
      roleInput.placeholder = "Role in story";
      roleInput.oninput = () => { currentPlan.characters[index].role = roleInput.value; };

      const goalInput = document.createElement("textarea");
      goalInput.rows = 2;
      goalInput.className = "character-goal-input";
      goalInput.value = char.goal;
      goalInput.placeholder = "Character objective";
      goalInput.oninput = () => { currentPlan.characters[index].goal = goalInput.value; };

      card.appendChild(nameInput);
      card.appendChild(roleInput);
      card.appendChild(goalInput);
      charactersContainer.appendChild(card);
    });

    // Render Scenes
    scenesContainer.replaceChildren();
    (plan.scenes || []).forEach((scene, index) => {
      const card = document.createElement("div");
      card.className = "scene-card";

      const header = document.createElement("div");
      header.className = "scene-card-header";

      const numBadge = document.createElement("span");
      numBadge.className = "scene-number-badge";
      numBadge.textContent = `Scene ${scene.scene_number || index + 1}`;
      header.appendChild(numBadge);
      card.appendChild(header);

      // Description
      const descGroup = document.createElement("div");
      descGroup.className = "scene-field-group";
      const descLabel = document.createElement("span");
      descLabel.className = "scene-sublabel";
      descLabel.textContent = "Action & Staging";
      const descTextarea = document.createElement("textarea");
      descTextarea.rows = 3;
      descTextarea.value = scene.description;
      descTextarea.oninput = () => { currentPlan.scenes[index].description = descTextarea.value; };
      descGroup.appendChild(descLabel);
      descGroup.appendChild(descTextarea);
      card.appendChild(descGroup);

      // Visual Suggestion
      const visualGroup = document.createElement("div");
      visualGroup.className = "scene-field-group";
      const visualLabel = document.createElement("span");
      visualLabel.className = "scene-sublabel";
      visualLabel.textContent = "Camera & Visual Suggestion";
      const visualInput = document.createElement("input");
      visualInput.type = "text";
      visualInput.className = "visual-suggestion-input";
      visualInput.value = scene.visual_suggestion;
      visualInput.oninput = () => { currentPlan.scenes[index].visual_suggestion = visualInput.value; };
      visualGroup.appendChild(visualLabel);
      visualGroup.appendChild(visualInput);
      card.appendChild(visualGroup);

      // Dialogue / Narration
      const dialogueGroup = document.createElement("div");
      dialogueGroup.className = "scene-field-group";
      const dialogueLabel = document.createElement("span");
      dialogueLabel.className = "scene-sublabel";
      dialogueLabel.textContent = "Dialogue / Narration";
      const dialogueInput = document.createElement("input");
      dialogueInput.type = "text";
      dialogueInput.className = "dialogue-input";
      dialogueInput.placeholder = "None (Pantomime/Silent)";
      dialogueInput.value = scene.dialogue || "";
      dialogueInput.oninput = () => {
        currentPlan.scenes[index].dialogue = dialogueInput.value.trim() || null;
      };
      dialogueGroup.appendChild(dialogueLabel);
      dialogueGroup.appendChild(dialogueInput);
      card.appendChild(dialogueGroup);

      scenesContainer.appendChild(card);
    });

    // Sound Suggestions
    const soundArray = plan.sound_suggestions || [];
    planSound.value = soundArray.join("\n• ");
    if (soundArray.length > 0 && !planSound.value.startsWith("• ")) {
      planSound.value = "• " + planSound.value;
    }
    planSound.oninput = () => {
      currentPlan.sound_suggestions = planSound.value
        .split("\n")
        .map(s => s.replace(/^•\s*/, "").trim())
        .filter(Boolean);
    };

    // Reveal output section
    outputSection.classList.remove("hidden");
    outputSection.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  // -------------------------------------------------------------------------
  // 5. Generate Plan Submission
  // -------------------------------------------------------------------------
  generatorForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    hideError();

    const idea = ideaInput.value.trim();
    if (idea.length < 5) {
      showError("Please enter an animation idea with at least 5 characters.");
      return;
    }

    const payload = {
      idea: idea,
      runtime: runtimeSelect.value,
      mood: moodSelect.value,
      audience: audienceSelect.value,
      has_dialogue: dialogueSelect.value === "true",
      complexity: complexitySelect.value,
    };

    // UI Loading state
    generateBtn.disabled = true;
    generateSpinner.classList.remove("hidden");

    try {
      const response = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (!response.ok) {
        const errorMsg = (data.error && data.error.message) || "Failed to generate animation plan.";
        throw new Error(errorMsg);
      }

      renderPlan(data);
      showToast("✨ Animation plan generated successfully!");
    } catch (err) {
      showError(err.message || "An unexpected network error occurred.");
    } finally {
      generateBtn.disabled = false;
      generateSpinner.classList.add("hidden");
    }
  });

  // -------------------------------------------------------------------------
  // 6. Revision Modal & Submission
  // -------------------------------------------------------------------------
  openRevisionBtn.addEventListener("click", () => {
    if (!currentPlan) return;
    revisionInput.value = "";
    revisionModal.classList.remove("hidden");
    revisionInput.focus();
  });

  function closeRevisionModal() {
    revisionModal.classList.add("hidden");
  }

  modalCloseBtn.addEventListener("click", closeRevisionModal);
  modalCancelBtn.addEventListener("click", closeRevisionModal);

  // Quick hint chips
  document.querySelectorAll(".quick-hint").forEach(chip => {
    chip.addEventListener("click", () => {
      revisionInput.value = chip.getAttribute("data-hint");
      revisionInput.focus();
    });
  });

  revisionForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const instruction = revisionInput.value.trim();
    if (instruction.length < 3) {
      showError("Please enter a revision instruction with at least 3 characters.");
      return;
    }

    submitRevisionBtn.disabled = true;
    revisionSpinner.classList.remove("hidden");

    try {
      const response = await fetch("/api/revise", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          previous_plan: currentPlan,
          revision_instruction: instruction,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        const errorMsg = (data.error && data.error.message) || "Failed to apply revision.";
        throw new Error(errorMsg);
      }

      closeRevisionModal();
      renderPlan(data);
      showToast("🔄 Story revised and updated!");
    } catch (err) {
      closeRevisionModal();
      showError(err.message || "Failed to apply story revision.");
    } finally {
      submitRevisionBtn.disabled = false;
      revisionSpinner.classList.add("hidden");
    }
  });

  // -------------------------------------------------------------------------
  // 7. Copy Formatted Plan to Clipboard
  // -------------------------------------------------------------------------
  copyBtn.addEventListener("click", () => {
    if (!currentPlan) return;

    let md = `# ${currentPlan.title}\n\n`;
    md += `**Logline:** ${currentPlan.logline}\n\n`;
    md += `**Runtime:** ${currentPlan.runtime} | **Mood:** ${currentPlan.mood} | **Audience:** ${currentPlan.audience} | **Scope:** ${currentPlan.complexity}\n\n`;
    md += `## Characters\n`;
    (currentPlan.characters || []).forEach(c => {
      md += `- **${c.name}** (${c.role}): Goal: ${c.goal}\n`;
    });
    md += `\n## Scene Breakdown\n`;
    (currentPlan.scenes || []).forEach(s => {
      md += `### Scene ${s.scene_number}\n`;
      md += `**Action:** ${s.description}\n`;
      md += `**Visual Framing:** ${s.visual_suggestion}\n`;
      if (s.dialogue) {
        md += `**Dialogue/Narration:** "${s.dialogue}"\n`;
      }
      if (s.sound_suggestions && s.sound_suggestions.length > 0) {
        md += `**Sound FX:** ${s.sound_suggestions.join(", ")}\n`;
      }
      md += `\n`;
    });
    if (currentPlan.sound_suggestions && currentPlan.sound_suggestions.length > 0) {
      md += `## Sound Design Notes\n`;
      currentPlan.sound_suggestions.forEach(snd => {
        md += `- ${snd}\n`;
      });
    }

    navigator.clipboard.writeText(md)
      .then(() => {
        showToast("📋 Formatted animation plan copied to clipboard!");
      })
      .catch(() => {
        showError("Clipboard copy failed. Please select and copy manually.");
      });
  });
});
