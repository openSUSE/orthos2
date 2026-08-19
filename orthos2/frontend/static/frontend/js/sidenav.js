(function () {
  "use strict";

  var LG_BREAKPOINT = 992;
  var STORAGE_KEY = "orthos2.sidenavCollapsed";
  var ADMIN_NAV_STORAGE_KEY = "orthos2.adminNavOpen";

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

    var adminNavToggle = document.querySelector('[href="#nav-administration"]');
    var adminNav = document.getElementById("nav-administration");
    if (adminNavToggle && adminNav) {
      var storedAdminNavOpen = localStorage.getItem(ADMIN_NAV_STORAGE_KEY);
      if (storedAdminNavOpen !== null) {
        var shouldBeOpen = storedAdminNavOpen === "true";
        adminNav.classList.toggle("show", shouldBeOpen);
        adminNavToggle.setAttribute("aria-expanded", String(shouldBeOpen));
      }

      adminNav.addEventListener("shown.bs.collapse", function () {
        localStorage.setItem(ADMIN_NAV_STORAGE_KEY, "true");
      });
      adminNav.addEventListener("hidden.bs.collapse", function () {
        localStorage.setItem(ADMIN_NAV_STORAGE_KEY, "false");
      });
    }
  });
})();
