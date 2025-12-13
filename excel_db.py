# -*- coding: utf-8 -*-

import re
import pandas as pd

SURAH_ID = 2
SURAH_NAME = "البقرة"

with open("data/baqara.txt", "r", encoding="utf-8") as f:
    text = f.read().strip()

parts = re.split(r"\((\d+)\)", text)

rows = []

# ✅ الآية الأولى (قبل رقم 1)
first_ayah_text = parts[0].strip()
if first_ayah_text:
    rows.append({
        "surah_id": SURAH_ID,
        "surah_name": SURAH_NAME,
        "ayah_number": 1,
        "ayah_text": first_ayah_text
    })

# ✅ باقي الآيات
for i in range(2, len(parts) - 1, 2):
    ayah_number = int(parts[i - 1])
    ayah_text = parts[i].strip()

    if ayah_text:  # منع الصفوف الفاضية
        rows.append({
            "surah_id": SURAH_ID,
            "surah_name": SURAH_NAME,
            "ayah_number": ayah_number,
            "ayah_text": ayah_text
        })

df = pd.DataFrame(rows)

# ترتيب احترازي
df = df.sort_values("ayah_number").reset_index(drop=True)

# تحقق
print("عدد الآيات:", len(df))
print(df.head())
print(df.tail())

df.to_excel("surat_al_baqara.xlsx", index=False)

print("تم إنشاء الملف بالترتيب الصحيح")
