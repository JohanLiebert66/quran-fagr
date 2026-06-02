# -*- coding: utf-8 -*-
"""
ask.py — أرسل سؤالًا إلى Gemini واحصل على إجابة Markdown نظيفة لا تفقد تنسيقها عند النسخ.

افتراضيًا يستخدم `gemini-2.5-flash-lite` ليحافظ على حصة `gemini-2.5-flash` اليومية
المخصصة لتوليد السور.

الاستخدام:
    python ask.py "ما الفرق بين الرحمن والرحيم؟"
    python ask.py "..." > note.md                    # حفظ مباشرة
    python ask.py "..." | clip                        # نسخ إلى الحافظة (Windows)
    Get-Content question.txt | python ask.py          # تمرير سؤال طويل من ملف

تغيير النموذج:
    $env:ASK_MODEL = "gemini-2.5-flash"; python ask.py "..."
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ModuleNotFoundError:
    pass

from google import genai

MODEL = os.environ.get("ASK_MODEL", "gemini-2.5-flash-lite")

# تعليمة نظام بسيطة: اطلب Markdown نظيفًا بالعربية
SYSTEM_HINT = (
    "أجب بالعربية الفصحى وبصيغة Markdown نظيفة. "
    "استخدم **التشديد** للمفاهيم المحورية، و*الإفراد* للإشارات الجانبية، "
    "واقتبس الآيات في صناديق `> \"...\"`. اجعل العناوين بـ `##` فما دون."
)


def main() -> None:
    args = " ".join(sys.argv[1:]).strip()
    if not args:
        if sys.stdin.isatty():
            sys.exit(
                "الاستخدام: python ask.py \"سؤالك هنا\"\n"
                "أو مرّر السؤال من stdin:  Get-Content q.txt | python ask.py"
            )
        args = sys.stdin.read().strip()
    if not args:
        sys.exit("السؤال فارغ.")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        sys.exit("✗ ضع المفتاح في ملف .env (GEMINI_API_KEY=...)")

    client = genai.Client(api_key=api_key)
    resp = client.models.generate_content(
        model=MODEL,
        contents=f"{SYSTEM_HINT}\n\nالسؤال:\n{args}",
    )
    print((resp.text or "").rstrip())


if __name__ == "__main__":
    main()
