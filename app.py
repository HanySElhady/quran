import streamlit as st
import pandas as pd
import re
from io import BytesIO
from PIL import Image
import os

# =========================
# إعداد الصفحة
# =========================
st.set_page_config(
    page_title="البحث في القرآن الكريم",
    page_icon="📖",
    layout="wide"
)

# =========================
# صورة العنوان
# =========================
header_img = Image.open("assets/header.png")
st.image(header_img, use_container_width=True)

# =========================
# إزالة التشكيل
# =========================
def remove_tashkeel(text):
    tashkeel = re.compile(
        r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED]'
    )
    return tashkeel.sub('', str(text))

# =========================
# تنظيف اسم السورة النهائي (حسب ملفاتك الجديدة)
# =========================
def clean_surah_name(name):
    name = re.sub(r'^\d+[_-]*', '', name)     # إزالة الرقم من البداية
    name = re.sub(r'\.xlsx$', '', name)       # إزالة .xlsx لو ظهرت
    return name.strip()

# =========================
# قراءة ملفات السور من مجلد data
# =========================
@st.cache_data
def get_surah_files():
    files = {}
    files[0] = {"name": "القرآن كله", "path": None}

    for file in os.listdir("data"):
        if file.endswith(".xlsx"):
            match = re.match(r"^(\d+)", file)
            surah_num = int(match.group(1)) if match else 999
            surah_name = clean_surah_name(file.replace(".xlsx", ""))
            files[surah_num] = {
                "name": surah_name,
                "path": os.path.join("data", file)
            }

    return dict(sorted(files.items(), key=lambda x: x[0]))

surah_files_dict = get_surah_files()
surah_options = [v["name"] for v in surah_files_dict.values()]
selected_surah = st.sidebar.selectbox("اختر السورة", surah_options)

# مسار الملف حسب اسم السورة
def get_file_path_by_name(surah_name):
    for v in surah_files_dict.values():
        if v["name"] == surah_name:
            return v["path"]
    return None
# =========================
# تحميل الداتا حسب الاختيار (بعد التعديل)
# =========================
@st.cache_data
def load_data(selected_surah_name):
    if selected_surah_name == "القرآن كله":
        all_rows = []
        for k, v in surah_files_dict.items():
            if v["path"] is None:
                continue

            df_temp = pd.read_excel(v["path"])

            # استخراج رقم السورة من اسم الملف
            file_num_match = re.match(r"^(\d+)", os.path.basename(v["path"]))
            surah_id = int(file_num_match.group(1)) if file_num_match else 999

            # إضافة الأعمدة المهمة
            df_temp["surah_id"] = surah_id
            df_temp["surah_name"] = clean_surah_name(v["name"])

            all_rows.append(df_temp)

        # دمج وترتيب حسب المصحف
        df_all = (
            pd.concat(all_rows, ignore_index=True)
            .sort_values(["surah_id", "ayah_number"])
            .reset_index(drop=True)
        )

        return df_all

    else:
        path = get_file_path_by_name(selected_surah_name)
        df_single = pd.read_excel(path)

        # إضافة رقم السورة لملف السورة المنفردة
        file_num_match = re.match(r"^(\d+)", os.path.basename(path))
        surah_id = int(file_num_match.group(1)) if file_num_match else 999

        df_single["surah_id"] = surah_id
        df_single["surah_name"] = clean_surah_name(selected_surah_name)

        # ترتيب للضمان
        return df_single.sort_values("ayah_number").reset_index(drop=True)


df = load_data(selected_surah)
# =========================
# 📊 إحصاءات السور والآيات (تصحيح التجميع)
# =========================
st.markdown("## 📊 إحصاءات")

if selected_surah == "القرآن كله":

    # تجهيز ترتيب المصحف مرة واحدة
    surah_order = (
        df[["surah_id", "surah_name"]]
        .drop_duplicates()
        .sort_values("surah_id")
        .copy()
    )
    surah_order["surah_name"] = surah_order["surah_name"].apply(clean_surah_name)

    # حساب عدد الآيات بناءً على رقم السورة وليس الاسم فقط
    stats_df = (
        df.groupby(["surah_id", "surah_name"])["ayah_number"]
        .nunique()  # ضمان عدم التكرار
        .reset_index()
        .rename(columns={"surah_name": "اسم السورة", "ayah_number": "عدد الآيات"})
    )

    # تنظيف أسماء السور
    stats_df["اسم السورة"] = stats_df["اسم السورة"].apply(clean_surah_name)

    # دمج الترتيب
    stats_df = stats_df.merge(
        surah_order,
        left_on="surah_id",
        right_on="surah_id",
        how="left"
    ).sort_values("surah_id")

    # جدول نظيف نهائي
    stats_df = stats_df[["surah_id", "اسم السورة", "عدد الآيات"]].reset_index(drop=True)

    # حساب الإجمالي الصحيح 6236 آية
    total_ayahs = stats_df["عدد الآيات"].sum()

    # عرض الإجمالي
    st.markdown(
        f"""
        <div style="background-color:black; padding:15px; border-radius:10px; text-align:center;">
            <h3>📖 إجمالي عدد آيات القرآن الكريم</h3>
            <h1 style="color:white;">{total_ayahs}</h1>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()
    st.markdown("### 📘 عدد الآيات في كل سورة بترتيب المصحف")

    st.dataframe(
        stats_df,
        use_container_width=True,
        hide_index=True
    )

else:
    surah_clean = clean_surah_name(selected_surah)
    ayah_count = df["ayah_number"].nunique()  # تصحيح العد داخل السورة

    st.markdown(
        f"""
        <div style="background-color:#e8f4ff; padding:20px; border-radius:10px; text-align:center;">
            <h3>📘 سورة {surah_clean}</h3>
            <p style="font-size:18px;">عدد الآيات</p>
            <h1 style="color:#003366;">{ayah_count}</h1>
        </div>
        """,
        unsafe_allow_html=True
    )

st.divider()
# =========================
# عنوان الصفحة
# =========================
st.markdown(
    f"""
    <div style="background-color:#f0f8ff; padding:15px; border-radius:10px;">
        <h1 style="color:#003366; text-align:center;">📖 البحث في القرآن الكريم</h1>
        <h3 style="color:#006699; text-align:center;">{clean_surah_name(selected_surah)}</h3>
    </div>
    """,
    unsafe_allow_html=True
)

st.divider()

# =========================
# نوع البحث
# =========================
search_type = st.radio(
    "اختر نوع البحث",
    ["بحث برقم الآية", "عرض السورة كاملة", "بحث حروف الكلمة"],
    horizontal=True
)
st.divider()
# =========================
# تظليل مطابق للحروف
# =========================
def highlight_chars_as_input(text, keyword):
    keyword_clean = remove_tashkeel(keyword)
    highlighted = ""
    used = []
    for char in text:
        char_clean = remove_tashkeel(char)
        if char_clean in keyword_clean and used.count(char_clean) < keyword_clean.count(char_clean):
            highlighted += f'<span style="color:green; font-weight:bold;">{char}</span>'
            used.append(char_clean)
        else:
            highlighted += char
    return highlighted

# =========================
# 🔍 بحث حروف الكلمة
# =========================
if search_type == "بحث حروف الكلمة":
    keyword = st.text_input("اكتب الحروف للبحث داخل الآيات")
    if keyword:
        keyword_clean = remove_tashkeel(keyword)

        def contains_all_chars_counted(ayah):
            ayah_clean = remove_tashkeel(ayah)
            return all(ayah_clean.count(c) >= keyword_clean.count(c) for c in set(keyword_clean))

        results = df[df["ayah_text"].apply(contains_all_chars_counted)]

        if selected_surah == "القرآن كله":
            results = results.sort_values(["surah_id","ayah_number"]).reset_index(drop=True)

        st.write(f"عدد النتائج: {len(results)}")

        for _, row in results.iterrows():
            st.markdown(
                f"<b>{row['surah_name']} ({row['ayah_number']})</b><br>{highlight_chars_as_input(row['ayah_text'], keyword)}<br><br>",
                unsafe_allow_html=True
            )
# =========================
# 🔢 بحث برقم الآية
# =========================
elif search_type == "بحث برقم الآية":
    ayah_number = st.number_input(
        "أدخل رقم الآية",
        min_value=1,
        max_value=int(df["ayah_number"].max()),
        step=1
    )
    result = df[df["ayah_number"] == ayah_number]
    for _, row in result.iterrows():
        st.markdown(
            f"<b>{row['surah_name']} ({ayah_number})</b><br>{row['ayah_text']}<br><br>",
            unsafe_allow_html=True
        )

# =========================
# 📖 عرض السورة كاملة
# =========================
elif search_type == "عرض السورة كاملة":
    for _, row in df.iterrows():
        st.markdown(
            f"<b>{row['surah_name']} ({row['ayah_number']})</b><br>{row['ayah_text']}<br><br>",
            unsafe_allow_html=True
        )

st.markdown("---")
try:
    footer_img = Image.open("assets/footer.png")
    st.image(footer_img, use_container_width=False)
except:
    st.warning("⚠ لم يتم العثور على صورة footer.png داخل مجلد assets")




