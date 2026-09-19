let allStyles = [];
let regularStyles = [];
let adultStyles = [];
let generatedImages = [];
let globalRevealNsfw = false;

const samplePrompts = [
  "cyberpunk ronin warrior standing in neon lit rain, intricate cybernetics, katana, reflective puddles",
  "ethereal portrait of an elf sorceress in an ancient enchanted forest, magical glowing bioluminescent dust",
  "dramatic cinematic shot of an astronaut looking at an alien ruined megalith on Mars, dust storm",
  "gorgeous anime character portrait, soft natural lighting, detailed expressive eyes, studio ghibli aesthetic",
  "hyper-detailed medieval knight in ornate gilded gothic armor, dramatic volumetric rim lighting",
  "portrait of a futuristic cyborg woman, elegant features, glowing holographic interface, 8k uhd",
  "mythological phoenix rising from vibrant swirling flames and embers, majestic wings, digital painting"
];

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", async () => {
  setupEventListeners();
  await loadStyles();
  await loadHistory();
});

async function loadHistory() {
  try {
    const res = await fetch("/api/history");
    const data = await res.json();
    if (data.images && data.images.length > 0) {
      generatedImages = data.images;
      renderGallery();
    }
  } catch (err) {
    console.error("Failed to load history:", err);
  }
}

function setupEventListeners() {
  const adultToggle = document.getElementById("adultModeToggle");
  const adultLabel = document.getElementById("adultLabel");
  const nsfwBox = document.getElementById("nsfwModifiersBox");
  const gSlider = document.getElementById("guidanceScale");
  const gVal = document.getElementById("gVal");
  const generateBtn = document.getElementById("generateBtn");
  const randomPromptBtn = document.getElementById("randomPromptBtn");
  const randomSeedBtn = document.getElementById("randomSeedBtn");
  const clearNegBtn = document.getElementById("clearNegBtn");
  const unblurAllBtn = document.getElementById("unblurAllBtn");
  const clearGalleryBtn = document.getElementById("clearGalleryBtn");

  // Adult Mode Toggle
  adultToggle.addEventListener("change", (e) => {
    const isAdult = e.target.checked;
    adultLabel.innerHTML = isAdult 
      ? '🔞 Adult Mode (+18): <b style="color:#ff3366;">ON</b>' 
      : '🔞 Adult Mode (+18): <b>OFF</b>';
    nsfwBox.style.display = isAdult ? "block" : "none";
    populateStyleDropdown(isAdult);

    // If turned on, auto switch to a prominent NSFW style if currently on basic
    const styleSelect = document.getElementById("artStyleSelect");
    if (isAdult && styleSelect.value === "No style") {
      styleSelect.value = "NSFW - Realistic";
    }
  });

  // Guidance Scale Slider
  gSlider.addEventListener("input", (e) => {
    gVal.textContent = parseFloat(e.target.value).toFixed(1);
  });

  // Random Prompt Button
  randomPromptBtn.addEventListener("click", () => {
    const promptInput = document.getElementById("promptInput");
    const choice = samplePrompts[Math.floor(Math.random() * samplePrompts.length)];
    promptInput.value = choice;
  });

  // Random Seed Button
  randomSeedBtn.addEventListener("click", () => {
    document.getElementById("seedInput").value = -1;
  });

  // Clear Negative Button
  clearNegBtn.addEventListener("click", () => {
    document.getElementById("negativeInput").value = "";
  });

  // Unblur NSFW Images Button
  unblurAllBtn.addEventListener("click", () => {
    globalRevealNsfw = !globalRevealNsfw;
    unblurAllBtn.textContent = globalRevealNsfw ? "🙈 Hide NSFW Blur" : "👁 Reveal NSFW Blur";
    document.querySelectorAll(".image-wrap").forEach(wrap => {
      const isNsfw = wrap.dataset.nsfw === "true";
      if (isNsfw) {
        if (globalRevealNsfw) {
          wrap.classList.remove("nsfw-blurred");
          const overlay = wrap.querySelector(".nsfw-overlay");
          if (overlay) overlay.style.display = "none";
        } else {
          wrap.classList.add("nsfw-blurred");
          const overlay = wrap.querySelector(".nsfw-overlay");
          if (overlay) overlay.style.display = "flex";
        }
      }
    });
  });

  // Clear Gallery Button
  clearGalleryBtn.addEventListener("click", () => {
    generatedImages = [];
    renderGallery();
  });

  // Modifier Pills
  document.querySelectorAll(".pill").forEach(pill => {
    pill.addEventListener("click", () => {
      const tag = pill.dataset.tag;
      const promptInput = document.getElementById("promptInput");
      const current = promptInput.value.trim();
      if (current) {
        promptInput.value = `${current}, ${tag}`;
      } else {
        promptInput.value = tag;
      }
    });
  });

  // Generate Button
  generateBtn.addEventListener("click", handleGenerate);
}

async function loadStyles() {
  try {
    const res = await fetch("/api/styles");
    const data = await res.json();
    allStyles = data.all || [];
    regularStyles = data.regular || [];
    adultStyles = data.adult || [];
    populateStyleDropdown(false);
    populateMixDropdown();
  } catch (err) {
    console.error("Failed to load styles:", err);
  }
}

function populateStyleDropdown(isAdult) {
  const select = document.getElementById("artStyleSelect");
  const currentVal = select.value;
  select.innerHTML = "";

  if (isAdult) {
    const optGroupAdult = document.createElement("optgroup");
    optGroupAdult.label = "🔞 Adult (+18) Styles";
    adultStyles.forEach(s => {
      const opt = document.createElement("option");
      opt.value = s;
      opt.textContent = s;
      optGroupAdult.appendChild(opt);
    });
    select.appendChild(optGroupAdult);
  }

  const optGroupRegular = document.createElement("optgroup");
  optGroupRegular.label = "🎨 Standard Styles";
  regularStyles.forEach(s => {
    const opt = document.createElement("option");
    opt.value = s;
    opt.textContent = s;
    optGroupRegular.appendChild(opt);
  });
  select.appendChild(optGroupRegular);

  if (isAdult && adultStyles.includes(currentVal)) {
    select.value = currentVal;
  } else if (!isAdult && adultStyles.includes(currentVal)) {
    select.value = "Realistic images";
  } else if (currentVal) {
    select.value = currentVal;
  }
}

function populateMixDropdown() {
  const select = document.getElementById("artStyleMixSelect");
  select.innerHTML = `
    <option value="Not Mix">Not Mix</option>
    <option value="NSFW">NSFW (+, nsfw)</option>
  `;
  allStyles.forEach(s => {
    if (s !== "No style") {
      const opt = document.createElement("option");
      opt.value = s;
      opt.textContent = s;
      select.appendChild(opt);
    }
  });
}

async function handleGenerate() {
  const promptInput = document.getElementById("promptInput");
  const prompt = promptInput.value.trim();
  if (!prompt) {
    showStatus("Please enter a prompt before generating.", "error");
    return;
  }

  const negative = document.getElementById("negativeInput").value.trim();
  const artStyle = document.getElementById("artStyleSelect").value;
  const artStyleMix = document.getElementById("artStyleMixSelect").value;
  const adultMode = document.getElementById("adultModeToggle").checked;
  const shape = document.getElementById("shapeSelect").value;
  const guidanceScale = parseFloat(document.getElementById("guidanceScale").value);
  const seed = parseInt(document.getElementById("seedInput").value, 10);
  const batchCount = parseInt(document.getElementById("batchCount").value, 10);

  const generateBtn = document.getElementById("generateBtn");
  const btnText = generateBtn.querySelector(".btn-text");
  const btnSpinner = generateBtn.querySelector(".btn-spinner");

  generateBtn.disabled = true;
  btnText.style.display = "none";
  btnSpinner.style.display = "inline";
  showStatus(`Connecting to Perchance API... Generating ${batchCount} image(s)...`, "success");

  try {
    const payload = {
      prompt,
      negative_prompt: negative,
      art_style: artStyle,
      art_style_mix: artStyleMix,
      adult_mode: adultMode,
      shape,
      guidance_scale: guidanceScale,
      seed,
      batch_count: batchCount
    };

    const res = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (!res.ok || data.status !== "success") {
      throw new Error(data.detail || "Failed to generate images.");
    }

    // Add generated images to beginning of list
    data.images.forEach(img => generatedImages.unshift(img));
    renderGallery();
    showStatus(`Successfully generated ${data.images.length} image(s)!`, "success");
  } catch (err) {
    console.error("Generation error:", err);
    showStatus(`Error: ${err.message}`, "error");
  } finally {
    generateBtn.disabled = false;
    btnText.style.display = "inline";
    btnSpinner.style.display = "none";
  }
}

function showStatus(msg, type) {
  const box = document.getElementById("statusBox");
  box.style.display = "block";
  box.className = `status-box ${type}`;
  box.textContent = msg;
}

function renderGallery() {
  const grid = document.getElementById("galleryGrid");
  if (generatedImages.length === 0) {
    grid.innerHTML = `
      <div class="empty-state" id="emptyState">
        <p>No images generated yet.</p>
        <p class="sub">Configure your settings and click <b>Generate Image</b> to start!</p>
      </div>
    `;
    return;
  }

  grid.innerHTML = "";
  generatedImages.forEach((img, idx) => {
    const card = document.createElement("div");
    card.className = "image-card";

    const isNsfw = img.maybe_nsfw;
    const shouldBlur = isNsfw && !globalRevealNsfw;

    card.innerHTML = `
      <div class="image-wrap ${shouldBlur ? 'nsfw-blurred' : ''}" data-nsfw="${isNsfw}">
        <img src="${img.image_url}" alt="Generated AI image" loading="lazy">
        ${isNsfw ? `
          <div class="nsfw-overlay" style="display: ${shouldBlur ? 'flex' : 'none'};">
            <span style="font-size:1.5rem;">🔞</span>
            <b style="color:#ff3366;">18+ Content Warning</b>
            <p style="font-size:0.75rem; color:#ccc;">This image is flagged as adult / sensitive.</p>
            <button type="button" class="btn-reveal" onclick="revealSingleImage(this)">Click to View</button>
          </div>
        ` : ''}
      </div>
      <div class="image-info">
        <div class="image-prompt" title="${escapeHtml(img.prompt)}">
          <b>Prompt:</b> ${escapeHtml(img.prompt)}
        </div>
        <div class="image-meta">
          <span>Seed: <code>${img.seed}</code></span>
          <span>${img.width}x${img.height}</span>
          <span class="badge ${isNsfw ? 'badge-nsfw' : 'badge-sfw'}">${isNsfw ? 'NSFW' : 'SFW'}</span>
        </div>
        <div class="image-actions">
          <a href="${img.image_url}" download="perchance_${(img.image_id || 'img').slice(0, 8)}.jpeg" class="btn-sm" style="text-decoration:none; text-align:center; flex:1;">⬇️ Download</a>
          <button type="button" class="btn-sm" onclick="copyPrompt('${escapeHtml(img.prompt)}')">📋 Copy</button>
        </div>
      </div>
    `;

    grid.appendChild(card);
  });
}

function revealSingleImage(btn) {
  const wrap = btn.closest(".image-wrap");
  wrap.classList.remove("nsfw-blurred");
  const overlay = wrap.querySelector(".nsfw-overlay");
  if (overlay) overlay.style.display = "none";
}

function copyPrompt(text) {
  navigator.clipboard.writeText(text);
  alert("Prompt copied to clipboard!");
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}
