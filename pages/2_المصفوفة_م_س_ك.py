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
# التاريخ الحالي
# =========================================================

today = datetime.now()

CURRENT_GREGORIAN_YEAR = today.year


# =========================================================
# تحويل التاريخ الميلادي إلى الهجري
# =========================================================

def gregorian_to_hijri(year, month, day):

    a = (14 - month) // 12

    y = year + 4800 - a

    m = month + 12 * a - 3

    jd = (
        day
        + ((153 * m + 2) // 5)
        + 365 * y
        + (y // 4)
        - (y // 100)
        + (y // 400)
        - 32045
    )

    l = jd - 1948440 + 10632

    n = (l - 1) // 10631

    l = l - 10631 * n + 354

    j = (
        ((10985 - l) // 5316)
        *
        ((50 * l) // 17719)
        +
        (l // 5670)
        *
        ((43 * l) // 15238)
    )

    l = (
        l
        - (
            (30 - j) // 15
        )
        *
        (
            (17719 * j) // 50
        )
        - (
            j // 16
        )
        *
        (
            (15238 * j) // 43
        )
        + 29
    )

    month_h = (24 * l) // 709

    day_h = (
        l
        - (709 * month_h) // 24
    )

    year_h = (
        30 * n
        + j
        - 30
    )

    return (
        int(year_h),
        int(month_h),
        int(day_h)
    )


# =========================================================
# تحويل السنة الهجرية إلى السنة الميلادية المقابلة
# =========================================================

def hijri_year_to_gregorian_year(hijri_year):

    # اليوم الأول من السنة الهجرية
    start_date = hijri_to_gregorian(
        hijri_year,
        1,
        1
    )

    # اليوم الأول من السنة الهجرية التالية
    next_start_date = hijri_to_gregorian(
        hijri_year + 1,
        1,
        1
    )

    # منتصف السنة الهجرية
    middle_date = start_date + (
        next_start_date - start_date
    ) / 2

    return middle_date.year


# =========================================================
# تحويل التاريخ الهجري إلى ميلادي
# =========================================================

def hijri_to_gregorian(
    h_year,
    h_month,
    h_day
):

    jd = (
        h_day
        + math.ceil(
            29.5 * (h_month - 1)
        )
        + (h_year - 1) * 354
        + math.floor(
            (3 + 11 * h_year) / 30
        )
        + 1948439
        - 1
    )

    l = jd + 68569

    n = (4 * l) // 146097

    l = l - (
        (146097 * n + 3) // 4
    )

    i = (
        4000 * (l + 1)
    ) // 1461001

    l = (
        l
        - (1461 * i) // 4
        + 31
    )

    j = (80 * l) // 2447

    day = (
        l
        - (2447 * j) // 80
    )

    l = j // 11

    month = (
        j
        + 2
        - 12 * l
    )

    year = (
        100 * (n - 49)
        + i
        + l
    )

    return datetime(
        int(year),
        int(month),
        int(day)
    )


# =========================================================
# السنة الهجرية الحالية
# =========================================================

CURRENT_HIJRI_YEAR = gregorian_to_hijri(
    today.year,
    today.month,
    today.day
)[0]


# =========================================================
# حساب نطاق الآيات
# =========================================================

def calculate_ayah_range(year_value):

    # -----------------------------------------------------
    # ناتج الضرب
    # -----------------------------------------------------

    multiplication_result = (
        year_value * CONSTANT
    )

    # -----------------------------------------------------
    # ناتج الطرح
    # -----------------------------------------------------

    subtraction_result = (
        multiplication_result - CONSTANT
    )

    # -----------------------------------------------------
    # التقريب لأعلى
    # -----------------------------------------------------

    upper_ayah = math.ceil(
        multiplication_result
    )

    lower_ayah = math.ceil(
        subtraction_result
    )

    # -----------------------------------------------------
    # حماية الحدود
    # -----------------------------------------------------

    lower_ayah = max(
        1,
        lower_ayah
    )

    upper_ayah = min(
        TOTAL_AYAT,
        upper_ayah
    )

    return (
        multiplication_result,
        subtraction_result,
        lower_ayah,
        upper_ayah
    )


# =========================================================
# عرض صندوق السنة
# =========================================================

def show_year_box(
    input_year,
    input_label,
    equivalent_year
):

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
                السنة المدخلة
            </div>

            <div style="
                color:white;
                font-size:34px;
                font-weight:bold;
                margin-top:5px;
            ">
                {input_year} {input_label}
            </div>

            <div style="
                color:#CFA500;
                font-size:24px;
                font-weight:bold;
                margin-top:12px;
            ">
                السنة الميلادية المقابلة:
                {equivalent_year} م
            </div>

        </div>
        """
    )


# =========================================================
# عرض صندوق الحساب
# =========================================================

def show_calculation_box(
    year_value,
    year_label
):

    (
        multiplication_result,
        subtraction_result,
        lower_ayah,
        upper_ayah
    ) = calculate_ayah_range(
        year_value
    )

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

            <div style="
                color:#CFA500;
                font-size:28px;
                font-weight:bold;
                margin-bottom:10px;
            ">
                حساب السنة {year_value} {year_label}
            </div>

            الثابت =

            {TOTAL_AYAT}

            ÷

            {TOTAL_HOURS}

            =

            {CONSTANT:.11f}

            <br><br>

            ناتج الضرب =

            {year_value}

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

    return (
        lower_ayah,
        upper_ayah
    )


# =========================================================
# عرض الآيات
# =========================================================

def show_ayah_results(results):

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

                    سورة  —
                    {clean_name}

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


# =========================================================
# عنوان الصفحة
# =========================================================

st.markdown(
    "## 📅 مصفوفة م س ك (R G B)"
)


# =========================================================
# إدخال السنة الهجرية
# =========================================================

hijri_input = st.text_input(
    "أدخل السنة الهجرية",
    placeholder="مثال: 1395",
    key="hijri_year_input"
)


# =========================================================
# التحقق من السنة
# =========================================================

if hijri_input:

    # -----------------------------------------------------
    # يجب أن تكون أرقام فقط
    # -----------------------------------------------------

    if not hijri_input.isdigit():

        st.error(
            "⚠️ من فضلك أدخل السنة الهجرية كرقم صحيح."
        )

        st.stop()

    input_year = int(
        hijri_input
    )

    # -----------------------------------------------------
    # التحقق من الحد الأدنى
    # -----------------------------------------------------

    if input_year < 1:

        st.error(
            "⚠️ السنة الهجرية يجب أن تبدأ من 1 هـ."
        )

        st.stop()

    # -----------------------------------------------------
    # التحقق من السنوات المستقبلية
    # -----------------------------------------------------

    if input_year > CURRENT_HIJRI_YEAR:

        st.error(
            f"""
            ⚠️ لا يمكن البحث في سنوات غيبية.

            السنة المدخلة:
            {input_year} هـ

            السنة الهجرية الحالية:
            {CURRENT_HIJRI_YEAR} هـ
            """
        )

        st.stop()


    # =====================================================
    # تحديد السنة الميلادية المقابلة
    # =====================================================

    equivalent_gregorian_year = (
        hijri_year_to_gregorian_year(
            input_year
        )
    )


    # =====================================================
    # عرض السنة الهجرية والميلادية
    # =====================================================

    st.markdown(
        "### 📊 نتائج المصفوفة"
    )

    show_year_box(
        input_year,
        "هـ",
        equivalent_gregorian_year
    )


    # =====================================================
    # الحساب الأول
    # السنة الهجرية
    # =====================================================

    st.markdown(
        f"## 🌙 أولاً: نتائج السنة الهجرية {input_year} هـ"
    )


    lower_hijri, upper_hijri = (
        show_calculation_box(
            input_year,
            "هـ"
        )
    )


    # =====================================================
    # استخراج آيات السنة الهجرية
    # =====================================================

    hijri_results = df[
        (df["quran_ayah_number"] >= lower_hijri)
        &
        (df["quran_ayah_number"] <= upper_hijri)
    ]


    # =====================================================
    # عدد النتائج الهجرية
    # =====================================================

    st.markdown(
        f"""
        ### 📌 عدد النتائج:
        {len(hijri_results)}
        """
    )


    # =====================================================
    # عرض النتائج الهجرية
    # =====================================================

    show_ayah_results(
        hijri_results
    )


    # =====================================================
    # فاصل
    # =====================================================

    st.divider()


    # =====================================================
    # الحساب الثاني
    # السنة الميلادية المقابلة
    # =====================================================

    st.markdown(
        f"""
        ## ☀️ ثانياً: نتائج السنة الميلادية
        {equivalent_gregorian_year} م
        """
    )


    lower_gregorian, upper_gregorian = (
        show_calculation_box(
            equivalent_gregorian_year,
            "م"
        )
    )


    # =====================================================
    # استخراج آيات السنة الميلادية
    # =====================================================

    gregorian_results = df[
        (df["quran_ayah_number"] >= lower_gregorian)
        &
        (df["quran_ayah_number"] <= upper_gregorian)
    ]


    # =====================================================
    # عدد النتائج الميلادية
    # =====================================================

    st.markdown(
        f"""
        ### 📌 عدد النتائج:
        {len(gregorian_results)}
        """
    )


    # =====================================================
    # عرض النتائج الميلادية
    # =====================================================

    show_ayah_results(
        gregorian_results
    )

    # =========================
    # Footer
    # =========================
    # =========================
    # Footer
    # =========================
    try:
        footer_img = Image.open("assets/footer.png")

        import io
        import base64

        buffer = io.BytesIO()
        footer_img.save(buffer, format="PNG")
        footer_base64 = base64.b64encode(buffer.getvalue()).decode()

        st.html(
            f"""
            <div style="
                width:100%;
                display:flex;
                justify-content:center;
                align-items:center;
                margin-top:30px;
                margin-bottom:20px;
            ">
                <img
                    src="data:image/png;base64,{footer_base64}"
                    style="
                        max-width:100%;
                        height:auto;
                    "
                >
            </div>
            """
        )

    except:
        pass
