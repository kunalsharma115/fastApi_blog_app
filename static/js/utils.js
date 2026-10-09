// Error message extraction from API responses
export function getErrorMessage(error) {
  if (!error) return "An error occurred. Please try again.";
  if (typeof error === "string") return error;
  if (typeof error.detail === "string") {
    return error.detail;
  } else if (Array.isArray(error.detail)) {
    return error.detail.map((err) => err.msg).join(". ");
  }
  if (typeof error.message === "string") {
    return error.message;
  }
  return "An error occurred. Please try again.";
}

// Show a Bootstrap modal by ID
export function showModal(modalId) {
  const element = document.getElementById(modalId);
  if (!element) return null;
  const modal = bootstrap.Modal.getOrCreateInstance(element);
  modal.show();
  return modal;
}

// Hide a Bootstrap modal by ID
export function hideModal(modalId) {
  const element = document.getElementById(modalId);
  if (!element) return;
  const modal = bootstrap.Modal.getInstance(element);
  if (modal) modal.hide();
}

// XSS prevention for dynamic content insertion
export function escapeHtml(text) {
  if (text === null || text === undefined) return "";
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

// Date formatting to match server's strftime("%B %d, %Y")
export function formatDate(dateString) {
  if (!dateString) return "";
  const date = new Date(dateString);
  if (isNaN(date.getTime())) return "";
  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "2-digit",
  });
}