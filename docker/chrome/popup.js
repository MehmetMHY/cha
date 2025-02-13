document.addEventListener("DOMContentLoaded", () => {
  const iframe = document.getElementById("my-iframe");
  const srcUrl = `http://localhost:8080/`;
  iframe.src = srcUrl;
});
