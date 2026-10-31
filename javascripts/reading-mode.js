/* وضع القراءة — زرّ عائم يبدّل تنسيق الصفحة إلى عرضٍ مركّز للتأمل:
   نصّ أكبر، عمود أضيق، وإخفاء أشرطة التنقّل. التفضيل يُحفظ في localStorage. */
(function () {
  var KEY = "qf-reading-mode";

  function init() {
    if (document.querySelector(".reading-toggle")) return; // تفادي التكرار

    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "reading-toggle md-icon";
    btn.setAttribute("aria-label", "وضع القراءة");
    btn.textContent = "📖";

    function apply(on) {
      document.body.classList.toggle("reading-mode", on);
      btn.classList.toggle("is-on", on);
      btn.title = on ? "إنهاء وضع القراءة" : "وضع القراءة";
      btn.setAttribute("aria-pressed", on ? "true" : "false");
    }

    btn.addEventListener("click", function () {
      var on = !document.body.classList.contains("reading-mode");
      try { localStorage.setItem(KEY, on ? "1" : "0"); } catch (e) {}
      apply(on);
    });

    document.body.appendChild(btn);
    var saved = "0";
    try { saved = localStorage.getItem(KEY) || "0"; } catch (e) {}
    apply(saved === "1");
  }

  if (document.readyState !== "loading") init();
  else document.addEventListener("DOMContentLoaded", init);
})();
