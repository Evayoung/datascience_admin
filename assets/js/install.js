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

document.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-install-app]");
  if (!button) return;

  if (!deferredInstallPrompt) {
    window.alert("Use your browser menu to install this admin app on this device.");
    return;
  }

  deferredInstallPrompt.prompt();
  await deferredInstallPrompt.userChoice;
  deferredInstallPrompt = null;
});
