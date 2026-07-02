(function () {
    const frame = document.getElementById("pageFrame");
    const navItems = Array.from(document.querySelectorAll(".nav-item"));

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

    function switchPage(button) {
        navItems.forEach((item) => item.classList.toggle("active", item === button));
        frame.src = button.dataset.target;
    }

    navItems.forEach((button) => {
        button.addEventListener("click", () => switchPage(button));
    });

    frame.addEventListener("load", sharePywebviewWithFrame);
    window.addEventListener("pywebviewready", sharePywebviewWithFrame);
})();
