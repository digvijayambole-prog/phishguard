document.addEventListener("DOMContentLoaded", () => {
  const resultTitle = document.getElementById("resultTitle");
  if (resultTitle) resultTitle.focus();

  const form = document.getElementById("analyzeForm");
  if (!form) return;

  const input = document.getElementById("url");
  const button = document.getElementById("analyzeButton");
  const loading = document.getElementById("loading");
  const error = document.getElementById("urlError");

  // The server's own message is shown under the field; put the cursor back in the box.
  if (error.textContent.trim()) input.focus();

  // Returning with the Back button must not leave the form locked.
  window.addEventListener("pageshow", (event) => {
    if (event.persisted) {
      button.disabled = false;
      button.removeAttribute("aria-disabled");
      loading.hidden = true;
    }
  });

  // All validation happens on the server so users always see its wording.
  form.addEventListener("submit", () => {
    error.textContent = "";
    button.disabled = true;
    button.setAttribute("aria-disabled", "true");
    loading.hidden = false;
  });
});
