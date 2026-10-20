import { API } from "./api.js";

const state = {
  file: null,
  phone: null,
  industryId: null,
  requestId: null,
  analysis: null,
  questionLimit: 5,
  questionsUsed: 0,
};

const $ = (id) => document.getElementById(id);
const show = (id) => $(id).classList.remove("hidden");
const hide = (id) => $(id).classList.add("hidden");
const setAlert = (msg, kind = "error") => {
  const el = $("alert");
  el.textContent = msg;
  el.className = `alert ${kind}`;
  el.classList.remove("hidden");
  if (kind === "success") setTimeout(() => el.classList.add("hidden"), 4000);
};
const setModalError = (msg) => {
  const el = $("modal-error");
  if (msg) {
    el.textContent = msg;
    el.classList.remove("hidden");
  } else {
    el.classList.add("hidden");
  }
};

// --- مودال ---
function openModal() {
  $("auth-modal").classList.add("active");
  $("modal-step-phone").classList.remove("hidden");
  $("modal-step-otp").classList.add("hidden");
  setModalError(null);
  $("phone-input").value = "";
  $("phone-input").focus();
}

function closeModal() {
  $("auth-modal").classList.remove("active");
  setModalError(null);
}

// --- بارگذاری اولیه ---
async function bootstrap() {
  try {
    const s = await API.get("/api/settings/public/");
    state.questionLimit = s.question_limit ?? 5;
  } catch { /* ignore */ }

  try {
    const list = await API.get("/api/industries/");
    const sel = $("industry-select");
    sel.innerHTML = `<option value="">انتخاب صنعت...</option>` +
      list.map(i => `<option value="${i.id}">${i.name}</option>`).join("");
  } catch {
    setAlert("خطا در دریافت فهرست صنایع.");
  }
}

// --- انتخاب فایل ---
function bindUpload() {
  const input = $("file-input");
  const dz = $("dropzone");

  dz.addEventListener("click", (e) => {
    if (e.target !== input) input.click();
  });
  dz.addEventListener("dragover", (e) => { e.preventDefault(); dz.classList.add("drag"); });
  dz.addEventListener("dragleave", () => dz.classList.remove("drag"));
  dz.addEventListener("drop", (e) => {
    e.preventDefault();
    dz.classList.remove("drag");
    if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
  });
  input.addEventListener("change", () => {
    if (input.files.length) handleFile(input.files[0]);
  });

  $("industry-select").addEventListener("input", validateUpload);
}

function handleFile(file) {
  const maxMB = 8;
  if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
    return setAlert("فرمت تصویر پشتیبانی نمی‌شود (JPEG/PNG/WEBP).");
  }
  if (file.size > maxMB * 1024 * 1024) {
    return setAlert(`حجم تصویر بیش از ${maxMB} مگابایت است.`);
  }
  state.file = file;
  const preview = $("preview");
  preview.src = URL.createObjectURL(file);
  preview.classList.remove("hidden");
  const dzText = document.querySelector("#dropzone .dz-text");
  if (dzText) dzText.textContent = "تغییر تصویر";
  validateUpload();
}

function validateUpload() {
  const industry = $("industry-select").value;
  state.industryId = industry;
  const ok = state.file && industry;
  $("btn-request-otp").disabled = !ok;
}

// --- باز کردن مودال با کلیک روی دکمه اصلی ---
function bindModalTriggers() {
  $("btn-request-otp").addEventListener("click", () => {
    openModal();
  });
  
  $("modal-close-btn").addEventListener("click", closeModal);
  
  // بستن مودال با کلیک روی فضای خالی
  $("auth-modal").addEventListener("click", (e) => {
    if (e.target === $("auth-modal")) closeModal();
  });
}

// --- عملیات داخل مودال ---
function bindModalActions() {
  // ارسال OTP
  $("btn-send-otp").addEventListener("click", async () => {
    const phone = $("phone-input").value.trim();
    if (!/^0?9\d{9}$/.test(phone.replace(/\D/g, ""))) {
      return setModalError("شماره موبایل معتبر نیست.");
    }
    
    const btn = $("btn-send-otp");
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span>';
    setModalError(null);

    try {
      const res = await API.postJSON("/api/verification/request/", { phone });
      state.phone = res.phone;
      $("display-phone").textContent = res.phone;
      $("modal-step-phone").classList.add("hidden");
      $("modal-step-otp").classList.remove("hidden");
      $("otp-input").focus();
    } catch (e) {
      setModalError(e.message);
    } finally {
      btn.disabled = false;
      btn.textContent = "دریافت کد تأیید";
    }
  });

  // ارسال مجدد
  $("btn-resend-otp").addEventListener("click", async () => {
    try {
      await API.postJSON("/api/verification/request/", { phone: state.phone });
      setModalError(null);
      setAlert("کد جدید ارسال شد.", "success");
    } catch (e) {
      setModalError(e.message);
    }
  });

  // تأیید OTP
  $("btn-verify-otp").addEventListener("click", async () => {
    const code = $("otp-input").value.trim();
    if (!/^\d{4,6}$/.test(code)) return setModalError("کد تأیید معتبر نیست.");
    
    const btn = $("btn-verify-otp");
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span>';
    setModalError(null);

    try {
      await API.postJSON("/api/verification/verify/", { phone: state.phone, code });
      // بستن مودال و ادامه فرایند
      closeModal();
      await loadQuotaAndContinue();
    } catch (e) {
      setModalError(e.message);
    } finally {
      btn.disabled = false;
      btn.textContent = "تأیید و ادامه";
    }
  });
}

async function loadQuotaAndContinue() {
  try {
    const q = await API.get(`/api/quota/status/?phone=${encodeURIComponent(state.phone)}`);
    $("quota-info").textContent =
      `سهمیه تصاویر: ${q.used_count} مصرف‌شده از ${q.total_quota} — باقی‌مانده: ${q.remaining}`;
    if (!q.can_use) {
      $("btn-analyze").disabled = true;
      setAlert("سهمیه پنج تصویر آزمایشی شما تکمیل شده است. برای ادامه با مدیریت تماس بگیرید.");
    }
    // مخفی کردن مرحله ۱ و نمایش مرحله ۲ (تحلیل)
    hide("step-upload");
    show("step-analyze");
  } catch (e) { setAlert(e.message); }
}

// --- تحلیل ---
function bindAnalyze() {
  $("btn-analyze").addEventListener("click", async () => {
    const form = new FormData();
    form.append("phone", state.phone);
    form.append("industry_id", state.industryId);
    form.append("image", state.file);
    form.append("request_id", crypto.randomUUID());

    $("btn-analyze").disabled = true;
    $("btn-analyze").innerHTML = '<span class="spinner"></span> در حال تحلیل...';
    try {
      const res = await API.postForm("/api/analysis/analyze/", form);
      state.analysis = res;
      state.requestId = res.request_id;
      state.questionsUsed = res.questions_used;
      renderResult(res);
      hide("step-analyze");
      show("step-result");
      show("step-qa");
      renderChat([]);
    } catch (e) {
      setAlert(e.message);
      $("btn-analyze").disabled = false;
      $("btn-analyze").innerHTML = '<i class="bi bi-lightning-charge-fill"></i> پردازش تصویر';
    }
  });
}

function renderResult(r) {
  const box = $("result-box");
  const defects = (r.defects || []).map(d => `
    <li class="defect-item">
      <strong>${d.name}</strong>
      <p>${d.description || ""}</p>
      ${d.confidence != null ? `<small style="color:var(--text-muted);font-size:12px;">میزان اطمینان: ${(d.confidence * 100).toFixed(0)}٪</small>` : ""}
    </li>
  `).join("");

  box.innerHTML = `
    <div class="result-head">
      <span class="badge">${r.industry_name}</span>
      <span class="badge ${r.status === 'success' ? 'success' : 'failed'}">${r.status === "success" ? "موفق" : r.status}</span>
    </div>
    <p class="summary" style="font-size:15px; line-height:1.8; margin-bottom:20px;">${r.summary || "خلاصه‌ای بازنگشت."}</p>
    <h3 style="font-size:16px; margin-bottom:12px;">عیوب احتمالی</h3>
    <ul class="defect-list">${defects || "<li class='defect-item'>عیب مشخصی گزارش نشد.</li>"}</ul>
    <p class="disclaimer" style="font-size:12px; color:var(--text-muted); border-top:1px dashed var(--border-light); padding-top:16px; margin-top:20px;">
      این تحلیل صرفاً ارزیابی اولیه و نمایشی است و جایگزین بازرسی صنعتی تأییدشده نیست.
    </p>
  `;
}

// --- پرسش و پاسخ ---
function escapeHTML(str) {
  return String(str).replace(/[&<>"']/g, s => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[s]));
}

function renderChat(messages) {
  const chat = $("chat");
  chat.innerHTML = messages.map(m => `
    <div class="msg ${m.role}">
      <div class="msg-avatar">${m.role === 'user' ? '<i class="bi bi-person"></i>' : '<i class="bi bi-robot"></i>'}</div>
      <div class="msg-bubble">${escapeHTML(m.content)}</div>
    </div>
  `).join("");
  updateQaHint();
}

function appendMessage(m) {
  const chat = $("chat");
  const wrap = document.createElement("div");
  wrap.className = `msg ${m.role}`;
  wrap.innerHTML = `
    <div class="msg-avatar">${m.role === 'user' ? '<i class="bi bi-person"></i>' : '<i class="bi bi-robot"></i>'}</div>
    <div class="msg-bubble">${escapeHTML(m.content)}</div>
  `;
  chat.appendChild(wrap);
  chat.scrollTop = chat.scrollHeight;
}

function updateQaHint() {
  const remaining = Math.max(0, state.questionLimit - state.questionsUsed);
  $("qa-hint").textContent = remaining > 0
    ? `پرسش‌های باقی‌مانده برای این تصویر: ${remaining}`
    : "سقف ۵ پرسش برای این تصویر مصرف شده است.";
  $("btn-ask").disabled = remaining <= 0;
  $("question-input").disabled = remaining <= 0;
}

function bindQa() {
  $("btn-ask").addEventListener("click", async () => {
    const input = $("question-input");
    const q = input.value.trim();
    if (!q) return;
    if (state.questionsUsed >= state.questionLimit) return;

    appendMessage({ role: "user", content: q });
    input.value = "";
    state.questionsUsed++;
    updateQaHint();

    try {
      const res = await API.postJSON("/api/conversations/ask/", {
        request_id: state.requestId,
        question: q,
      });
      appendMessage({ role: "assistant", content: res.content });
    } catch (e) {
      appendMessage({ role: "assistant", content: `خطا: ${e.message}` });
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  bootstrap();
  bindUpload();
  bindModalTriggers();
  bindModalActions();
  bindAnalyze();
  bindQa();
});