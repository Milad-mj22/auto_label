import { API } from "./api.js";

const state = {
  file: null,
  fileUrl: null,
  phone: null,
  industryId: null,
  requestId: null,
  analysis: null,
  questionLimit: 5,
  questionsUsed: 0,
  isVerified: false,
  pendingAnalysis: false,
  analyzing: false,
  asking: false,
};

const $ = (id) => document.getElementById(id);
const show = (id) => $(id).classList.remove("hidden");
const hide = (id) => $(id).classList.add("hidden");

function escapeHTML(str) {
  return String(str ?? "").replace(/[&<>"']/g, (s) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[s]));
}

/* ---------- آلرت ---------- */
let alertTimer = null;
function setAlert(msg, kind = "error") {
  const el = $("alert");
  el.textContent = msg;
  el.className = `alert ${kind}`;
  clearTimeout(alertTimer);
  if (kind === "success") alertTimer = setTimeout(() => el.classList.add("hidden"), 4000);
}
function clearAlert() { $("alert").classList.add("hidden"); }

function setModalError(msg) {
  const el = $("modal-error");
  if (msg) { el.textContent = msg; el.classList.remove("hidden"); }
  else el.classList.add("hidden");
}

/* ---------- ابزار شماره ---------- */
function normalizeDigits(str) {
  return String(str)
    .replace(/[۰-۹]/g, (d) => "۰۱۲۳۴۵۶۷۸۹".indexOf(d))
    .replace(/[٠-٩]/g, (d) => "٠١٢٣٤٥٦٧٨٩".indexOf(d));
}
function normalizePhone(raw) {
  const digits = normalizeDigits(raw).replace(/\D/g, "");
  if (/^09\d{9}$/.test(digits)) return digits;
  if (/^9\d{9}$/.test(digits)) return "0" + digits;
  if (/^989\d{9}$/.test(digits)) return "0" + digits.slice(2);
  return null;
}

/* ---------- جابه‌جایی بین دو نما ---------- */
function showView(name) {
  if (name === "result") {
    hide("view-upload");
    show("view-result");
    setTab("report");
  } else {
    show("view-upload");
    hide("view-result");
  }
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function setTab(tab) {
  $("view-result").dataset.tab = tab;
  document.querySelectorAll(".tab-btn").forEach((b) =>
    b.classList.toggle("active", b.dataset.tab === tab)
  );
  if (tab === "qa") {
    const chat = $("chat");
    chat.scrollTop = chat.scrollHeight;
  }
}

/* ---------- بارگذاری اولیه ---------- */
async function bootstrap() {
  try {
    const s = await API.get("/api/settings/public/");
    state.questionLimit = s.question_limit ?? 5;
  } catch { /* ignore */ }

  try {
    const list = await API.get("/api/industries/");
    $("industry-select").innerHTML =
      `<option value="">انتخاب صنعت...</option>` +
      list.map((i) => `<option value="${i.id}">${escapeHTML(i.name)}</option>`).join("");
  } catch {
    setAlert("خطا در دریافت فهرست صنایع.");
  }

  await checkStoredVerification();
}

async function checkStoredVerification() {
  const stored = localStorage.getItem("verified_phone");
  if (!stored) return;
  try {
    const res = await API.get(`/api/verification/check/?phone=${encodeURIComponent(stored)}`);
    if (res.verified) setVerified(res.phone || stored);
    else localStorage.removeItem("verified_phone");
  } catch { /* ignore */ }
}

function setVerified(phone) {
  state.phone = phone;
  state.isVerified = true;
  localStorage.setItem("verified_phone", phone);
  $("verified-phone-label").textContent = phone;
  show("change-phone-link");
}

function resetVerifiedState() {
  state.isVerified = false;
  state.phone = null;
  localStorage.removeItem("verified_phone");
  hide("change-phone-link");
}

/* ---------- نمای ۱: انتخاب فایل ---------- */
function bindUpload() {
  const input = $("file-input");
  const dz = $("dropzone");

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

  $("industry-select").addEventListener("change", validateUpload);
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

  if (state.fileUrl) URL.revokeObjectURL(state.fileUrl);
  state.fileUrl = URL.createObjectURL(file);

  const preview = $("preview");
  preview.src = state.fileUrl;
  preview.classList.remove("hidden");

  const dzText = document.querySelector("#dropzone .dz-text");
  if (dzText) dzText.textContent = "تغییر تصویر";

  clearAlert();
  validateUpload();
}

function validateUpload() {
  state.industryId = $("industry-select").value;
  $("btn-process").disabled = !(state.file && state.industryId) || state.analyzing;
}

/* ---------- دکمه‌ها ---------- */
function bindProcessButton() {
  $("btn-process").addEventListener("click", () => {
    clearAlert();
    if (state.isVerified) {
      runAnalysis();
    } else {
      state.pendingAnalysis = true;
      openModal();
    }
  });

  $("link-change-phone").addEventListener("click", (e) => {
    e.preventDefault();
    resetVerifiedState();
  });

  $("btn-new-analysis").addEventListener("click", resetForNewAnalysis);

  document.querySelectorAll(".tab-btn").forEach((b) =>
    b.addEventListener("click", () => setTab(b.dataset.tab))
  );
}

function resetForNewAnalysis() {
  state.file = null;
  state.requestId = null;
  state.analysis = null;
  state.questionsUsed = 0;

  $("file-input").value = "";
  if (state.fileUrl) URL.revokeObjectURL(state.fileUrl);
  state.fileUrl = null;

  const preview = $("preview");
  preview.removeAttribute("src");
  preview.classList.add("hidden");
  const thumb = $("result-thumb");
  thumb.removeAttribute("src");
  thumb.classList.add("hidden");

  const dzText = document.querySelector("#dropzone .dz-text");
  if (dzText) dzText.textContent = "برای انتخاب تصویر کلیک کنید یا فایل را اینجا رها کنید";

  $("result-box").innerHTML = "";
  renderChat([]);
  clearAlert();
  validateUpload();
  showView("upload");
}

/* ---------- مودال تأیید شماره ---------- */
let resendInterval = null;

function showPhoneStep() {
  $("modal-title").textContent = "تأیید شماره موبایل";
  show("modal-step-phone");
  hide("modal-step-otp");
  $("otp-input").value = "";
}

function showOtpStep() {
  $("modal-title").textContent = "وارد کردن کد تأیید";
  hide("modal-step-phone");
  show("modal-step-otp");
  $("otp-input").value = "";
  setTimeout(() => $("otp-input").focus(), 50);
}

function openModal() {
  $("auth-modal").classList.add("active");
  showPhoneStep();
  setModalError(null);
  $("phone-input").value = state.phone || "";
  setTimeout(() => $("phone-input").focus(), 50);
}

function closeModal() {
  $("auth-modal").classList.remove("active");
  setModalError(null);
  clearInterval(resendInterval);
  state.pendingAnalysis = false;
}

function startResendTimer(seconds = 60) {
  const btn = $("btn-resend-otp");
  clearInterval(resendInterval);
  let left = seconds;
  btn.disabled = true;
  btn.textContent = `ارسال مجدد کد (${left})`;
  resendInterval = setInterval(() => {
    left--;
    if (left <= 0) {
      clearInterval(resendInterval);
      btn.disabled = false;
      btn.textContent = "ارسال مجدد کد";
    } else {
      btn.textContent = `ارسال مجدد کد (${left})`;
    }
  }, 1000);
}

function bindModalActions() {
  $("modal-close-btn").addEventListener("click", closeModal);
  $("auth-modal").addEventListener("click", (e) => {
    if (e.target === $("auth-modal")) closeModal();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && $("auth-modal").classList.contains("active")) closeModal();
  });

  $("phone-input").addEventListener("keydown", (e) => { if (e.key === "Enter") $("btn-send-otp").click(); });
  $("otp-input").addEventListener("keydown", (e) => { if (e.key === "Enter") $("btn-verify-otp").click(); });
  $("otp-input").addEventListener("input", (e) => {
    e.target.value = normalizeDigits(e.target.value).replace(/\D/g, "");
  });

  // گام اول: ارسال کد
  $("btn-send-otp").addEventListener("click", async () => {
    const phone = normalizePhone($("phone-input").value);
    if (!phone) return setModalError("شماره موبایل معتبر نیست.");

    const btn = $("btn-send-otp");
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span>';
    setModalError(null);

    try {
      const res = await API.postJSON("/api/verification/request/", { phone });
      state.phone = res.phone || phone;
      $("display-phone").textContent = state.phone;
      showOtpStep();
      startResendTimer();
    } catch (e) {
      setModalError(e.message);
    } finally {
      btn.disabled = false;
      btn.textContent = "ارسال کد تأیید";
    }
  });

  // ارسال مجدد
  $("btn-resend-otp").addEventListener("click", async () => {
    const btn = $("btn-resend-otp");
    btn.disabled = true;
    try {
      await API.postJSON("/api/verification/request/", { phone: state.phone });
      setModalError(null);
      startResendTimer();
    } catch (e) {
      setModalError(e.message);
      btn.disabled = false;
    }
  });

  // بازگشت به گام شماره
  $("btn-back-phone").addEventListener("click", () => {
    clearInterval(resendInterval);
    setModalError(null);
    showPhoneStep();
    $("phone-input").value = state.phone || "";
    $("phone-input").focus();
  });

  // گام دوم: تأیید کد
  $("btn-verify-otp").addEventListener("click", async () => {
    const code = normalizeDigits($("otp-input").value).trim();
    if (!/^\d{4,6}$/.test(code)) return setModalError("کد تأیید معتبر نیست.");

    const btn = $("btn-verify-otp");
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span>';
    setModalError(null);

    try {
      await API.postJSON("/api/verification/verify/", { phone: state.phone, code });

      setVerified(state.phone);
      const shouldAnalyze = state.pendingAnalysis;
      closeModal();
      if (shouldAnalyze) runAnalysis(); // فقط بعد از تأیید بدون خطا
    } catch (e) {
      setModalError(e.message); // مودال باز می‌ماند، تصویر ارسال نمی‌شود
    } finally {
      btn.disabled = false;
      btn.textContent = "تأیید و ادامه";
    }
  });
}

/* ---------- تحلیل ---------- */
async function runAnalysis() {
  if (state.analyzing) return;
  state.analyzing = true;

  const form = new FormData();
  form.append("phone", state.phone);
  form.append("industry_id", state.industryId);
  form.append("image", state.file);
  form.append("request_id", crypto.randomUUID());

  const btn = $("btn-process");
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> در حال تحلیل...';

  try {
    const res = await API.postForm("/api/analysis/analyze/", form);
    state.analysis = res;
    state.requestId = res.request_id;
    state.questionsUsed = res.questions_used ?? 0;

    renderResult(res);
    renderChat([]);
    showView("result");
    setAlert("تحلیل با موفقیت انجام شد.", "success");
  } catch (e) {
    if (e.status === 401 || e.status === 403) {
      resetVerifiedState();
      state.pendingAnalysis = true;
      openModal();
    } else {
      setAlert(e.message);
    }
  } finally {
    state.analyzing = false;
    btn.innerHTML = '<i class="bi bi-lightning-charge-fill"></i> پردازش تصویر';
    validateUpload();
  }
}

/* ---------- رندر نتیجه ---------- */
function renderResult(r) {
  const thumb = $("result-thumb");
  if (state.fileUrl) {
    thumb.src = state.fileUrl;
    thumb.classList.remove("hidden");
  }

  const defects = (r.defects || []).map((d) => `
    <li class="defect-item">
      <strong>${escapeHTML(d.name)}</strong>
      <p>${escapeHTML(d.description || "")}</p>
      ${d.confidence != null ? `<small>میزان اطمینان: ${(d.confidence * 100).toFixed(0)}٪</small>` : ""}
    </li>
  `).join("");

  $("result-box").innerHTML = `
    <div class="result-head">
      <span class="badge">${escapeHTML(r.industry_name)}</span>
      <span class="badge ${r.status === "success" ? "success" : "failed"}">
        ${r.status === "success" ? "موفق" : escapeHTML(r.status)}
      </span>
    </div>
    <p class="summary">${escapeHTML(r.summary || "خلاصه‌ای بازنگشت.")}</p>
    <h3 class="section-title">عیوب احتمالی</h3>
    <ul class="defect-list">${defects || "<li class='defect-item'>عیب مشخصی گزارش نشد.</li>"}</ul>
    <p class="disclaimer">این تحلیل صرفاً ارزیابی اولیه و نمایشی است و جایگزین بازرسی صنعتی تأییدشده نیست.</p>
  `;
}

/* ---------- پرسش و پاسخ ---------- */
function msgHTML(m) {
  return `
    <div class="msg-avatar">${m.role === "user" ? '<i class="bi bi-person"></i>' : '<i class="bi bi-robot"></i>'}</div>
    <div class="msg-bubble">${escapeHTML(m.content)}</div>`;
}

function renderChat(messages) {
  $("chat").innerHTML = messages.map((m) => `<div class="msg ${m.role}">${msgHTML(m)}</div>`).join("");
  updateQaHint();
}

function appendMessage(m) {
  const chat = $("chat");
  const wrap = document.createElement("div");
  wrap.className = `msg ${m.role}`;
  wrap.innerHTML = msgHTML(m);
  chat.appendChild(wrap);
  chat.scrollTop = chat.scrollHeight;
}

function updateQaHint() {
  const remaining = Math.max(0, state.questionLimit - state.questionsUsed);
  $("qa-hint").textContent = remaining > 0
    ? `پرسش‌های باقی‌مانده برای این تصویر: ${remaining}`
    : `سقف ${state.questionLimit} پرسش برای این تصویر مصرف شده است.`;
  const disabled = remaining <= 0 || state.asking;
  $("btn-ask").disabled = disabled;
  $("question-input").disabled = remaining <= 0;
}

function bindQa() {
  const ask = async () => {
    const input = $("question-input");
    const q = input.value.trim();
    if (!q || state.asking || state.questionsUsed >= state.questionLimit) return;

    state.asking = true;
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
    } finally {
      state.asking = false;
      updateQaHint();
      if (state.questionsUsed < state.questionLimit) input.focus();
    }
  };

  $("btn-ask").addEventListener("click", ask);
  $("question-input").addEventListener("keydown", (e) => { if (e.key === "Enter") ask(); });
}

/* ---------- شروع ---------- */
document.addEventListener("DOMContentLoaded", () => {
  bootstrap();
  bindUpload();
  bindProcessButton();
  bindModalActions();
  bindQa();
  showView("upload");
});