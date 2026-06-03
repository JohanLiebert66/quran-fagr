# -*- coding: utf-8 -*-
"""
contemplate.py — تدبر القرآن آليًا عبر Gemini API (الطبقة المجانية)

يمرّ على سور القرآن واحدة تلو الأخرى، يرسل نفس السؤال التدبري إلى Gemini،
ينتظر الرد كاملًا، ثم يحفظه في ملف Markdown مستقل لكل سورة (رقم + اسم).

التشغيل (PowerShell):
    $env:GEMINI_API_KEY = "ضع-مفتاحك-هنا"
    pip install -r requirements.txt
    python contemplate.py            # كل السور التي لم تُنجَز بعد (استئناف تلقائي)
    python contemplate.py 18         # سورة الكهف فقط
    python contemplate.py 1 10       # السور من 1 إلى 10
    python contemplate.py --force 2  # إعادة توليد سورة البقرة حتى لو وُجد ملفها

مفتاح مجاني من: https://aistudio.google.com/apikey
"""
from __future__ import annotations

import datetime
import os
import sys
import time
from pathlib import Path

from google import genai

from surahs import BY_NUMBER, SURAHS

# طباعة العربية في طرفية ويندوز دون أخطاء ترميز
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ───────────────────────── الإعدادات ─────────────────────────
MODEL = "gemini-3.5-flash"   # نموذج Flash الأحدث؛ بدّله بـ gemini-3.1-pro-preview لتحليل أعمق، أو gemini-flash-latest ليتبع الأحدث آليًا
SLEEP_BETWEEN = 5            # ثوانٍ بين الطلبات (الحد المجاني ~15 طلب/دقيقة)
MAX_RETRIES = 4

SCRIPTS_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPTS_DIR.parent
OUTPUT_DIR = PROJECT_DIR / "surahs" / "quran"   # قسم "تدبر السور" في الموقع
PROMPT_FILE = SCRIPTS_DIR / "prompt.md"

# تحميل المفتاح من ملف .env في جذر المشروع إن وُجد
try:
    from dotenv import load_dotenv

    load_dotenv(PROJECT_DIR / ".env")
except ModuleNotFoundError:
    pass


def slug(name: str) -> str:
    return name.replace(" ", "-")


def out_path(number: int, name: str) -> Path:
    return OUTPUT_DIR / f"{number:03d}-{slug(name)}.md"


class DailyQuotaExceeded(Exception):
    """بلوغ الحد اليومي المجاني — لا فائدة من إعادة المحاولة قبل الغد."""


def _is_daily_quota(exc: Exception) -> bool:
    """429 خاص بالحصة اليومية (PerDay) لا حصة الدقيقة — يُعرف من quotaId في رسالة الخطأ."""
    msg = str(exc)
    is_429 = getattr(exc, "code", None) == 429 or "429" in msg or "RESOURCE_EXHAUSTED" in msg
    return is_429 and "perday" in msg.lower()


def ask_gemini(client: genai.Client, prompt: str) -> str:
    delay = 10
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = client.models.generate_content(model=MODEL, contents=prompt)
            return (resp.text or "").strip()
        except Exception as exc:  # noqa: BLE001
            if _is_daily_quota(exc):
                raise DailyQuotaExceeded() from exc  # توقّف فورًا — الحد اليومي لا يتجدد بالانتظار
            if attempt == MAX_RETRIES:
                raise
            print(f"   ! خطأ مؤقت — إعادة المحاولة بعد {delay}s ({attempt}/{MAX_RETRIES})")
            time.sleep(delay)
            delay *= 2
    return ""


def save(number: int, name: str, body: str) -> Path:
    today = datetime.date.today().isoformat()
    frontmatter = (
        "---\n"
        f"surah: {number}\n"
        f"name: {name}\n"
        f"slug: {number:03d}-{slug(name)}\n"
        f"generated: {today}\n"
        f"model: {MODEL}\n"
        "---\n\n"
        f"# {number:03d} — سورة {name}\n\n"
    )
    # ملاحظة: لا نضع وسومًا عامة في frontmatter — كانت تتكرر في كل سورة فتفسد فهرس الوسوم.
    # الوسوم تُكتب يدويًا في صفحات مشاركات الفجر، أو يُستخدم البحث للعثور على سورة بعينها.
    path = out_path(number, name)
    path.write_text(frontmatter + body + "\n", encoding="utf-8")
    return path


def parse_args(argv: list[str]) -> tuple[list[int], bool]:
    force = "--force" in argv
    nums = [a for a in argv if a.lstrip("-").isdigit()]
    if not nums:
        targets = [n for n, _ in SURAHS]
    elif len(nums) == 1:
        targets = [int(nums[0])]
    else:
        lo, hi = int(nums[0]), int(nums[1])
        targets = list(range(lo, hi + 1))
    return targets, force


def main() -> None:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        sys.exit('✗ ضع المفتاح أولًا:  $env:GEMINI_API_KEY = "..."  (مجانًا من aistudio.google.com/apikey)')

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    template = PROMPT_FILE.read_text(encoding="utf-8")
    client = genai.Client(api_key=api_key)
    targets, force = parse_args(sys.argv[1:])

    done = skipped = failed = 0
    stopped = None  # "quota" أو "interrupt"
    try:
        for number in targets:
            name = BY_NUMBER.get(number)
            if name is None:
                print(f"… تخطّي رقم غير صالح: {number}")
                continue
            path = out_path(number, name)
            if path.exists() and not force:
                print(f"[skip] {number:03d} {name} — موجود (استخدم --force لإعادة التوليد)")
                skipped += 1
                continue
            print(f"[ask ] {number:03d} {name} — أسأل Gemini…")
            try:
                body = ask_gemini(client, template.format(number=number, name=name))
            except DailyQuotaExceeded:
                stopped = "quota"
                break
            except Exception as exc:  # noqa: BLE001
                print(f"   ✗ فشل بعد كل المحاولات: {exc}")
                failed += 1
                continue
            if not body:
                print("   ✗ رد فارغ — تخطّي")
                failed += 1
                continue
            save(number, name, body)
            print(f"   ✓ حُفظ في {path.name} ({len(body)} حرف)")
            done += 1
            time.sleep(SLEEP_BETWEEN)
    except KeyboardInterrupt:
        stopped = "interrupt"

    print(f"\nانتهى — حُفظ {done}، تُخطّي {skipped}، فشل {failed}.")
    if stopped == "quota":
        print("⏸  بلغتَ الحد اليومي المجاني (≈20 طلب/يوم لـ gemini-2.5-flash). توقّفت فورًا.")
        print("   الملفات المُنجزة محفوظة — أعد تشغيل نفس الأمر لاحقًا وسيُكمل تلقائيًا من أول سورة ناقصة.")
    elif stopped == "interrupt":
        print("⏸  أوقفتَ التشغيل يدويًا — أعد تشغيل نفس الأمر للمتابعة من حيث توقفت.")


if __name__ == "__main__":
    main()
