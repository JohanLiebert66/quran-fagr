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
& $py "scripts\contemplate.py"  | Tee-Object -FilePath $log -Append   # ~20 سورة/يوم ثم يتوقف
& $py "scripts\aggregate.py"    | Tee-Object -FilePath $log -Append   # تحديث تجميع بلاغة/نحو
& $py -m mkdocs gh-deploy --remote-name origin | Tee-Object -FilePath $log -Append
"==== $(Get-Date -Format 'yyyy-MM-dd HH:mm') DONE ====" | Tee-Object -FilePath $log -Append
