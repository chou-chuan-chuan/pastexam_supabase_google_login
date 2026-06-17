import { createClient } from "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm";
import {
  SUPABASE_URL,
  SUPABASE_PUBLISHABLE_KEY,
  STORAGE_BUCKET,
  MAX_FILE_SIZE_BYTES
} from "../config.js";

const configured =
  SUPABASE_URL.startsWith("https://") &&
  !SUPABASE_PUBLISHABLE_KEY.includes("PASTE_");

const supabase = configured
  ? createClient(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY)
  : null;

const $ = (selector) => document.querySelector(selector);

const el = {
  setupNotice: $("#setupNotice"),
  messageBox: $("#messageBox"),
  userLabel: $("#userLabel"),
  googleSignIn: $("#googleSignInButton"),
  signOut: $("#signOutButton"),
  openUpload: $("#openUploadButton"),
  adminPage: $("#adminPageLink"),

  uploadDialog: $("#uploadDialog"),
  uploadForm: $("#uploadForm"),
  course: $("#courseInput"),
  teacher: $("#teacherInput"),
  year: $("#yearInput"),
  semester: $("#semesterInput"),
  examType: $("#examTypeInput"),
  notes: $("#notesInput"),
  pdf: $("#pdfInput"),
  maxFileSizeLabel: $("#maxFileSizeLabel"),
  uploadProgress: $("#uploadProgress"),
  submitUpload: $("#submitUploadButton"),

  editDialog: $("#editDialog"),
  editForm: $("#editForm"),
  editCourse: $("#editCourseInput"),
  editTeacher: $("#editTeacherInput"),
  editYear: $("#editYearInput"),
  editSemester: $("#editSemesterInput"),
  editExamType: $("#editExamTypeInput"),
  editNotes: $("#editNotesInput"),
  editProgress: $("#editProgress"),
  saveEdit: $("#saveEditButton"),

  search: $("#searchInput"),
  typeFilter: $("#typeFilter"),
  yearFilter: $("#yearFilter"),
  clearFilters: $("#clearFiltersButton"),
  refresh: $("#refreshButton"),
  total: $("#totalCount"),
  listDescription: $("#listDescription"),
  loading: $("#loadingState"),
  grid: $("#examGrid"),
  empty: $("#emptyState"),

  previewDialog: $("#previewDialog"),
  previewTitle: $("#previewTitle"),
  previewFrame: $("#pdfPreviewFrame"),
  closePreview: $("#closePreviewButton"),
  closePreviewFooter: $("#closePreviewFooterButton"),
  openPdf: $("#openPdfButton"),
  downloadPdf: $("#downloadPdfButton")
};

let currentUser = null;
let isAdmin = false;
let exams = [];
let editingExamId = null;
let messageTimer;

function showMessage(text, kind = "info", timeout = 7000) {
  clearTimeout(messageTimer);
  el.messageBox.textContent = text;
  el.messageBox.className = `notice ${kind}`;

  if (timeout) {
    messageTimer = setTimeout(
      () => el.messageBox.classList.add("hidden"),
      timeout
    );
  }
}

function errorMessage(error, fallback) {
  console.error(error);
  return error?.message || fallback;
}

function safeFilename(name) {
  return (
    name
      .normalize("NFKD")
      .replace(/[^\w.\-]+/g, "_")
      .replace(/_+/g, "_") || "exam.pdf"
  );
}

function fileUrl(path) {
  return supabase.storage
    .from(STORAGE_BUCKET)
    .getPublicUrl(path).data.publicUrl;
}

function maximumFileSizeText() {
  const megabytes = MAX_FILE_SIZE_BYTES / (1024 * 1024);
  return `${Number.isInteger(megabytes) ? megabytes : megabytes.toFixed(1)} MB`;
}

function accountUI() {
  const signedIn = Boolean(currentUser);
  const displayName =
    currentUser?.user_metadata?.full_name || currentUser?.email;

  el.userLabel.textContent = signedIn
    ? displayName
    : "Browsing as guest";

  el.googleSignIn.classList.toggle("hidden", signedIn);
  el.signOut.classList.toggle("hidden", !signedIn);
  el.openUpload.disabled = !signedIn || !configured;
  el.adminPage.classList.toggle("hidden", !signedIn || !isAdmin);

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
  const years = [...new Set(exams.map((exam) => Number(exam.year)))]
    .filter(Number.isFinite)
    .sort((a, b) => b - a);

  el.yearFilter.innerHTML = '<option value="">All years</option>';

  for (const year of years) {
    const option = document.createElement("option");
    option.value = String(year);
    option.textContent = String(year);
    el.yearFilter.append(option);
  }

  if (years.map(String).includes(oldValue)) {
    el.yearFilter.value = oldValue;
  }
}

function matches(exam) {
  const query = el.search.value.trim().toLowerCase();
  const haystack = [
    exam.course,
    exam.teacher,
    exam.year,
    exam.semester,
    exam.exam_type,
    exam.notes,
    exam.original_filename
  ]
    .join(" ")
    .toLowerCase();

  return (
    (!query || haystack.includes(query)) &&
    (!el.typeFilter.value || exam.exam_type === el.typeFilter.value) &&
    (!el.yearFilter.value || String(exam.year) === el.yearFilter.value)
  );
}

function node(tag, className, text) {
  const item = document.createElement(tag);

  if (className) item.className = className;
  if (text !== undefined) item.textContent = text;

  return item;
}

function canEditPendingExam(exam) {
  return Boolean(
    currentUser &&
    exam.uploader_id === currentUser.id &&
    exam.status === "pending"
  );
}

function openPdfPreview(exam) {
  const url = fileUrl(exam.file_path);
  const title = exam.course || exam.original_filename || "Past exam";

  el.previewTitle.textContent = title;
  el.previewFrame.src = `${url}#view=FitH&toolbar=1&navpanes=0`;
  el.openPdf.href = url;
  el.downloadPdf.href = url;
  el.downloadPdf.setAttribute(
    "download",
    exam.original_filename || "exam.pdf"
  );

  el.previewDialog.showModal();
}

function closePdfPreview() {
  if (el.previewDialog.open) {
    el.previewDialog.close();
  }
}

function clearPdfPreview() {
  el.previewFrame.removeAttribute("src");
  el.openPdf.href = "#";
  el.downloadPdf.href = "#";
}

function openEditDialog(exam) {
  if (!canEditPendingExam(exam)) {
    showMessage(
      "You can only edit your own pending submission.",
      "error"
    );
    return;
  }

  editingExamId = exam.id;
  el.editCourse.value = exam.course || "";
  el.editTeacher.value = exam.teacher || "";
  el.editYear.value = exam.year || new Date().getFullYear();
  el.editSemester.value = exam.semester || "Spring";
  el.editExamType.value = exam.exam_type || "Other";
  el.editNotes.value = exam.notes || "";

  el.editDialog.showModal();
}

function examCard(exam) {
  const card = node("article", "exam-card");
  const top = node("div", "card-top");

  top.append(node("span", "badge type", exam.exam_type || "Other"));

  if (exam.status !== "approved") {
    top.append(node("span", "badge pending", "Pending review"));
  }

  card.append(
    top,
    node("h3", "", exam.course),
    node("p", "card-meta", exam.teacher || "No teacher listed"),
    node(
      "p",
      "card-meta",
      [exam.year, exam.semester].filter(Boolean).join(" · ")
    ),
    node("p", "card-notes", exam.notes || "No notes"),
    node("p", "filename", exam.original_filename || "exam.pdf")
  );

  const actions = node("div", "card-actions");
  const url = fileUrl(exam.file_path);

  const preview = node("button", "button primary", "Preview");
  preview.type = "button";
  preview.addEventListener("click", () => openPdfPreview(exam));

  const download = node("a", "button secondary", "Download");
  download.href = url;
  download.target = "_blank";
  download.rel = "noopener noreferrer";

  actions.append(preview, download);

  if (canEditPendingExam(exam)) {
    const edit = node(
      "button",
      "button secondary",
      "Edit information"
    );
    edit.type = "button";
    edit.addEventListener("click", () => openEditDialog(exam));

    const remove = node("button", "button danger", "Delete");
    remove.type = "button";
    remove.addEventListener("click", () => deletePending(exam));

    actions.append(edit, remove);
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
    el.empty.querySelector("p").textContent =
      "Paste your Supabase publishable key into config.js.";
    return;
  }

  setLoading(true);

  const { data, error } = await supabase
    .from("exams")
    .select(
      "id,course,teacher,year,semester,exam_type,notes,file_path,original_filename,uploader_id,status,created_at"
    )
    .order("year", { ascending: false })
    .order("created_at", { ascending: false });

  setLoading(false);

  if (error) {
    showMessage(
      errorMessage(error, "Could not load exams."),
      "error",
      0
    );
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

  if (error) {
    showMessage(
      errorMessage(error, "Could not read the session."),
      "error"
    );
  }

  currentUser = data?.session?.user || null;
}

async function refreshAdminAccess() {
  isAdmin = false;

  if (!currentUser || !configured) return;

  const { data, error } = await supabase.rpc("is_admin");

  // Keep the public archive working before optional admin SQL is installed.
  if (!error) {
    isAdmin = data === true;
  }
}

function appRedirectUrl() {
  // Preserves a GitHub Pages repository path such as /pastexam/.
  return new URL(".", window.location.href).href;
}

async function signInWithGoogle() {
  if (!configured) {
    showMessage(
      "Paste your Supabase publishable key into config.js first.",
      "error"
    );
    return;
  }

  el.googleSignIn.disabled = true;

  const { error } = await supabase.auth.signInWithOAuth({
    provider: "google",
    options: {
      redirectTo: appRedirectUrl()
    }
  });

  // Successful OAuth redirects the browser, so this normally runs on error.
  el.googleSignIn.disabled = false;

  if (error) {
    showMessage(
      errorMessage(error, "Could not start Google sign-in."),
      "error",
      0
    );
  }
}

async function signOut() {
  const { error } = await supabase.auth.signOut();

  if (error) {
    showMessage(
      errorMessage(error, "Could not sign out."),
      "error"
    );
    return;
  }

  showMessage("Signed out.", "success");
}

function uploadBusy(busy) {
  el.submitUpload.disabled = busy;
  el.uploadProgress.classList.toggle("hidden", !busy);

  el.uploadForm
    .querySelectorAll("input,select,textarea,button")
    .forEach((control) => {
      if (control !== el.submitUpload) {
        control.disabled = busy;
      }
    });
}

async function uploadExam(event) {
  event.preventDefault();

  if (!currentUser) {
    el.uploadDialog.close();
    await signInWithGoogle();
    return;
  }

  const file = el.pdf.files[0];

  if (!file) {
    showMessage("Choose a PDF file.", "error");
    return;
  }

  if (
    file.type !== "application/pdf" &&
    !file.name.toLowerCase().endsWith(".pdf")
  ) {
    showMessage("Only PDF files are allowed.", "error");
    return;
  }

  if (file.size > MAX_FILE_SIZE_BYTES) {
    showMessage(
      `The PDF is larger than ${maximumFileSizeText()}.`,
      "error"
    );
    return;
  }

  uploadBusy(true);

  const path = `${currentUser.id}/${Date.now()}-${crypto.randomUUID()}-${safeFilename(file.name)}`;

  const { error: storageError } = await supabase.storage
    .from(STORAGE_BUCKET)
    .upload(path, file, {
      contentType: "application/pdf",
      cacheControl: "3600",
      upsert: false
    });

  if (storageError) {
    uploadBusy(false);
    showMessage(
      errorMessage(storageError, "Could not upload the PDF."),
      "error"
    );
    return;
  }

  const { error: databaseError } = await supabase
    .from("exams")
    .insert({
      course: el.course.value.trim(),
      teacher: el.teacher.value.trim() || null,
      year: Number(el.year.value),
      semester: el.semester.value,
      exam_type: el.examType.value,
      notes: el.notes.value.trim() || null,
      file_path: path,
      original_filename: file.name,
      uploader_id: currentUser.id,
      status: "pending"
    });

  if (databaseError) {
    await supabase.storage.from(STORAGE_BUCKET).remove([path]);
    uploadBusy(false);
    showMessage(
      errorMessage(
        databaseError,
        "Could not save the exam information."
      ),
      "error",
      0
    );
    return;
  }

  uploadBusy(false);
  el.uploadForm.reset();
  el.year.value = new Date().getFullYear();
  el.uploadDialog.close();

  showMessage(
    "Upload complete. The exam is pending approval and visible to you.",
    "success",
    10000
  );

  await loadExams();
}

function editBusy(busy) {
  el.saveEdit.disabled = busy;
  el.editProgress.classList.toggle("hidden", !busy);

  el.editForm
    .querySelectorAll("input,select,textarea,button")
    .forEach((control) => {
      if (control !== el.saveEdit) {
        control.disabled = busy;
      }
    });
}

async function saveExamEdits(event) {
  event.preventDefault();

  if (!currentUser) {
    showMessage("You must sign in first.", "error");
    return;
  }

  if (!editingExamId) {
    showMessage("No exam was selected for editing.", "error");
    return;
  }

  const course = el.editCourse.value.trim();
  const year = Number(el.editYear.value);

  if (!course) {
    showMessage("Course name is required.", "error");
    return;
  }

  if (!Number.isInteger(year) || year < 1900 || year > 2100) {
    showMessage("Enter a valid year.", "error");
    return;
  }

  editBusy(true);

  const { error } = await supabase.rpc(
    "update_own_pending_exam",
    {
      p_exam_id: editingExamId,
      p_course: course,
      p_teacher: el.editTeacher.value.trim() || null,
      p_year: year,
      p_semester: el.editSemester.value || null,
      p_exam_type: el.editExamType.value || null,
      p_notes: el.editNotes.value.trim() || null
    }
  );

  editBusy(false);

  if (error) {
    showMessage(
      errorMessage(
        error,
        "Could not update the exam information."
      ),
      "error",
      0
    );
    return;
  }

  el.editDialog.close();
  showMessage(
    "Pending submission updated successfully.",
    "success"
  );

  await loadExams();
}

async function deletePending(exam) {
  if (!confirm(`Delete your pending submission “${exam.course}”?`)) {
    return;
  }

  const { error: storageError } = await supabase.storage
    .from(STORAGE_BUCKET)
    .remove([exam.file_path]);

  if (storageError) {
    showMessage(
      errorMessage(storageError, "Could not delete the PDF."),
      "error"
    );
    return;
  }

  const { error: databaseError } = await supabase
    .from("exams")
    .delete()
    .eq("id", exam.id);

  if (databaseError) {
    showMessage(
      errorMessage(
        databaseError,
        "PDF deleted, but the database row remains."
      ),
      "error",
      0
    );
    return;
  }

  showMessage("Pending submission deleted.", "success");
  await loadExams();
}

function showOAuthErrorFromUrl() {
  const params = new URLSearchParams(window.location.search);
  const error =
    params.get("error_description") || params.get("error");

  if (error) {
    showMessage(error, "error", 0);
  }
}

function bind() {
  el.googleSignIn.addEventListener("click", signInWithGoogle);
  el.openUpload.addEventListener("click", () => {
    if (currentUser) {
      el.uploadDialog.showModal();
    } else {
      signInWithGoogle();
    }
  });
  el.signOut.addEventListener("click", signOut);

  el.uploadForm.addEventListener("submit", uploadExam);
  el.editForm.addEventListener("submit", saveExamEdits);

  el.refresh.addEventListener("click", loadExams);

  el.closePreview.addEventListener("click", closePdfPreview);
  el.closePreviewFooter.addEventListener("click", closePdfPreview);
  el.previewDialog.addEventListener("close", clearPdfPreview);
  el.previewDialog.addEventListener("click", (event) => {
    if (event.target === el.previewDialog) {
      closePdfPreview();
    }
  });

  el.editDialog.addEventListener("close", () => {
    editingExamId = null;
    el.editForm.reset();
    editBusy(false);
  });

  document.querySelectorAll("[data-close]").forEach((button) => {
    button.addEventListener("click", () => {
      const dialog = document.getElementById(button.dataset.close);
      if (dialog?.open) dialog.close();
    });
  });

  [el.search, el.typeFilter, el.yearFilter].forEach((control) => {
    control.addEventListener("input", render);
    control.addEventListener("change", render);
  });

  el.clearFilters.addEventListener("click", () => {
    el.search.value = "";
    el.typeFilter.value = "";
    el.yearFilter.value = "";
    render();
  });
}

async function init() {
  bind();
  showOAuthErrorFromUrl();

  el.year.value = new Date().getFullYear();
  el.maxFileSizeLabel.textContent = maximumFileSizeText();

  if (!configured) {
    el.setupNotice.classList.remove("hidden");
    accountUI();
    await loadExams();
    return;
  }

  await getSession();
  await refreshAdminAccess();
  accountUI();
  await loadExams();

  supabase.auth.onAuthStateChange((_event, session) => {
    currentUser = session?.user || null;
    isAdmin = false;
    accountUI();

    setTimeout(async () => {
      await refreshAdminAccess();
      accountUI();
      await loadExams();
    }, 0);
  });
}

init();
