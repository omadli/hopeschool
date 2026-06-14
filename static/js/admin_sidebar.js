document.addEventListener("alpine:init", function () {
  window.Alpine.store("hsnav", {
    open: false,
    toggle() {
      this.open = !this.open;
    },
    close() {
      this.open = false;
    },
  });
});
