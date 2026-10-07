import streamlit as st
import pandas as pd
import re
import os
import math
from PIL import Image


# =========================================================
# إعداد الصفحة
# =========================================================

st.set_page_config(
    page_title="مصفوفة م س ك (R G B)",
    page_icon="📖",
    layout="wide"
)


# =========================================================
# صورة العنوان
# =========================================================

try:
    header_img = Image.open("assets/header.png")
    st.image(header_img, use_container_width=True)
except:
    pass


# =========================================================
# قراءة جميع ملفات القرآن
# =========================================================

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

        # اسم السورة
        surah_name = re.sub(r"^\d+[_\-]*", "", f)
        surah_name = re.sub(r"\.xlsx$", "", surah_name)

        df["surah_name"] = surah_name.strip()

        rows.append(df)

    if not rows:
        return pd.DataFrame()

    # تجميع جميع السور
    quran = pd.concat(
        rows,
        ignore_index=True
    )

    # ترتيب السور ثم الآيات
    quran = quran.sort_values(
        ["surah_id", "ayah_number"]
    ).reset_index(drop=True)

    # =====================================================
    # الرقم التسلسلي للآية في القرآن كله
    # =====================================================

    quran["quran_ayah_number"] = range(
        1,
        len(quran) + 1
    )

    return quran


# =========================================================
# تحميل القرآن
# =========================================================

df = load_quran_all()


# =========================================================
# التحقق من وجود البيانات
# =========================================================

if df.empty:

    st.error(
        "لم يتم العثور على ملفات القرآن داخل مجلد data"
    )

    st.stop()


# =========================================================
# إعدادات المصفوفة
# =========================================================

TOTAL_AYAT = 6236
TOTAL_HOURS = 2400

CONSTANT = TOTAL_AYAT / TOTAL_HOURS


# =========================================================
# السنة الهجرية الحالية
# =========================================================
# اليوم 7 أكتوبر 2026 = 1448 هـ في مصر
# =========================================================

CURRENT_HIJRI_YEAR = 1448


# =========================================================
# إدخال السنة الهجرية
# =========================================================

st.markdown("### 📅 أدخل السنة الهجرية")


hijri_input = st.text_input(
    "السنة الهجرية",
    placeholder="مثال: 1395",
    key="hijri_year_input"
)


# =========================================================
# التحقق من السنة
# =========================================================

if hijri_input:

    # التأكد أن المدخل رقم صحيح
    if not hijri_input.isdigit():

        st.error(
            "⚠️ من فضلك أدخل السنة الهجرية كرقم صحيح."
        )

        st.stop()


    hijri_year = int(hijri_input)


    # =====================================================
    # التأكد من أن السنة داخل النطاق
    # =====================================================

    if hijri_year < 1:

        st.error(
            "⚠️ السنة الهجرية يجب أن تبدأ من 1 هـ."
        )

        st.stop()


    if hijri_year > CURRENT_HIJRI_YEAR:

        st.error(
            f"⚠️ لا يمكن البحث في سنوات غيبية. "
            f"السنة المدخلة {hijri_year} هـ أكبر من السنة الحالية "
            f"{CURRENT_HIJRI_YEAR} هـ."
        )

        st.stop()


    # =====================================================
    # الحساب
    # =====================================================

    multiplication_result = hijri_year * CONSTANT

    subtraction_result = (
        multiplication_result - CONSTANT
    )


    # =====================================================
    # التقريب لأعلى
    # =====================================================

    upper_ayah = math.ceil(
        multiplication_result
    )

    lower_ayah = math.ceil(
        subtraction_result
    )


    # =====================================================
    # حماية الحدود
    # =====================================================

    lower_ayah = max(
        1,
        lower_ayah
    )

    upper_ayah = min(
        TOTAL_AYAT,
        upper_ayah
    )


    # =====================================================
    # عرض نتائج الحساب
    # =====================================================

    st.markdown("### 📊 نتائج المصفوفة")


    st.markdown(
        f"""
        <div style="
            background:black;
            padding:15px;
            border-radius:10px;
            text-align:center;
            margin-bottom:15px;
        ">

        <div style="
            color:#CFA500;
            font-size:22px;
            font-weight:bold;
        ">
        السنة الهجرية
        </div>

        <div style="
            color:white;
            font-size:32px;
            font-weight:bold;
        ">
        {hijri_year} هـ
        </div>

        </div>
        """,
        unsafe_allow_html=True
    )


    st.markdown(
        f"""
        <div style="
            background:#fff7e6;
            border:2px solid #CFA500;
            border-radius:10px;
            padding:20px;
            text-align:center;
            font-size:24px;
            font-weight:bold;
            color:#222222;
            line-height:2;
        ">

        الثابت =
        {TOTAL_AYAT} ÷ {TOTAL_HOURS}
        =
        {CONSTANT:.11f}

        <br><br>

        ناتج الضرب =
        {hijri_year}
        ×
        {CONSTANT:.11f}
        =
        {multiplication_result:.11f}

        <br><br>

        ناتج الطرح =
        {multiplication_result:.11f}
        -
        {CONSTANT:.11f}
        =
        {subtraction_result:.11f}

        <br><br>

        <span style="color:#CFA500;font-size:26px;">
        نطاق الآيات:
        {lower_ayah}
        إلى
        {upper_ayah}
        </span>

        </div>
        """,
        unsafe_allow_html=True
    )


    st.divider()


    # =====================================================
    # استخراج الآيات المطلوبة فقط
    # =====================================================

    results = df[
        (df["quran_ayah_number"] >= lower_ayah)
        &
        (df["quran_ayah_number"] <= upper_ayah)
    ]


    # =====================================================
    # عرض النتائج
    # بنفس شكل صفحة الباحث القرآني
    # =====================================================

    st.markdown(
        f"### 📌 عدد النتائج: {len(results)}"
    )


    for _, r in results.iterrows():

        st.markdown(
            f"""
            <b>{r['quran_ayah_number']}-</b>
            {r['ayah_text']}
            <hr>
            """,
            unsafe_allow_html=True
        )
