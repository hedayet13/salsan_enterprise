// Small helper to auto-hide flashes
setTimeout(() => {
  document.querySelectorAll('.flash').forEach(el => el.style.display='none');
}, 5000);
document.addEventListener('click', (e) => {
  if (e.target.classList.contains('thumb')) {
    const main = document.getElementById('main-photo');
    if (main) main.src = e.target.src;
  }
});