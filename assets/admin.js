import { createClient } from "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm";
import { SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, STORAGE_BUCKET } from "../config.js";
import {
  SUPABASE_CLIENT_OPTIONS,
  cleanOAuthCallbackFromBrowser,
  oauthRedirectUrl,
  parseOAuthResponse,
  verifyGoogleAuthConfiguration
} from "./auth.js";

const configured = SUPABASE_URL.startsWith("https://") && !SUPABASE_PUBLISHABLE_KEY.includes("PASTE_");
const supabase = configured
  ? createClient(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, SUPABASE_CLIENT_OPTIONS)
  : null;
const $ = (selector) => document.querySelector(selector);

const el = {
  setupNotice: $("#adminSetupNotice"),
  messageBox: $("#adminMessageBox"),
  userLabel: $("#adminUserLabel"),
  headerSignIn: $("#adminGoogleSignInButton"),
  panelSignIn: $("#adminPanelSignInButton"),
  signOut: $("#adminSignOutButton"),
  deniedSignOut: $("#adminDeniedSignOutButton"),
  signedOutState: $("#adminSignedOutState"),
  deniedState: $("#adminDeniedState"),
  deniedDescription: $("#adminDeniedDescription"),
  dashboard: $("#adminDashboard"),
  search: $("#adminSearchInput"),
  statusFilter: $("#adminStatusFilter"),
  refresh: $("#adminRefreshButton"),
  listDescription: $("#adminListDescription"),
  loading: $("#adminLoadingState"),
  grid: $("#adminExamGrid"),
  empty: $("#adminEmptyState"),
  pendingCount: $("#pendingCount"),
  approvedCount: $("#approvedCount"),
  rejectedCount: $("#rejectedCount"),
  previewDialog: $("#adminPreviewDialog"),
  previewTitle: $("#adminPreviewTitle"),
  previewFrame: $("#adminPdfPreviewFrame"),
  closePreview: $("#adminClosePreviewButton"),
  closePreviewFooter: $("#adminClosePreviewFooterButton"),
  openPdf: $("#adminOpenPdfButton"),
  downloadPdf: $("#adminDownloadPdfButton")
};

let currentUser = null;
let isAdmin = false;
let exams = [];
let messageTimer;
let authQueue = Promise.resolve();
let appliedAuthUserId;

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

function node(tag, className, text) {
  const item = document.createElement(tag);
  if (className) item.className = className;
  if (text !== undefined) item.textContent = text;
  return item;
}

function fileUrl(path) {
  return supabase.storage.from(STORAGE_BUCKET).getPublicUrl(path).data.publicUrl;
}

function formatDate(value) {
  if (!value) return "Unknown date";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Unknown date";
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(date);
}

function updateAccessUI() {
  const signedIn = Boolean(currentUser);
  const name = currentUser?.user_metadata?.full_name || currentUser?.email || "Signed-in user";
  el.userLabel.textContent = signedIn ? name : "Not signed in";
  el.headerSignIn.classList.toggle("hidden", signedIn);
  el.signOut.classList.toggle("hidden", !signedIn);
  el.signedOutState.classList.toggle("hidden", signedIn);
  el.deniedState.classList.toggle("hidden", !signedIn || isAdmin);
  el.dashboard.classList.toggle("hidden", !signedIn || !isAdmin);

  if (signedIn && !isAdmin) {
    el.deniedDescription.textContent = `${currentUser.email || "This account"} is signed in, but it is not listed in public.admin_users.`;
  }
}

function setLoading(loading) {
  el.loading.classList.toggle("hidden", !loading);
  if (loading) {
    el.grid.classList.add("hidden");
    el.empty.classList.add("hidden");
  }
}

function updateCounts() {
  const count = (status) => exams.filter((exam) => exam.status === status).length;
  el.pendingCount.textContent = String(count("pending"));
  el.approvedCount.textContent = String(count("approved"));
  el.rejectedCount.textContent = String(count("rejected"));
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
    exam.original_filename,
    exam.uploader_id,
    exam.status
  ].join(" ").toLowerCase();
  return (!query || haystack.includes(query))
    && (!el.statusFilter.value || exam.status === el.statusFilter.value);
}

function statusLabel(status) {
  if (status === "approved") return "Approved";
  if (status === "rejected") return "Rejected";
  return "Pending";
}

function openPdfPreview(exam) {
  const url = fileUrl(exam.file_path);
  el.previewTitle.textContent = exam.course || exam.original_filename || "Past exam";
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

function actionButton(text, className, handler) {
  const button = node("button", `button ${className}`, text);
  button.type = "button";
  button.addEventListener("click", handler);
  return button;
}

function adminExamCard(exam) {
  const card = node("article", "admin-exam-card");
  const content = node("div", "admin-card-content");
  const top = node("div", "card-top");
  top.append(
    node("span", "badge type", exam.exam_type || "Other"),
    node("span", `badge status-${exam.status || "pending"}`, statusLabel(exam.status))
  );

  const details = node("dl", "admin-details");
  const addDetail = (term, value) => {
    details.append(node("dt", "", term), node("dd", "", value || "—"));
  };
  addDetail("Teacher", exam.teacher || "No teacher listed");
  addDetail("Term", [exam.year, exam.semester].filter(Boolean).join(" · "));
  addDetail("Uploaded", formatDate(exam.created_at));
  addDetail("Uploader ID", exam.uploader_id || "Unknown");
  if (exam.reviewed_at) addDetail("Last reviewed", formatDate(exam.reviewed_at));

  content.append(
    top,
    node("h3", "", exam.course || "Untitled exam"),
    details,
    node("p", "card-notes", exam.notes || "No notes"),
    node("p", "filename", exam.original_filename || "exam.pdf")
  );

  const actions = node("div", "admin-card-actions");
  actions.append(actionButton("Preview PDF", "primary", () => openPdfPreview(exam)));

  if (exam.status !== "approved") {
    actions.append(actionButton("Approve", "success", () => changeStatus(exam, "approved")));
  }
  if (exam.status !== "rejected") {
    actions.append(actionButton("Reject", "warning", () => changeStatus(exam, "rejected")));
  }
  if (exam.status !== "pending") {
    actions.append(actionButton("Return to pending", "secondary", () => changeStatus(exam, "pending")));
  }
  actions.append(actionButton("Delete permanently", "danger", () => deleteExam(exam)));

  card.append(content, actions);
  return card;
}

function render() {
  const visible = exams.filter(matches);
  el.grid.replaceChildren(...visible.map(adminExamCard));
  el.grid.classList.toggle("hidden", visible.length === 0);
  el.empty.classList.toggle("hidden", visible.length !== 0);

  const status = el.statusFilter.value;
  el.listDescription.textContent = status
    ? `Showing ${statusLabel(status).toLowerCase()} submissions (${visible.length}).`
    : `Showing all submissions (${visible.length}).`;
}

async function checkAdminAccess() {
  isAdmin = false;
  if (!currentUser || !configured) return false;

  const { data, error } = await supabase.rpc("is_admin");
  if (error) {
    showMessage(
      errorMessage(error, "Could not verify administrator access."),
      "error",
      0
    );
    return false;
  }
  isAdmin = data === true;
  return isAdmin;
}

async function loadExams() {
  if (!isAdmin) return;
  setLoading(true);
  const { data, error } = await supabase.from("exams")
    .select("id,course,teacher,year,semester,exam_type,notes,file_path,original_filename,uploader_id,status,created_at,reviewed_at,reviewed_by")
    .order("created_at", { ascending: false });
  setLoading(false);

  if (error) {
    showMessage(errorMessage(error, "Could not load submissions."), "error", 0);
    el.empty.classList.remove("hidden");
    return;
  }

  exams = data || [];
  updateCounts();
  render();
}

async function changeStatus(exam, status) {
  const verb = status === "approved" ? "approve" : status === "rejected" ? "reject" : "return to pending";
  if (!confirm(`Are you sure you want to ${verb} “${exam.course}”?`)) return;

  const { error } = await supabase.from("exams")
    .update({
      status,
      reviewed_at: new Date().toISOString(),
      reviewed_by: currentUser.id
    })
    .eq("id", exam.id);

  if (error) return showMessage(errorMessage(error, `Could not ${verb} this submission.`), "error", 0);
  showMessage(`Submission marked ${status}.`, "success");
  await loadExams();
}

async function deleteExam(exam) {
  const confirmed = confirm(
    `Permanently delete “${exam.course}”?\n\nThis removes both the PDF and its database record and cannot be undone.`
  );
  if (!confirmed) return;

  const { error: storageError } = await supabase.storage.from(STORAGE_BUCKET).remove([exam.file_path]);
  if (storageError) {
    return showMessage(errorMessage(storageError, "Could not delete the PDF from Storage."), "error", 0);
  }

  const { error: databaseError } = await supabase.from("exams").delete().eq("id", exam.id);
  if (databaseError) {
    return showMessage(
      errorMessage(databaseError, "The PDF was deleted, but its database record could not be removed."),
      "error",
      0
    );
  }

  showMessage("Submission and PDF deleted.", "success");
  await loadExams();
}

async function signInWithGoogle() {
  if (!configured) {
    showMessage("Keep your configured config.js in the project root.", "error", 0);
    return;
  }

  el.headerSignIn.disabled = true;
  el.panelSignIn.disabled = true;

  try {
    await verifyGoogleAuthConfiguration(
      SUPABASE_URL,
      SUPABASE_PUBLISHABLE_KEY
    );

    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: oauthRedirectUrl(window.location.href, "admin")
      }
    });

    if (error) throw error;
  } catch (error) {
    showMessage(errorMessage(error, "Could not start Google sign-in."), "error", 0);
  } finally {
    el.headerSignIn.disabled = false;
    el.panelSignIn.disabled = false;
  }
}

async function signOut() {
  if (!configured) return;
  const { error } = await supabase.auth.signOut({ scope: "local" });
  if (error) return showMessage(errorMessage(error, "Could not sign out."), "error");
  await queueAuthSession(null, "SIGNED_OUT");
  showMessage("Signed out.", "success");
}

async function applySession(session) {
  currentUser = session?.user || null;
  isAdmin = false;
  if (currentUser) await checkAdminAccess();
  updateAccessUI();
  if (isAdmin) {
    await loadExams();
  } else {
    exams = [];
    updateCounts();
    render();
  }
}

function queueAuthSession(session, event) {
  authQueue = authQueue
    .catch((error) => {
      console.error(error);
    })
    .then(async () => {
      const userId = session?.user?.id || null;

      if (userId === appliedAuthUserId && event !== "USER_UPDATED") {
        currentUser = session?.user || null;
        updateAccessUI();
        return;
      }

      await applySession(session);
      appliedAuthUserId = userId;
    });

  return authQueue;
}

function bind() {
  el.headerSignIn.addEventListener("click", signInWithGoogle);
  el.panelSignIn.addEventListener("click", signInWithGoogle);
  el.signOut.addEventListener("click", signOut);
  el.deniedSignOut.addEventListener("click", signOut);
  el.refresh.addEventListener("click", loadExams);
  el.search.addEventListener("input", render);
  el.statusFilter.addEventListener("change", render);
  el.closePreview.addEventListener("click", closePdfPreview);
  el.closePreviewFooter.addEventListener("click", closePdfPreview);
  el.previewDialog.addEventListener("close", clearPdfPreview);
  el.previewDialog.addEventListener("click", (event) => {
    if (event.target === el.previewDialog) closePdfPreview();
  });
}

async function init() {
  bind();
  if (!configured) {
    el.setupNotice.classList.remove("hidden");
    updateAccessUI();
    return;
  }

  const oauthResponse = parseOAuthResponse(window.location.href);
  supabase.auth.onAuthStateChange((event, session) => {
    setTimeout(() => void queueAuthSession(session, event), 0);
  });

  const { data, error } = await supabase.auth.getSession();
  await queueAuthSession(data?.session || null, "GET_SESSION");

  cleanOAuthCallbackFromBrowser();

  if (oauthResponse.error) {
    showMessage(oauthResponse.error, "error", 0);
  } else if (error) {
    showMessage(errorMessage(error, "Could not read the session."), "error", 0);
  }
}

init();
