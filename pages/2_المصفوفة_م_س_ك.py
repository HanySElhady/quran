import streamlit as st
import pandas as pd
import re
import os
import math
from datetime import datetime
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
except Exception:
    pass


# =========================================================
# قراءة جميع ملفات القرآن
# =========================================================

@st.cache_data
def load_quran_all():

    rows = []

    for f in os.listdir("data"):

        # ملفات Excel فقط
        if not f.lower().endswith(".xlsx"):
            continue

        # استخراج رقم السورة من بداية اسم الملف
        match = re.match(r"^(\d+)", f)

        if not match:
            continue

        surah_id = int(match.group(1))

        path = os.path.join("data", f)

        try:
            df_surah = pd.read_excel(path)
        except Exception:
            continue

        # =================================================
        # تنظيف اسم السورة
        # =================================================

        surah_name = re.sub(
            r"^\s*\d+\s*[-_ ]*\s*",
            "",
            f
        )

        surah_name = re.sub(
            r"\.xlsx$",
            "",
            surah_name,
            flags=re.IGNORECASE
        )

        # دعم الأرقام العربية في اسم الملف
        surah_name = re.sub(
            r"^\s*[٠-٩]+\s*[-_ ]*\s*",
            "",
            surah_name
        )

        surah_name = surah_name.strip()

        # إضافة بيانات السورة
        df_surah["surah_id"] = surah_id
        df_surah["surah_name"] = surah_name

        rows.append(df_surah)

    # =====================================================
    # لا توجد ملفات
    # =====================================================

    if not rows:
        return pd.DataFrame()

    # =====================================================
    # تجميع القرآن
    # =====================================================

    quran = pd.concat(
        rows,
        ignore_index=True
    )

    # =====================================================
    # ترتيب السور والآيات
    # =====================================================

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
# التحقق من البيانات
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
# قراءة التاريخ الحالي
# =========================================================

today = datetime.now()

CURRENT_GREGORIAN_YEAR = today.year


# =========================================================
# حساب السنة الهجرية الحالية
# =========================================================

def gregorian_to_hijri_year(year, month, day):

    jd = (
        367 * year
        - int(
            (7 * (
                year + int((month + 9) / 12)
            )) / 4
        )
        + int((275 * month) / 9)
        + day
        + 1721013.5
    )

    hijri_year = int(
        (
            30 * (jd - 1948439.5) + 10646
        ) / 10631
    )

    return hijri_year


CURRENT_HIJRI_YEAR = gregorian_to_hijri_year(
    today.year,
    today.month,
    today.day
)


# =========================================================
# عنوان الصفحة
# =========================================================

st.markdown(
    "## 📅 مصفوفة م س ك (R G B)"
)


# =========================================================
# اختيار نوع السنة
# =========================================================

date_type = st.radio(
    "اختر نوع السنة:",
    [
        "السنة الهجرية",
        "السنة الميلادية"
    ],
    horizontal=True
)


# =========================================================
# متغير السنة المستخدمة في المعادلة
# =========================================================

input_year = None
year_label = ""


# =========================================================
# إدخال السنة الهجرية
# =========================================================

if date_type == "السنة الهجرية":

    hijri_input = st.text_input(
        "أدخل السنة الهجرية",
        placeholder="مثال: 1395",
        key="hijri_year_input"
    )

    if hijri_input:

        if not hijri_input.isdigit():

            st.error(
                "⚠️ من فضلك أدخل السنة الهجرية كرقم صحيح."
            )

            st.stop()

        input_year = int(hijri_input)
        year_label = "هـ"

        if input_year < 1:

            st.error(
                "⚠️ السنة الهجرية يجب أن تبدأ من 1 هـ."
            )

            st.stop()

        if input_year > CURRENT_HIJRI_YEAR:

            st.error(
                f"⚠️ لا يمكن البحث في سنوات غيبية.\n\n"
                f"السنة المدخلة: {input_year} هـ\n"
                f"السنة الهجرية الحالية: {CURRENT_HIJRI_YEAR} هـ"
            )

            st.stop()


# =========================================================
# إدخال السنة الميلادية
# =========================================================

else:

    gregorian_input = st.text_input(
        "أدخل السنة الميلادية",
        placeholder="مثال: 1973",
        key="gregorian_year_input"
    )

    if gregorian_input:

        if not gregorian_input.isdigit():

            st.error(
                "⚠️ من فضلك أدخل السنة الميلادية كرقم صحيح."
            )

            st.stop()

        input_year = int(gregorian_input)
        year_label = "م"

        if input_year < 1:

            st.error(
                "⚠️ السنة الميلادية يجب أن تبدأ من 1 م."
            )

            st.stop()

        if input_year > CURRENT_GREGORIAN_YEAR:

            st.error(
                f"⚠️ لا يمكن البحث في سنوات غيبية.\n\n"
                f"السنة المدخلة: {input_year} م\n"
                f"السنة الميلادية الحالية: {CURRENT_GREGORIAN_YEAR} م"
            )

            st.stop()


# =========================================================
# تنفيذ المعادلة
#
# ملاحظة:
# لا يوجد أي تحويل بين هجري وميلادي.
# الرقم المدخل نفسه يدخل في المعادلة.
# =========================================================

if input_year is not None:

    multiplication_result = (
        input_year * CONSTANT
    )

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
    # النتائج
    # =====================================================

    st.markdown(
        "### 📊 نتائج المصفوفة"
    )


    # =====================================================
    # صندوق السنة
    # =====================================================

    st.html(
        f"""
        <div style="
            background:black;
            padding:18px;
            border-radius:10px;
            text-align:center;
            margin-bottom:18px;
        ">

            <div style="
                color:#CFA500;
                font-size:22px;
                font-weight:bold;
            ">
                السنة المستخدمة في المصفوفة
            </div>

            <div style="
                color:white;
                font-size:34px;
                font-weight:bold;
                margin-top:5px;
            ">
                {input_year} {year_label}
            </div>

        </div>
        """
    )


    # =====================================================
    # صندوق الحساب
    # =====================================================

    st.html(
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
            {TOTAL_AYAT}
            ÷
            {TOTAL_HOURS}
            =
            {CONSTANT:.11f}

            <br><br>

            ناتج الضرب =
            {input_year}
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

            <span style="
                color:#CFA500;
                font-size:28px;
                font-weight:bold;
            ">
                نطاق الآيات:
                {lower_ayah}
                إلى
                {upper_ayah}
            </span>

        </div>
        """
    )


    st.divider()


    # =====================================================
    # استخراج الآيات
    # =====================================================

    results = df[
        (df["quran_ayah_number"] >= lower_ayah)
        &
        (df["quran_ayah_number"] <= upper_ayah)
    ]


    # =====================================================
    # عدد النتائج
    # =====================================================

    st.markdown(
        f"### 📌 عدد النتائج: {len(results)}"
    )


    # =====================================================
    # عرض الآيات
    # =====================================================

    for _, r in results.iterrows():

        clean_name = str(
            r["surah_name"]
        ).strip()

        st.html(
            f"""
            <div style="
                direction:rtl;
                text-align:right;
                margin-bottom:30px;
            ">

                <div style="
                    font-size:20px;
                    font-weight:bold;
                    color:#CFA500;
                    margin-bottom:10px;
                ">
                    سورة {r['surah_id']} — {clean_name}
                    &nbsp;&nbsp; | &nbsp;&nbsp;
                    الآية {r['ayah_number']}
                </div>


                <div style="
                    font-size:32px;
                    line-height:2.3;
                    color:#CFA500;
                    font-weight:normal;
                ">

                    <span style="
                        color:#222222;
                        font-size:29px;
                        font-weight:bold;
                        white-space:nowrap;
                    ">
                        {r['quran_ayah_number']} —
                    </span>

                    <span>
                        {r['ayah_text']}
                    </span>

                </div>


                <div style="
                    border-bottom:1px solid #CFA500;
                    opacity:0.5;
                    margin-top:15px;
                "></div>

            </div>
            """
        )
