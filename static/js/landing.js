import { API } from "./api.js";

async function loadIndustries() {
  const grid = document.getElementById("industries-grid");
  try {
    const list = await API.get("/api/industries/");
    grid.innerHTML = list.map(i => `<span class="chip">${i.name}</span>`).join("");
  } catch (e) {
    grid.innerHTML = `<span class="chip error">خطا در دریافت صنایع</span>`;
  }
}

async function loadPublicSettings() {
  try {
    const s = await API.get("/api/settings/public/");
    const callBtn = document.getElementById("cta-call");
    if (s.management_phone) callBtn.href = `tel:${s.management_phone}`;
  } catch { /* ignore */ }
}

document.addEventListener("DOMContentLoaded", () => {
  loadIndustries();
  loadPublicSettings();
});