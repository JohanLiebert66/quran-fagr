# daily-update.ps1 — توليد دفعة السور اليومية وتحديث الموقع المنشور
# يستأنف من أول سورة ناقصة (لا يستبدل القديم)، يتوقف تلقائيًا عند الحد اليومي المجاني،
# يحدّث صفحات التجميع، ثم ينشر الموقع على GitHub Pages.
# يشغّله Task Scheduler يوميًا؛ ويمكن تشغيله يدويًا في أي وقت.

$ErrorActionPreference = "Continue"
$py   = "C:\Users\alane\anaconda3\envs\quran-fagr\python.exe"
$proj = "C:\Hazem\1. Projects\Claude_WorkSpace\Brainstorm\projects\quran-fagr"

$logDir = Join-Path $proj "logs"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
$log = Join-Path $logDir ("daily-" + (Get-Date -Format "yyyy-MM-dd") + ".log")

Set-Location $proj
"==== $(Get-Date -Format 'yyyy-MM-dd HH:mm') START ====" | Tee-Object -FilePath $log -Append

# اسحب تحريرات الموقع من GitHub أولًا (محرّر الويب على الهاتف، إلخ)
git pull --rebase origin main 2>&1 | Tee-Object -FilePath $log -Append

& $py "scripts\contemplate.py"           | Tee-Object -FilePath $log -Append   # توليد أي سورة ناقصة (إن وُجدت)
& $py "scripts\contemplate.py" --upgrade | Tee-Object -FilePath $log -Append   # ترقية دفعة إلى التنسيق الغني (rich) حتى نفاد الحصة اليومية
& $py "scripts\aggregate.py"         | Tee-Object -FilePath $log -Append   # تحديث تجميع بلاغة/نحو
& $py "scripts\build_surah_index.py" | Tee-Object -FilePath $log -Append   # فهرس الملاحظات حسب السورة
& $py "scripts\build_khatmas.py"     | Tee-Object -FilePath $log -Append   # صفحات الختمات
& $py "scripts\build_whatsnew.py"    | Tee-Object -FilePath $log -Append   # صفحة الجديد
& $py "scripts\validate_quran.py"    | Tee-Object -FilePath $log -Append   # تحذير فقط — يفحص الاقتباسات

# سجّل التحديثات تلقائيًا وادفعها قبل النشر
git add -A 2>&1 | Tee-Object -FilePath $log -Append
$staged = (git diff --cached --name-only | Measure-Object).Count
if ($staged -gt 0) {
    git commit -m "daily $(Get-Date -Format 'yyyy-MM-dd')" 2>&1 | Tee-Object -FilePath $log -Append
    git push origin main 2>&1 | Tee-Object -FilePath $log -Append
} else {
    "(no changes to commit)" | Tee-Object -FilePath $log -Append
}

& $py -m mkdocs gh-deploy --remote-name origin | Tee-Object -FilePath $log -Append
"==== $(Get-Date -Format 'yyyy-MM-dd HH:mm') DONE ====" | Tee-Object -FilePath $log -Append
