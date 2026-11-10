// Fade out success/info flash messages after a few seconds.
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".alert-success, .alert-info").forEach((el) => {
    setTimeout(() => {
      const instance = bootstrap.Alert.getOrCreateInstance(el);
      instance.close();
    }, 5000);
  });
});
