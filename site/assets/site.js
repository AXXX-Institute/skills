(function () {
  function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text);
    }
    return new Promise(function (resolve, reject) {
      var textarea = document.createElement("textarea");
      textarea.value = text;
      textarea.style.position = "fixed";
      textarea.style.opacity = "0";
      document.body.appendChild(textarea);
      textarea.focus();
      textarea.select();
      try { document.execCommand("copy"); resolve(); } catch (error) { reject(error); }
      document.body.removeChild(textarea);
    });
  }

  document.querySelectorAll("pre").forEach(function (pre) {
    var button = document.createElement("button");
    button.type = "button";
    button.className = "copy-btn";
    button.textContent = "Copy";
    button.addEventListener("click", function () {
      var code = pre.querySelector("code");
      var text = (code ? code.textContent : pre.textContent).replace(/\s+$/, "");
      copyText(text).then(function () {
        button.textContent = "Copied";
        button.classList.add("ok");
        setTimeout(function () {
          button.textContent = "Copy";
          button.classList.remove("ok");
        }, 1400);
      }).catch(function () {});
    });
    pre.appendChild(button);
  });

  document.querySelectorAll(".flip").forEach(function (button) {
    button.addEventListener("click", function () {
      var deck = button.closest(".deck");
      var active = deck.classList.toggle("show");
      var label = button.querySelector(".lbl");
      var icon = button.querySelector(".ic");
      button.setAttribute("aria-expanded", active ? "true" : "false");
      if (label) { label.textContent = active ? "Back" : "Without"; }
      if (icon) { icon.textContent = active ? "↩" : "⚠"; }
    });
  });
})();
