// ===== Header: fondo al hacer scroll =====
const header = document.getElementById("siteHeader");

function updateHeader() {
  header.classList.toggle("scrolled", window.scrollY > 40);
}

updateHeader();
window.addEventListener("scroll", updateHeader, { passive: true });

// ===== Menú móvil =====
const navToggle = document.getElementById("navToggle");
const navLinks = document.getElementById("navLinks");

navToggle.addEventListener("click", () => {
  const open = navLinks.classList.toggle("open");
  navToggle.setAttribute("aria-expanded", String(open));
  if (open) header.classList.add("scrolled");
  else updateHeader();
});

navLinks.querySelectorAll("a").forEach((link) => {
  link.addEventListener("click", () => {
    navLinks.classList.remove("open");
    navToggle.setAttribute("aria-expanded", "false");
    updateHeader();
  });
});

// ===== Aparición suave al hacer scroll =====
const revealTargets = document.querySelectorAll(
  ".section-title, .kicker, .editorial-text, .editorial-media, .step, .card, .story, .visit-grid > *, .section-intro"
);
revealTargets.forEach((el) => el.classList.add("reveal"));

const revealObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry, i) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("visible");
        revealObserver.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.12 }
);

revealTargets.forEach((el, i) => {
  el.style.transitionDelay = `${(i % 4) * 80}ms`;
  revealObserver.observe(el);
});

// ===== Año del footer =====
document.getElementById("year").textContent = new Date().getFullYear();
