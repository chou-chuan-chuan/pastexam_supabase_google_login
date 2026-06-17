import { createClient } from "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm";
import { SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, STORAGE_BUCKET, MAX_FILE_SIZE_BYTES } from "../config.js";

const configured = SUPABASE_URL.startsWith("https://") && !SUPABASE_PUBLISHABLE_KEY.includes("PASTE_");
const supabase = configured ? createClient(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY) : null;
const $ = (selector) => document.querySelector(selector);

const el = {
  setupNotice: $("#setupNotice"), messageBox: $("#messageBox"), userLabel: $("#userLabel"),
  googleSignIn: $("#googleSignInButton"), signOut: $("#signOutButton"), openUpload: $("#openUploadButton"),
  uploadDialog: $("#uploadDialog"), uploadForm: $("#uploadForm"), course: $("#courseInput"),
  teacher: $("#teacherInput"), year: $("#yearInput"), semester: $("#semesterInput"),
  examType: $("#examTypeInput"), notes: $("#notesInput"), pdf: $("#pdfInput"),
  uploadProgress: $("#uploadProgress"), submitUpload: $("#submitUploadButton"),
  search: $("#searchInput"), typeFilter: $("#typeFilter"), yearFilter: $("#yearFilter"),
  clearFilters: $("#clearFiltersButton"), refresh: $("#refreshButton"), total: $("#totalCount"),
  listDescription: $("#listDescription"), loading: $("#loadingState"), grid: $("#examGrid"),
  empty: $("#emptyState"),
  previewDialog: $("#previewDialog"), previewTitle: $("#previewTitle"),
  previewFrame: $("#pdfPreviewFrame"), closePreview: $("#closePreviewButton"),
  closePreviewFooter: $("#closePreviewFooterButton"), openPdf: $("#openPdfButton"),
  downloadPdf: $("#downloadPdfButton")
};

let currentUser = null;
let exams = [];
let messageTimer;

function showMessage(text, kind = "info", timeout = 7000) {
  clearTimeout(messageTimer);
  el.messageBox.textContent = text;
  el.messageBox.className = `notice ${kind}`;
  if (timeout) messageTimer = setTimeout(() => el.messageBox.classList.add("hidden"), timeout);
}

function errorMessage(error, fallback) {
  console.error(error);
  return error?.message || fallback;
}

function safeFilename(name) {
  return name.normalize("NFKD").replace(/[^\w.\-]+/g, "_").replace(/_+/g, "_") || "exam.pdf";
}

function fileUrl(path) {
  return supabase.storage.from(STORAGE_BUCKET).getPublicUrl(path).data.publicUrl;
}

function accountUI() {
  const signedIn = Boolean(currentUser);
  const displayName = currentUser?.user_metadata?.full_name || currentUser?.email;
  el.userLabel.textContent = signedIn ? displayName : "Browsing as guest";
  el.googleSignIn.classList.toggle("hidden", signedIn);
  el.signOut.classList.toggle("hidden", !signedIn);
  el.openUpload.disabled = !signedIn || !configured;
  el.listDescription.textContent = signedIn
    ? "Showing approved exams and your own pending submissions."
    : "Showing approved exams. Sign in with Google to upload.";
}

function setLoading(loading) {
  el.loading.classList.toggle("hidden", !loading);
  if (loading) {
    el.grid.classList.add("hidden");
    el.empty.classList.add("hidden");
  }
}

function rebuildYearFilter() {
  const oldValue = el.yearFilter.value;
  const years = [...new Set(exams.map((exam) => Number(exam.year)))].filter(Number.isFinite).sort((a, b) => b - a);
  el.yearFilter.innerHTML = '<option value="">All years</option>';
  for (const year of years) {
    const option = document.createElement("option");
    option.value = String(year);
    option.textContent = String(year);
    el.yearFilter.append(option);
  }
  if (years.map(String).includes(oldValue)) el.yearFilter.value = oldValue;
}

function matches(exam) {
  const query = el.search.value.trim().toLowerCase();
  const haystack = [exam.course, exam.teacher, exam.year, exam.semester, exam.exam_type, exam.notes, exam.original_filename]
    .join(" ").toLowerCase();
  return (!query || haystack.includes(query))
    && (!el.typeFilter.value || exam.exam_type === el.typeFilter.value)
    && (!el.yearFilter.value || String(exam.year) === el.yearFilter.value);
}

function node(tag, className, text) {
  const item = document.createElement(tag);
  if (className) item.className = className;
  if (text !== undefined) item.textContent = text;
  return item;
}

function openPdfPreview(exam) {
  const url = fileUrl(exam.file_path);
  const title = exam.course || exam.original_filename || "Past exam";

  el.previewTitle.textContent = title;
  el.previewFrame.src = `${url}#view=FitH&toolbar=1&navpanes=0`;
  el.openPdf.href = url;
  el.downloadPdf.href = url;
  el.downloadPdf.setAttribute("download", exam.original_filename || "exam.pdf");
  el.previewDialog.showModal();
}

function closePdfPreview() {
  if (el.previewDialog.open) el.previewDialog.close();
}

function clearPdfPreview() {
  el.previewFrame.removeAttribute("src");
  el.openPdf.href = "#";
  el.downloadPdf.href = "#";
}

function examCard(exam) {
  const card = node("article", "exam-card");
  const top = node("div", "card-top");
  top.append(node("span", "badge type", exam.exam_type || "Other"));
  if (exam.status !== "approved") top.append(node("span", "badge pending", "Pending review"));

  card.append(
    top,
    node("h3", "", exam.course),
    node("p", "card-meta", exam.teacher || "No teacher listed"),
    node("p", "card-meta", [exam.year, exam.semester].filter(Boolean).join(" · ")),
    node("p", "card-notes", exam.notes || "No notes"),
    node("p", "filename", exam.original_filename || "exam.pdf")
  );

  const actions = node("div", "card-actions");
  const url = fileUrl(exam.file_path);
  const preview = node("button", "button primary", "Preview");
  preview.type = "button";
  preview.addEventListener("click", () => openPdfPreview(exam));
  const download = node("a", "button secondary", "Download");
  download.href = url; download.target = "_blank"; download.rel = "noopener noreferrer";
  actions.append(preview, download);

  if (currentUser && exam.uploader_id === currentUser.id && exam.status === "pending") {
    const remove = node("button", "button danger", "Delete");
    remove.type = "button";
    remove.addEventListener("click", () => deletePending(exam));
    actions.append(remove);
  }
  card.append(actions);
  return card;
}

function render() {
  const visible = exams.filter(matches);
  el.grid.replaceChildren(...visible.map(examCard));
  el.total.textContent = String(visible.length);
  el.grid.classList.toggle("hidden", visible.length === 0);
  el.empty.classList.toggle("hidden", visible.length !== 0);
}

async function loadExams() {
  if (!configured) {
    setLoading(false);
    el.empty.classList.remove("hidden");
    el.empty.querySelector("h2").textContent = "Setup required";
    el.empty.querySelector("p").textContent = "Paste your Supabase publishable key into config.js.";
    return;
  }
  setLoading(true);
  const { data, error } = await supabase.from("exams")
    .select("id,course,teacher,year,semester,exam_type,notes,file_path,original_filename,uploader_id,status,created_at")
    .order("year", { ascending: false }).order("created_at", { ascending: false });
  setLoading(false);
  if (error) {
    showMessage(errorMessage(error, "Could not load exams."), "error", 0);
    el.empty.classList.remove("hidden");
    return;
  }
  exams = data || [];
  rebuildYearFilter();
  render();
}

async function getSession() {
  if (!configured) return;
  const { data, error } = await supabase.auth.getSession();
  if (error) showMessage(errorMessage(error, "Could not read the session."), "error");
  currentUser = data?.session?.user || null;
  accountUI();
}

function appRedirectUrl() {
  // Preserves a GitHub Pages repository path such as /pastexam/.
  return new URL(".", window.location.href).href;
}

async function signInWithGoogle() {
  if (!configured) {
    showMessage("Paste your Supabase publishable key into config.js first.", "error");
    return;
  }

  el.googleSignIn.disabled = true;
  const { error } = await supabase.auth.signInWithOAuth({
    provider: "google",
    options: {
      redirectTo: appRedirectUrl()
    }
  });

  // A successful call redirects the browser, so this normally runs only on error.
  el.googleSignIn.disabled = false;
  if (error) showMessage(errorMessage(error, "Could not start Google sign-in."), "error", 0);
}

async function signOut() {
  const { error } = await supabase.auth.signOut();
  if (error) return showMessage(errorMessage(error, "Could not sign out."), "error");
  showMessage("Signed out.", "success");
}

function uploadBusy(busy) {
  el.submitUpload.disabled = busy;
  el.uploadProgress.classList.toggle("hidden", !busy);
  el.uploadForm.querySelectorAll("input,select,textarea,button").forEach((control) => {
    if (control !== el.submitUpload) control.disabled = busy;
  });
}

async function uploadExam(event) {
  event.preventDefault();
  if (!currentUser) {
    el.uploadDialog.close();
    return signInWithGoogle();
  }
  const file = el.pdf.files[0];
  if (!file) return showMessage("Choose a PDF file.", "error");
  if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf"))
    return showMessage("Only PDF files are allowed.", "error");
  if (file.size > MAX_FILE_SIZE_BYTES) return showMessage("The PDF is larger than 20 MB.", "error");

  uploadBusy(true);
  const path = `${currentUser.id}/${Date.now()}-${crypto.randomUUID()}-${safeFilename(file.name)}`;
  const { error: storageError } = await supabase.storage.from(STORAGE_BUCKET).upload(path, file, {
    contentType: "application/pdf", cacheControl: "3600", upsert: false
  });
  if (storageError) {
    uploadBusy(false); return showMessage(errorMessage(storageError, "Could not upload the PDF."), "error");
  }

  const { error: databaseError } = await supabase.from("exams").insert({
    course: el.course.value.trim(), teacher: el.teacher.value.trim() || null,
    year: Number(el.year.value), semester: el.semester.value, exam_type: el.examType.value,
    notes: el.notes.value.trim() || null, file_path: path, original_filename: file.name,
    uploader_id: currentUser.id, status: "pending"
  });
  if (databaseError) {
    await supabase.storage.from(STORAGE_BUCKET).remove([path]);
    uploadBusy(false);
    return showMessage(errorMessage(databaseError, "Could not save the exam information."), "error", 0);
  }

  uploadBusy(false); el.uploadForm.reset(); el.year.value = new Date().getFullYear(); el.uploadDialog.close();
  showMessage("Upload complete. The exam is pending approval and visible to you.", "success", 10000);
  await loadExams();
}

async function deletePending(exam) {
  if (!confirm(`Delete your pending submission “${exam.course}”?`)) return;
  const { error: storageError } = await supabase.storage.from(STORAGE_BUCKET).remove([exam.file_path]);
  if (storageError) return showMessage(errorMessage(storageError, "Could not delete the PDF."), "error");
  const { error: databaseError } = await supabase.from("exams").delete().eq("id", exam.id);
  if (databaseError) return showMessage(errorMessage(databaseError, "PDF deleted, but the database row remains."), "error", 0);
  showMessage("Pending submission deleted.", "success");
  await loadExams();
}

function showOAuthErrorFromUrl() {
  const params = new URLSearchParams(window.location.search);
  const error = params.get("error_description") || params.get("error");
  if (error) showMessage(error, "error", 0);
}

function bind() {
  el.googleSignIn.addEventListener("click", signInWithGoogle);
  el.openUpload.addEventListener("click", () => currentUser ? el.uploadDialog.showModal() : signInWithGoogle());
  el.signOut.addEventListener("click", signOut);
  el.uploadForm.addEventListener("submit", uploadExam);
  el.refresh.addEventListener("click", loadExams);
  el.closePreview.addEventListener("click", closePdfPreview);
  el.closePreviewFooter.addEventListener("click", closePdfPreview);
  el.previewDialog.addEventListener("close", clearPdfPreview);
  el.previewDialog.addEventListener("click", (event) => {
    if (event.target === el.previewDialog) closePdfPreview();
  });
  document.querySelectorAll("[data-close]").forEach((button) => button.addEventListener("click", () => document.getElementById(button.dataset.close).close()));
  [el.search, el.typeFilter, el.yearFilter].forEach((control) => { control.addEventListener("input", render); control.addEventListener("change", render); });
  el.clearFilters.addEventListener("click", () => { el.search.value = ""; el.typeFilter.value = ""; el.yearFilter.value = ""; render(); });
}

async function init() {
  bind();
  showOAuthErrorFromUrl();
  el.year.value = new Date().getFullYear();
  if (!configured) { el.setupNotice.classList.remove("hidden"); accountUI(); return loadExams(); }
  await getSession();
  await loadExams();
  supabase.auth.onAuthStateChange((_event, session) => {
    currentUser = session?.user || null;
    accountUI();
    setTimeout(loadExams, 0);
  });
}

init();
