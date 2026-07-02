(function () {
    let adopted = false;

    function adoptParentApi() {
        try {
            if (!window.pywebview && window.parent && window.parent !== window && window.parent.pywebview) {
                window.pywebview = window.parent.pywebview;
                adopted = true;
                window.dispatchEvent(new Event("pywebviewready"));
            }
        } catch (error) {
        }
    }

    adoptParentApi();
    window.addEventListener("pywebviewready", adoptParentApi);

    const startedAt = Date.now();
    const timer = window.setInterval(() => {
        adoptParentApi();
        if (adopted || Date.now() - startedAt > 5000) {
            window.clearInterval(timer);
        }
    }, 50);
})();
