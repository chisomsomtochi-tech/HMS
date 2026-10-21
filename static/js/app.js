(function () {
  "use strict";

  /* Mobile sidebar -------------------------------------------------------- */
  const sidebar = document.querySelector("[data-sidebar]");
  const overlay = document.querySelector("[data-sidebar-overlay]");

  function openSidebar() {
    if (!sidebar || !overlay) return;
    sidebar.classList.remove("-translate-x-full");
    overlay.classList.remove("hidden");
    document.body.classList.add("overflow-hidden");
  }

  function closeSidebar() {
    if (!sidebar || !overlay) return;
    sidebar.classList.add("-translate-x-full");
    overlay.classList.add("hidden");
    document.body.classList.remove("overflow-hidden");
  }

  document.querySelectorAll("[data-sidebar-toggle]").forEach(function (button) {
    button.addEventListener("click", openSidebar);
  });

  if (overlay) {
    overlay.addEventListener("click", closeSidebar);
  }

  window.addEventListener("keydown", function (event) {
    if (event.key === "Escape") closeSidebar();
  });

  if (sidebar) {
    sidebar.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", closeSidebar);
    });
  }

  /* Toasts ---------------------------------------------------------------- */
  function dismissToast(toast) {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(-4px)";
    window.setTimeout(function () {
      toast.remove();
    }, 200);
  }

  document.querySelectorAll("[data-toast]").forEach(function (toast) {
    window.setTimeout(function () {
      dismissToast(toast);
    }, 6000);

    const close = toast.querySelector("[data-toast-close]");
    if (close) {
      close.addEventListener("click", function () {
        dismissToast(toast);
      });
    }
  });

  /* Password reveal toggles ---------------------------------------------- */
  document.querySelectorAll("[data-password-toggle]").forEach(function (button) {
    const input = document.getElementById(button.getAttribute("data-password-toggle"));
    if (!input) return;

    button.addEventListener("click", function () {
      const reveal = input.type === "password";
      input.type = reveal ? "text" : "password";
      button.setAttribute("aria-pressed", reveal ? "true" : "false");
      button.setAttribute("aria-label", reveal ? "Hide password" : "Show password");

      const showIcon = button.querySelector('[data-icon="show"]');
      const hideIcon = button.querySelector('[data-icon="hide"]');
      if (showIcon) showIcon.classList.toggle("hidden", reveal);
      if (hideIcon) hideIcon.classList.toggle("hidden", !reveal);
    });
  });

  /* Auto-submit filters --------------------------------------------------- */
  document.querySelectorAll("[data-auto-submit]").forEach(function (element) {
    element.addEventListener("change", function () {
      if (element.form) {
        if (element.form.requestSubmit) {
          element.form.requestSubmit();
        } else {
          element.form.submit();
        }
      }
    });
  });

  /* Copy refraction into the prescription -------------------------------- */
  const refractionFields = [
    "sph_od",
    "cyl_od",
    "axis_od",
    "add_od",
    "sph_os",
    "cyl_os",
    "axis_os",
    "add_os",
    "pd",
  ];

  document.querySelectorAll("[data-copy-refraction]").forEach(function (button) {
    button.addEventListener("click", function () {
      let copied = 0;
      refractionFields.forEach(function (name) {
        const source = document.getElementById("id_exam-" + name);
        const target = document.getElementById("id_rx-" + name);
        if (source && target && source.value !== "") {
          target.value = source.value;
          copied += 1;
        }
      });

      const status = document.getElementById("copy-rx-status");
      if (status) {
        status.textContent = copied
          ? "Copied " + copied + " value" + (copied === 1 ? "" : "s") + " from the refraction."
          : "Enter refraction values first, then copy them across.";
        status.classList.remove("hidden");
        window.setTimeout(function () {
          status.classList.add("hidden");
        }, 4000);
      }
    });
  });

  /* Close the global search pane on outside click ------------------------- */
  document.addEventListener("click", function (event) {
    if (!event.target.closest("[data-patient-search]")) {
      const results = document.getElementById("global-search-results");
      if (results) results.innerHTML = "";
    }
  });
})();
