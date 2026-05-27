/** Sticky header shadow after scroll (index, faq, webflow). */
(function () {
  var header = document.getElementById("site-header");
  if (!header) return;
  function onScroll() {
    header.classList.toggle("is-scrolled", window.scrollY > 8);
  }
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });
})();
