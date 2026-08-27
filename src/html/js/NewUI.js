(function () {
    const frame = document.getElementById("pageFrame");
    const navItems = Array.from(document.querySelectorAll(".nav-item"));
    const debugButton = document.querySelector(".nav-debug");

    function sharePywebviewWithFrame() {
        try {
            if (frame.contentWindow && window.pywebview) {
                frame.contentWindow.pywebview = window.pywebview;
                frame.contentWindow.dispatchEvent(new Event("pywebviewready"));
            }
        } catch (error) {
            console.warn("Unable to share pywebview with frame", error);
        }
    }

    function syncFrameLanguage() {
        try {
            if (frame.contentWindow && frame.contentWindow.MouseEngineI18n) {
                frame.contentWindow.MouseEngineI18n.load();
            }
        } catch (error) {
            console.warn("Unable to sync language with frame", error);
        }
    }

    function switchPage(button) {
        navItems.forEach((item) => item.classList.toggle("active", item === button));
        frame.src = button.dataset.target;
    }

    async function initDebugNav() {
        if (!debugButton || !window.pywebview || !window.pywebview.api) {
            return;
        }
        try {
            const enabled = await window.pywebview.api.is_debug_enabled();
            debugButton.style.display = enabled ? "" : "none";
        } catch (error) {
            console.warn("Unable to check debug state", error);
            debugButton.style.display = "none";
        }
    }

    navItems.forEach((button) => {
        button.addEventListener("click", () => switchPage(button));
    });

    frame.addEventListener("load", () => {
        sharePywebviewWithFrame();
        syncFrameLanguage();
    });
    window.addEventListener("pywebviewready", () => {
        sharePywebviewWithFrame();
        initDebugNav();
    });
    window.addEventListener("mouseengine-language-applied", syncFrameLanguage);
    window.addEventListener("load", initDebugNav);
})();
