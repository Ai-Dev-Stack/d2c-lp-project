/* スムーズスクロール補助、追従CTA、フォームバリデーション、法務モーダル */

(function () {
  const header = document.querySelector(".site-header");
  const fv = document.getElementById("fv");
  const stickyCta = document.getElementById("sticky-cta");
  const form = document.getElementById("trial-form");
  const thanks = document.getElementById("thanks");
  const ctaSection = document.getElementById("cta");

  function headerOffset() {
    return header ? header.getBoundingClientRect().height : 0;
  }

  document.querySelectorAll('a[href^="#"]').forEach(function (link) {
    link.addEventListener("click", function (event) {
      const id = link.getAttribute("href").slice(1);
      const target = document.getElementById(id);
      if (!target) return;
      event.preventDefault();
      const top = window.scrollY + target.getBoundingClientRect().top - headerOffset() - 8;
      window.scrollTo({ top: Math.max(0, top), behavior: "smooth" });
    });
  });

  function updateStickyCta() {
    if (!stickyCta || !fv || !ctaSection) return;
    if (window.matchMedia("(min-width: 768px)").matches) {
      stickyCta.hidden = true;
      return;
    }
    const fvBottom = fv.getBoundingClientRect().bottom;
    const ctaTop = ctaSection.getBoundingClientRect().top;
    const pastFv = fvBottom < headerOffset();
    const ctaVisible = ctaTop < window.innerHeight * 0.7;
    stickyCta.hidden = !(pastFv && !ctaVisible);
  }

  window.addEventListener("scroll", updateStickyCta, { passive: true });
  window.addEventListener("resize", updateStickyCta);
  updateStickyCta();

  function showError(name, message) {
    const el = form.querySelector('[data-error-for="' + name + '"]');
    if (!el) return;
    el.textContent = message;
    el.hidden = !message;
  }

  function isEmail(value) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
  }

  if (form) {
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      const name = form.name.value.trim();
      const email = form.email.value.trim();
      const agree = form.agree.checked;
      let valid = true;

      if (!name) {
        showError("name", "お名前を入力してください。");
        valid = false;
      } else {
        showError("name", "");
      }

      if (!email) {
        showError("email", "メールアドレスを入力してください。");
        valid = false;
      } else if (!isEmail(email)) {
        showError("email", "メールアドレスの形式を確認してください。");
        valid = false;
      } else {
        showError("email", "");
      }

      if (!agree) {
        showError("agree", "同意へのチェックが必要です。");
        valid = false;
      } else {
        showError("agree", "");
      }

      if (!valid) return;

      form.classList.add("is-hidden");
      thanks.hidden = false;
      stickyCta.hidden = true;
      thanks.focus?.();
    });
  }

  document.querySelectorAll("[data-modal]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const dialog = document.getElementById("modal-" + btn.getAttribute("data-modal"));
      if (dialog && typeof dialog.showModal === "function") {
        dialog.showModal();
      }
    });
  });

  document.querySelectorAll("[data-close-modal]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const dialog = btn.closest("dialog");
      if (dialog) dialog.close();
    });
  });
})();
