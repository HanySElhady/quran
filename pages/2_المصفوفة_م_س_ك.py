import streamlit as st
import pandas as pd
import re
import os


# =========================
# إعداد الصفحة
# =========================
st.set_page_config(
    page_title="م س ك",
    page_icon="📖",
    layout="wide"
)


# =========================
# قراءة جميع ملفات القرآن
# =========================
@st.cache_data
def load_quran_all():

    rows = []

    for f in os.listdir("data"):

        if not f.endswith(".xlsx"):
            continue

        match = re.match(r"^(\d+)", f)

        if not match:
            continue

        surah_id = int(match.group(1))

        path = os.path.join("data", f)

        df = pd.read_excel(path)

        df["surah_id"] = surah_id

        surah_name = re.sub(r"^\d+[_\-]*", "", f)
        surah_name = re.sub(r"\.xlsx$", "", surah_name)

        df["surah_name"] = surah_name.strip()

        rows.append(df)

    if not rows:
        return pd.DataFrame()

    # ترتيب السور والآيات
    quran = pd.concat(rows, ignore_index=True)

    quran = quran.sort_values(
        ["surah_id", "ayah_number"]
    ).reset_index(drop=True)

    # =========================
    # الرقم التسلسلي للآية
    # من 1 إلى 6236
    # =========================
    quran["quran_ayah_number"] = range(
        1,
        len(quran) + 1
    )

    return quran


# =========================
# تحميل القرآن
# =========================
df = load_quran_all()


# =========================
# التحقق
# =========================
if df.empty:
    st.error("لم يتم العثور على ملفات القرآن داخل مجلد data")
    st.stop()


# =========================
# عرض جميع الآيات
# =========================

for _, r in df.iterrows():

    st.markdown(
        f"""
        <b>{r['quran_ayah_number']}-</b>
        {r['ayah_text']}
        <hr>
        """,
        unsafe_allow_html=True
    )