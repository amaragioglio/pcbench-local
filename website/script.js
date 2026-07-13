// ===== Barra superior: fondo al hacer scroll =====
const topbar = document.getElementById("topbar");

function updateTopbar() {
  topbar.classList.toggle("scrolled", window.scrollY > 40);
}

updateTopbar();
window.addEventListener("scroll", updateTopbar, { passive: true });

// ===== Menú móvil =====
const navToggle = document.getElementById("navToggle");
const topnav = document.getElementById("topnav");

navToggle.addEventListener("click", () => {
  const open = topnav.classList.toggle("open");
  navToggle.setAttribute("aria-expanded", String(open));
  if (open) topbar.classList.add("scrolled");
  else updateTopbar();
});

topnav.querySelectorAll("a").forEach((link) => {
  link.addEventListener("click", () => {
    topnav.classList.remove("open");
    navToggle.setAttribute("aria-expanded", "false");
    updateTopbar();
  });
});

// ===== Aparición suave al hacer scroll =====
const revealTargets = document.querySelectorAll(
  ".reveal, .atlas-row, .interlude, .pullquote, .facts, .feature-head .container, .article .narrow"
);

const revealObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("visible");
        revealObserver.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.08 }
);

revealTargets.forEach((el) => {
  el.classList.add("reveal");
  revealObserver.observe(el);
});

// ===== Captura de leads =====
// Fase smoke test: sin backend, el envío abre un correo pre-llenado.
// Para medir conversión real, sustituir por un endpoint de Formspree/Tally:
//   fetch('https://formspree.io/f/TU_ID', { method: 'POST', body: new FormData(form) })
const leadForm = document.getElementById("leadForm");

if (leadForm) {
  leadForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const email = leadForm.querySelector("input[name=email]").value;
    const subject = encodeURIComponent("Join la lista — Orígenes Coffee");
    const body = encodeURIComponent(
      `I want in!\n\nMy email: ${email}\nMy origin (country): `
    );
    window.location.href = `mailto:andresmaragiogliop@gmail.com?subject=${subject}&body=${body}`;
    const button = leadForm.querySelector("button");
    button.textContent = "¡Gracias!";
    setTimeout(() => (button.textContent = "I want in"), 4000);
  });
}

// ===== Año del pie =====
document.getElementById("year").textContent = new Date().getFullYear();
