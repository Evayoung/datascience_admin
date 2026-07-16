let deferredInstallPrompt = null;

function installButtons() {
  return Array.from(document.querySelectorAll("[data-install-app]"));
}

function setInstallButtonState(label, disabled = false) {
  installButtons().forEach((button) => {
    button.disabled = disabled;
    button.title = label;
    const text = button.querySelector("span");
    if (text) text.textContent = label;
  });
}

window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  deferredInstallPrompt = event;
  setInstallButtonState("Install App");
});

window.addEventListener("appinstalled", () => {
  deferredInstallPrompt = null;
  setInstallButtonState("Installed", true);
});

function showInstallToast(message) {
  const container = document.getElementById("toast-container");
  if (!container) {
    window.alert(message);
    return;
  }
  const toastHtml = `
    <div class="toast align-items-center text-bg-info border-0" role="alert" aria-live="assertive" aria-atomic="true" data-bs-autohide="true" data-bs-delay="5000">
      <div class="toast-header">
        <strong class="me-auto">Install App</strong>
        <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
      </div>
      <div class="toast-body">${message}</div>
    </div>
  `;
  const temp = document.createElement("div");
  temp.innerHTML = toastHtml;
  const toast = temp.querySelector(".toast");
  if (toast) {
    container.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    toast.addEventListener("hidden.bs.toast", () => toast.remove());
  }
}

document.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-install-app]");
  if (!button) return;

  if (!deferredInstallPrompt) {
    showInstallToast("Use your browser menu to install this admin app on this device.");
    return;
  }

  deferredInstallPrompt.prompt();
  await deferredInstallPrompt.userChoice;
  deferredInstallPrompt = null;
});
