(function () {
  "use strict";

  var LG_BREAKPOINT = 992;
  var STORAGE_KEY = "orthos2.sidenavCollapsed";

  document.addEventListener("DOMContentLoaded", function () {
    var toggles = document.querySelectorAll(".sidenav-toggle");
    var sidenav = document.getElementById("sidenav");
    if (toggles.length && sidenav) {
      toggles.forEach(function (toggle) {
        toggle.addEventListener("click", function () {
          if (window.innerWidth < LG_BREAKPOINT) {
            bootstrap.Offcanvas.getOrCreateInstance(sidenav).toggle();
            return;
          }

          var collapsed = document.documentElement.classList.toggle("sidenav-collapsed");
          localStorage.setItem(STORAGE_KEY, collapsed);
        });
      });
    }

    document.querySelectorAll('#sidenav [data-bs-toggle="collapse"]').forEach(function (navToggle) {
      var targetId = navToggle.getAttribute("href");
      var navGroup = targetId && document.querySelector(targetId);
      if (!navGroup) {
        return;
      }

      var storageKey = "orthos2.navOpen." + targetId.slice(1);
      var storedOpen = localStorage.getItem(storageKey);
      if (storedOpen !== null) {
        var shouldBeOpen = storedOpen === "true";
        navGroup.classList.toggle("show", shouldBeOpen);
        navToggle.setAttribute("aria-expanded", String(shouldBeOpen));
      }

      navGroup.addEventListener("shown.bs.collapse", function () {
        localStorage.setItem(storageKey, "true");
      });
      navGroup.addEventListener("hidden.bs.collapse", function () {
        localStorage.setItem(storageKey, "false");
      });
    });
  });
})();
