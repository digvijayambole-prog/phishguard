document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("analyzeForm");
  if (!form) return;

  const input = document.getElementById("url");
  const button = document.getElementById("analyzeButton");
  const loading = document.getElementById("loading");
  const error = document.getElementById("urlError");

  form.addEventListener("submit", (event) => {
    error.textContent = "";
    const value = input.value.trim();

    if (!value) {
      event.preventDefault();
      error.textContent = "Please enter a complete website URL.";
      input.focus();
      return;
    }

    if (!/^https?:\/\/.+/i.test(value)) {
      event.preventDefault();
      error.textContent = "Please enter a complete website URL.";
      input.focus();
      return;
    }

    button.disabled = true;
    button.setAttribute("aria-disabled", "true");
    loading.hidden = false;
  });
});
