let allStyles = [];
let regularStyles = [];
let adultStyles = [];

const PERCHANCE_EMBED_URL = "https://image-generation.perchance.org/embed#";
const samplePrompts = [
  "cyberpunk ronin warrior standing in neon lit rain, intricate cybernetics, katana, reflective puddles",
  "ethereal portrait of an elf sorceress in an ancient enchanted forest, magical glowing bioluminescent dust",
  "dramatic cinematic shot of an astronaut looking at an alien ruined megalith on Mars, dust storm",
  "gorgeous anime character portrait, soft natural lighting, detailed expressive eyes, studio ghibli aesthetic",
  "hyper-detailed medieval knight in ornate gilded gothic armor, dramatic volumetric rim lighting",
  "portrait of a futuristic cyborg woman, elegant features, glowing holographic interface, 8k uhd",
  "mythological phoenix rising from vibrant swirling flames and embers, majestic wings, digital painting"
];

document.addEventListener("DOMContentLoaded", async () => {
  setupEventListeners();
  await loadStyles();
});

function setupEventListeners() {
  const adultToggle = document.getElementById("adultModeToggle");
  const adultLabel = document.getElementById("adultLabel");
  const nsfwBox = document.getElementById("nsfwModifiersBox");

  adultToggle.addEventListener("change", (event) => {
    const isAdult = event.target.checked;
    adultLabel.innerHTML = isAdult
      ? '🔞 Adult Mode (+18): <b style="color:#ff3366;">ON</b>'
      : "🔞 Adult Mode (+18): <b>OFF</b>";
    nsfwBox.style.display = isAdult ? "block" : "none";
    populateStyleDropdown(isAdult);
  });

  document.getElementById("guidanceScale").addEventListener("input", (event) => {
    document.getElementById("gVal").textContent = Number(event.target.value).toFixed(1);
  });
  document.getElementById("randomPromptBtn").addEventListener("click", () => {
    document.getElementById("promptInput").value = samplePrompts[Math.floor(Math.random() * samplePrompts.length)];
  });
  document.getElementById("randomSeedBtn").addEventListener("click", () => {
    document.getElementById("seedInput").value = -1;
  });
  document.getElementById("clearNegBtn").addEventListener("click", () => {
    document.getElementById("negativeInput").value = "";
  });
  document.getElementById("clearEmbedsBtn").addEventListener("click", clearEmbeds);
  document.getElementById("generateBtn").addEventListener("click", handleGenerate);

  document.querySelectorAll(".pill").forEach((pill) => pill.addEventListener("click", () => {
    const prompt = document.getElementById("promptInput");
    prompt.value = [prompt.value.trim(), pill.dataset.tag].filter(Boolean).join(", ");
  }));
}

async function loadStyles() {
  try {
    const response = await fetch("/api/styles");
    const data = await response.json();
    allStyles = data.all || [];
    regularStyles = data.regular || [];
    adultStyles = data.adult || [];
    populateStyleDropdown(false);
    populateMixDropdown();
  } catch (error) {
    console.error("Failed to load styles:", error);
    showStatus("Could not load local style presets.", "error");
  }
}

function populateStyleDropdown(isAdult) {
  const select = document.getElementById("artStyleSelect");
  const current = select.value;
  select.innerHTML = "";
  if (isAdult) addOptions(select, "🔞 Adult (+18) Styles", adultStyles);
  addOptions(select, "🎨 Standard Styles", regularStyles);
  select.value = isAdult && adultStyles.includes(current)
    ? current
    : (regularStyles.includes(current) ? current : "Realistic images");
}

function addOptions(select, label, styles) {
  const group = document.createElement("optgroup");
  group.label = label;
  styles.forEach((style) => group.appendChild(new Option(style, style)));
  select.appendChild(group);
}

function populateMixDropdown() {
  const select = document.getElementById("artStyleMixSelect");
  select.innerHTML = '<option value="Not Mix">Not Mix</option><option value="NSFW">NSFW (+, nsfw)</option>';
  allStyles.filter((style) => style !== "No style").forEach((style) => select.add(new Option(style, style)));
}

async function handleGenerate() {
  const prompt = document.getElementById("promptInput").value.trim();
  if (!prompt) {
    showStatus("Please enter a prompt before generating.", "error");
    return;
  }

  const button = document.getElementById("generateBtn");
  button.disabled = true;
  button.querySelector(".btn-text").style.display = "none";
  button.querySelector(".btn-spinner").style.display = "inline";

  try {
    const response = await fetch("/api/compose", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt,
        negative_prompt: document.getElementById("negativeInput").value.trim(),
        art_style: document.getElementById("artStyleSelect").value,
        art_style_mix: document.getElementById("artStyleMixSelect").value,
        adult_mode: document.getElementById("adultModeToggle").checked
      })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Could not prepare the prompt.");

    const count = Number(document.getElementById("batchCount").value);
    const seed = Number(document.getElementById("seedInput").value);
    createPerchanceLaunches(
      data.prompt,
      data.negative_prompt,
      document.getElementById("shapeSelect").value,
      Number(document.getElementById("guidanceScale").value),
      seed,
      count
    );
    showStatus("Your Perchance generator link is ready below. Open it and complete any verification there, if prompted.", "success");
  } catch (error) {
    console.error("Embed setup error:", error);
    showStatus(`Error: ${error.message}`, "error");
  } finally {
    button.disabled = false;
    button.querySelector(".btn-text").style.display = "inline";
    button.querySelector(".btn-spinner").style.display = "none";
  }
}

function createPerchanceLaunches(prompt, negativePrompt, resolution, guidanceScale, requestedSeed, count) {
  const grid = document.getElementById("embedGrid");
  document.getElementById("emptyState")?.remove();

  for (let index = 0; index < count; index += 1) {
    const config = {
      saveChannel: "b7kc35yv7u",
      saveTitle: "",
      saveDescription: "Generated through the local Perchance embed UI.",
      prompt,
      negativePrompt,
      resolution,
      guidanceScale,
      seed: requestedSeed > 0 ? requestedSeed + index : -1
    };
    const card = document.createElement("section");
    card.className = "launch-card";
    const title = document.createElement("h3");
    title.textContent = `Generation ${grid.children.length + 1}`;
    const description = document.createElement("p");
    description.textContent = `${resolution} • CFG ${guidanceScale} • ${config.seed > 0 ? `Seed ${config.seed}` : "Random seed"}`;
    const link = document.createElement("a");
    link.className = "btn-primary launch-link";
    link.href = `${PERCHANCE_EMBED_URL}${encodeURIComponent(JSON.stringify(config))}`;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.textContent = "Open Perchance generator ↗";
    card.append(title, description, link);
    grid.prepend(card);
  }
}

function clearEmbeds() {
  document.getElementById("embedGrid").innerHTML = '<div class="empty-state" id="emptyState"><p>No generator is ready yet.</p><p class="sub">Configure your settings and click <b>Generate Image</b>.</p></div>';
}

function showStatus(message, type) {
  const box = document.getElementById("statusBox");
  box.style.display = "block";
  box.className = `status-box ${type}`;
  box.textContent = message;
}
