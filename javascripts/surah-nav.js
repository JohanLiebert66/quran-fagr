/* surah-nav.js — تحسين التنقل التلقائي بين الآيات والسور على الأجهزة الذكية:
   1. عند فتح القائمة الجانبية داخل أي سورة، يظهر «جدول المحتويات» (عناوين الآيات) تلقائياً دون الحاجة للتمرير أو الضغط على السهم.
   2. عند ضغط زر الرجوع في القائمة للعودة إلى قائمة الـ 114 سورة، يتم تمرير القائمة تلقائياً لموقع السورة الحالية.
   3. عند اختيار أي آية من جدول المحتويات، تُغلق القائمة تلقائياً ويتم الانتقال للآية بسلاسة.
   4. دعم التوافق التام مع نمط التصفح الفوري (navigation.instant).
*/
(function () {
  function setupSurahNav() {
    var drawer = document.getElementById("__drawer");
    var toc = document.getElementById("__toc");
    var isMobile = function () {
      return window.innerWidth < 1220; // نقطة انكسار شريط التنقل في ثيم Material
    };

    if (!toc) return;

    // التحقق من وجود عناصر داخل جدول المحتويات
    var tocNav = document.querySelector(".md-nav--secondary");
    var hasTocItems = tocNav && tocNav.querySelectorAll(".md-nav__link").length > 0;
    if (!hasTocItems) return;

    // 1. فتح جدول المحتويات تلقائياً على الجوال
    function autoExpandToc() {
      if (isMobile()) {
        toc.checked = true;
      }
    }

    // تطبيق أولي عند تحميل الصفحة
    autoExpandToc();

    // 2. عند فتح القائمة الجانبية (drawer)
    if (drawer) {
      drawer.addEventListener("change", function () {
        if (drawer.checked) {
          autoExpandToc();
        }
      });
    }

    // 3. التمرير التلقائي للسورة الحالية عند الرجوع لقائمة السور
    var tocTitleLabel = document.querySelector('label.md-nav__title[for="__toc"]');
    if (tocTitleLabel) {
      tocTitleLabel.addEventListener("click", function () {
        setTimeout(function () {
          var activeSurah = document.querySelector(".md-sidebar--primary .md-nav__item--active");
          if (activeSurah) {
            activeSurah.scrollIntoView({ block: "center", behavior: "smooth" });
          }
        }, 150);
      });
    }

    // 4. إغلاق القائمة تلقائياً عند النقر على رابط آية
    var tocLinks = tocNav.querySelectorAll("a.md-nav__link");
    tocLinks.forEach(function (link) {
      link.addEventListener("click", function () {
        if (drawer && isMobile()) {
          drawer.checked = false;
        }
      });
    });
  }

  // دعم التحميل العادي والتصفح الفوري (Material instant navigation)
  if (typeof document$ !== "undefined") {
    document$.subscribe(setupSurahNav);
  } else {
    if (document.readyState !== "loading") {
      setupSurahNav();
    } else {
      document.addEventListener("DOMContentLoaded", setupSurahNav);
    }
  }
})();
