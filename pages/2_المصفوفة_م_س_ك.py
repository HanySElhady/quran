import streamlit as st
import pandas as pd
import re
import os
import math
from datetime import datetime
from PIL import Image
import io
import base64


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
    header_img = Image.open("assets/header2.png")
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
            r"^\s*\d+\s*[-_ ]\s*",
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
            r"^\s*[٠-٩]+\s*[-_ ]\s*",
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
# بداية الحساب الهجري
# =========================================================
HIJRI_START_GREGORIAN_YEAR = 623


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
        - ((30 - j) // 15)
        * ((17719 * j) // 50)
        - (j // 16)
        * ((15238 * j) // 43)
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
# تحويل السنة الميلادية إلى السنة الهجرية المقابلة
# =========================================================
def gregorian_year_to_hijri_year(gregorian_year):

    # بداية السنة الميلادية
    start_date = datetime(
        gregorian_year,
        1,
        1
    )

    # بداية السنة الميلادية التالية
    next_start_date = datetime(
        gregorian_year + 1,
        1,
        1
    )

    # منتصف السنة الميلادية
    middle_date = start_date + (
        next_start_date - start_date
    ) / 2

    # تحويل منتصف السنة إلى هجري
    hijri_year = gregorian_to_hijri(
        middle_date.year,
        middle_date.month,
        middle_date.day
    )[0]

    return hijri_year


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
    equivalent_year,
    equivalent_label
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
                السنة المقابلة:
                {equivalent_year} {equivalent_label}
            </div>

        </div>
        """
    )


# =========================================================
# عرض صندوق التاريخ التقليدي
# =========================================================
def show_traditional_year_box(
    traditional_value
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
                التاريخ التقليدي
            </div>

            <div style="
                color:white;
                font-size:34px;
                font-weight:bold;
                margin-top:5px;
            ">
                {traditional_value}
            </div>

            <div style="
                color:#CFA500;
                font-size:24px;
                font-weight:bold;
                margin-top:12px;
            ">
                بدون تحويل هجري أو ميلادي
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

    # =====================================================
    # التحقق من أن النطاق داخل القرآن
    # =====================================================
    if (
        lower_ayah > TOTAL_AYAT
        or upper_ayah < 1
        or lower_ayah > upper_ayah
    ):

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

                <br>

                ناتج الضرب =
                {year_value}
                ×
                {CONSTANT:.11f}
                =
                {multiplication_result:.11f}

                <br>

                ناتج الطرح =
                {multiplication_result:.11f}
                -
                {CONSTANT:.11f}
                =
                {subtraction_result:.11f}

                <br>

                <span style="
                    color:#CFA500;
                    font-size:28px;
                    font-weight:bold;
                ">
                    نطاق الآيات خارج حدود القرآن الكريم
                    <br>
                    الحد الأقصى = {TOTAL_AYAT}
                </span>

            </div>
            """
        )

        return (
            TOTAL_AYAT + 1,
            TOTAL_AYAT
        )

    # =====================================================
    # بيانات الآية الأولى في النطاق
    # =====================================================
    lower_row = df[
        df["quran_ayah_number"] == lower_ayah
    ].iloc[0]

    lower_surah_name = str(
        lower_row["surah_name"]
    ).strip()

    lower_surah_number = int(
        lower_row["surah_id"]
    )

    lower_surah_ayah_number = int(
        lower_row["ayah_number"]
    )

    # =====================================================
    # بيانات الآية الأخيرة في النطاق
    # =====================================================
    upper_row = df[
        df["quran_ayah_number"] == upper_ayah
    ].iloc[0]

    upper_surah_name = str(
        upper_row["surah_name"]
    ).strip()

    upper_surah_number = int(
        upper_row["surah_id"]
    )

    upper_surah_ayah_number = int(
        upper_row["ayah_number"]
    )

    # =====================================================
    # عرض صندوق الحساب
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

            <br>

            ناتج الضرب =
            {year_value}
            ×
            {CONSTANT:.11f}
            =
            {multiplication_result:.11f}

            <br>

            ناتج الطرح =
            {multiplication_result:.11f}
            -
            {CONSTANT:.11f}
            =
            {subtraction_result:.11f}

            <span style="
                color:#CFA500;
                font-size:28px;
                font-weight:bold;
            ">

                <br>

                نطاق الآيات:
                {lower_ayah}
                إلى
                {upper_ayah}

            </span>

            <br>
            <br>

            <!-- الآية الأولى في النطاق -->

            <div style="
                color:#222222;
                font-size:21px;
                font-weight:bold;
                line-height:2.2;
                margin-top:10px;
            ">

                من الآية

                <span style="color:#CFA500;">
                    {lower_ayah}
                </span>

                من سورة

                <span style="color:#CFA500;">
                    {lower_surah_name}
                </span>

                ورقم السورة في القرآن الكريم

                <span style="color:#CFA500;">
                    {lower_surah_number}
                </span>

                ورقم الآية

                <span style="color:#CFA500;">
                    {lower_surah_ayah_number}
                </span>

                من ترتيب القرآن

            </div>


            <!-- الآية الأخيرة في النطاق -->

            <div style="
                color:#222222;
                font-size:21px;
                font-weight:bold;
                line-height:2.2;
                margin-top:8px;
            ">

                إلى الآية

                <span style="color:#CFA500;">
                    {upper_ayah}
                </span>

                من سورة

                <span style="color:#CFA500;">
                    {upper_surah_name}
                </span>

                ورقم السورة في القرآن الكريم

                <span style="color:#CFA500;">
                    {upper_surah_number}
                </span>

                ورقم الآية

                <span style="color:#CFA500;">
                    {upper_surah_ayah_number}
                </span>

                من ترتيب القرآن

            </div>

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

                    سورة —
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
                ">
                </div>

            </div>
            """
        )


# =========================================================
# عرض الـ Footer
# =========================================================
def show_footer():

    try:

        footer_img = Image.open(
            "assets/footer.png"
        )

        buffer = io.BytesIO()

        footer_img.save(
            buffer,
            format="PNG"
        )

        footer_base64 = base64.b64encode(
            buffer.getvalue()
        ).decode()

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

    except Exception:
        pass


# =========================================================
# عنوان الصفحة
# =========================================================
st.markdown(
    "## 📅 مصفوفة م س ك (R G B)"
)


# =========================================================
# اختيار نوع البحث
# =========================================================
search_type = st.radio(
    "اختر نوع البحث",
    [
        "🌙 البحث بالسنة الهجرية",
        "☀️ البحث بالسنة الميلادية",
        "🔢 البحث بالتاريخ التقليدي"
    ],
    horizontal=True
)


# =========================================================
# البحث بالسنة الهجرية
# =========================================================
if search_type == "🌙 البحث بالسنة الهجرية":

    # =====================================================
    # إدخال السنة الهجرية
    # =====================================================
    hijri_input = st.text_input(
        "أدخل السنة الهجرية",
        key="hijri_year_input"
    )

    # =====================================================
    # التحقق من السنة
    # =====================================================
    if hijri_input:

        if not hijri_input.isdigit():

            st.error(
                "⚠️ من فضلك أدخل السنة الهجرية كرقم صحيح."
            )

            st.stop()

        input_year = int(
            hijri_input
        )

        # -------------------------------------------------
        # الحد الأدنى
        # -------------------------------------------------
        if input_year < 1:

            st.error(
                "⚠️ السنة الهجرية يجب أن تبدأ من 1 هـ."
            )

            st.stop()

        # -------------------------------------------------
        # السنوات المستقبلية
        # -------------------------------------------------
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

        # =================================================
        # السنة الميلادية المقابلة
        # =================================================
        equivalent_gregorian_year = (
            hijri_year_to_gregorian_year(
                input_year
            )
        )

        # =================================================
        # عنوان النتائج
        # =================================================
        st.markdown(
            "### 📊 نتائج المصفوفة"
        )

        # =================================================
        # صندوق السنة
        # =================================================
        show_year_box(
            input_year,
            "هـ",
            equivalent_gregorian_year,
            "م"
        )

        # =================================================
        # أولاً: السنة الهجرية
        # =================================================
        st.markdown(
            f"## 🌙 أولاً: نتائج السنة الهجرية {input_year} هـ"
        )

        lower_hijri, upper_hijri = (
            show_calculation_box(
                input_year,
                "هـ"
            )
        )

        # =================================================
        # نتائج الآيات الهجرية
        # =================================================
        hijri_results = df[
            (df["quran_ayah_number"] >= lower_hijri)
            &
            (df["quran_ayah_number"] <= upper_hijri)
        ]

        st.markdown(
            f"""
            ### 📌 عدد النتائج:
            {len(hijri_results)}
            """
        )

        show_ayah_results(
            hijri_results
        )

        st.divider()

        # =================================================
        # ثانياً: السنة الميلادية
        # =================================================
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

        # =================================================
        # نتائج الآيات الميلادية
        # =================================================
        gregorian_results = df[
            (df["quran_ayah_number"] >= lower_gregorian)
            &
            (df["quran_ayah_number"] <= upper_gregorian)
        ]

        st.markdown(
            f"""
            ### 📌 عدد النتائج:
            {len(gregorian_results)}
            """
        )

        show_ayah_results(
            gregorian_results
        )

        show_footer()


# =========================================================
# البحث بالسنة الميلادية
# =========================================================
elif search_type == "☀️ البحث بالسنة الميلادية":

    # =====================================================
    # إدخال السنة الميلادية
    # =====================================================
    gregorian_input = st.text_input(
        "أدخل السنة الميلادية",
        key="gregorian_year_input"
    )

    # =====================================================
    # التحقق من السنة
    # =====================================================
    if gregorian_input:

        if not gregorian_input.isdigit():

            st.error(
                "⚠️ من فضلك أدخل السنة الميلادية كرقم صحيح."
            )

            st.stop()

        input_year = int(
            gregorian_input
        )

        # -------------------------------------------------
        # الحد الأدنى
        # -------------------------------------------------
        if input_year < 1:

            st.error(
                "⚠️ السنة الميلادية يجب أن تبدأ من 1 م."
            )

            st.stop()

        # -------------------------------------------------
        # السنوات المستقبلية
        # -------------------------------------------------
        if input_year > CURRENT_GREGORIAN_YEAR:

            st.error(
                f"""
                ⚠️ لا يمكن البحث في سنوات غيبية.

                السنة المدخلة:
                {input_year} م

                السنة الميلادية الحالية:
                {CURRENT_GREGORIAN_YEAR} م
                """
            )

            st.stop()

        # =================================================
        # عنوان النتائج
        # =================================================
        st.markdown(
            "### 📊 نتائج المصفوفة"
        )

        # =================================================
        # الحالة الأولى:
        # السنة الميلادية قبل 623 م
        # =================================================
        if input_year < HIJRI_START_GREGORIAN_YEAR:

            # =================================================
            # صندوق السنة
            # =================================================
            show_year_box(
                input_year,
                "م",
                "غير متاح",
                "هـ"
            )

            # =================================================
            # رسالة التنبيه
            # =================================================
            st.warning(
                "التاريخ المدخل الميلادي قبل تاريخ هجرة الرسول محمد صلى الله عليه وسلم تسليما كثيراً."
            )

            # =================================================
            # نتائج السنة الميلادية فقط
            # =================================================
            st.markdown(
                f"## ☀️ نتائج السنة الميلادية {input_year} م"
            )

            lower_gregorian, upper_gregorian = (
                show_calculation_box(
                    input_year,
                    "م"
                )
            )

            gregorian_results = df[
                (df["quran_ayah_number"] >= lower_gregorian)
                &
                (df["quran_ayah_number"] <= upper_gregorian)
            ]

            st.markdown(
                f"""
                ### 📌 عدد النتائج:
                {len(gregorian_results)}
                """
            )

            show_ayah_results(
                gregorian_results
            )

            show_footer()

        # =================================================
        # الحالة الثانية:
        # السنة الميلادية 623 م أو بعدها
        # =================================================
        else:

            # =================================================
            # السنة الهجرية المقابلة
            # =================================================
            equivalent_hijri_year = (
                gregorian_year_to_hijri_year(
                    input_year
                )
            )

            # =================================================
            # صندوق السنة
            # =================================================
            show_year_box(
                input_year,
                "م",
                equivalent_hijri_year,
                "هـ"
            )

            # =================================================
            # أولاً: السنة الميلادية
            # =================================================
            st.markdown(
                f"## ☀️ أولاً: نتائج السنة الميلادية {input_year} م"
            )

            lower_gregorian, upper_gregorian = (
                show_calculation_box(
                    input_year,
                    "م"
                )
            )

            # =================================================
            # نتائج الآيات الميلادية
            # =================================================
            gregorian_results = df[
                (df["quran_ayah_number"] >= lower_gregorian)
                &
                (df["quran_ayah_number"] <= upper_gregorian)
            ]

            st.markdown(
                f"""
                ### 📌 عدد النتائج:
                {len(gregorian_results)}
                """
            )

            show_ayah_results(
                gregorian_results
            )

            st.divider()

            # =================================================
            # ثانياً: السنة الهجرية
            # =================================================
            st.markdown(
                f"""
                ## 🌙 ثانياً: نتائج السنة الهجرية
                {equivalent_hijri_year} هـ
                """
            )

            lower_hijri, upper_hijri = (
                show_calculation_box(
                    equivalent_hijri_year,
                    "هـ"
                )
            )

            # =================================================
            # نتائج الآيات الهجرية
            # =================================================
            hijri_results = df[
                (df["quran_ayah_number"] >= lower_hijri)
                &
                (df["quran_ayah_number"] <= upper_hijri)
            ]

            st.markdown(
                f"""
                ### 📌 عدد النتائج:
                {len(hijri_results)}
                """
            )

            show_ayah_results(
                hijri_results
            )

            show_footer()


# =========================================================
# البحث بالتاريخ التقليدي
# =========================================================
else:

    # =====================================================
    # إدخال الرقم / السنة التقليدية
    # =====================================================
    traditional_input = st.text_input(
        "أدخل الرقم أو السنة بالتاريخ التقليدي",
        key="traditional_year_input"
    )

    # =====================================================
    # التحقق من الإدخال
    # =====================================================
    if traditional_input:

        if not traditional_input.isdigit():

            st.error(
                "⚠️ من فضلك أدخل الرقم كرقم صحيح."
            )

            st.stop()

        traditional_year = int(
            traditional_input
        )

        # =================================================
        # منع الصفر والأرقام السالبة
        # =================================================
        if traditional_year < 1:

            st.error(
                "⚠️ الرقم يجب أن يكون أكبر من صفر."
            )

            st.stop()

        # =================================================
        # عنوان النتائج
        # =================================================
        st.markdown(
            "### 📊 نتائج المصفوفة"
        )

        # =================================================
        # صندوق التاريخ التقليدي
        #
        # لا يوجد أي تحويل هجري أو ميلادي
        # =================================================
        show_traditional_year_box(
            traditional_year
        )

        # =================================================
        # نتائج التاريخ التقليدي
        # =================================================
        st.markdown(
            f"## 🔢 نتائج التاريخ التقليدي {traditional_year}"
        )

        # =================================================
        # الحساب المباشر بالمصفوفة
        #
        # الرقم يدخل مباشرة:
        #
        # traditional_year × (6236 ÷ 2400)
        #
        # بدون تحويل هجري
        # وبدون تحويل ميلادي
        # =================================================
        lower_traditional, upper_traditional = (
            show_calculation_box(
                traditional_year,
                "تقليدي"
            )
        )

        # =================================================
        # نتائج الآيات
        # =================================================
        traditional_results = df[
            (df["quran_ayah_number"] >= lower_traditional)
            &
            (df["quran_ayah_number"] <= upper_traditional)
        ]

        # =================================================
        # عدد النتائج
        # =================================================
        st.markdown(
            f"""
            ### 📌 عدد النتائج:
            {len(traditional_results)}
            """
        )

        # =================================================
        # عرض الآيات
        # =================================================
        show_ayah_results(
            traditional_results
        )

        # =================================================
        # Footer
        # =================================================
        show_footer()
