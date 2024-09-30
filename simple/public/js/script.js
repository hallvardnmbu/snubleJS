document.getElementById("minVolume").addEventListener("change", function () {
  document.getElementById("volumeForm").submit();
});

function toggleVisibility(ids = []) {
  ids.forEach((id) => {
    const element = document.getElementById(id);
    element.style.display = element.style.display === "none" ? "block" : "none";
  });
}
