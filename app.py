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
# تنظيف اسم السورة (عرض فقط)
# =========================
def clean_surah_name(name):
    name = re.sub(r'^\d+\s*[-_]*\s*', '', name)
    name = re.sub(r'\s*[-_]*\s*\d+$', '', name)
    return name.strip()

# =========================
# قراءة ملفات السور
# =========================
@st.cache_data
def get_surah_files():
    files = {}
    for file in os.listdir("data"):
        if file.endswith(".xlsx"):
            match = re.match(r"(\d+)", file)
            surah_num = int(match.group(1)) if match else 999
            surah_name = file.replace(".xlsx", "").replace("_", " ")
            files[surah_num] = {
                "name": surah_name,
                "path": os.path.join("data", file)
            }

    files[1000] = {"name": "القرآن كله", "path": None}
    return dict(sorted(files.items()))

surah_files_dict = get_surah_files()
surah_options = [v["name"] for v in surah_files_dict.values()]

selected_surah = st.sidebar.selectbox("اختر السورة", surah_options)

def get_file_path_by_name(surah_name):
    for v in surah_files_dict.values():
        if v["name"] == surah_name:
            return v["path"]
    return None

# =========================
# تحميل البيانات
# =========================
@st.cache_data
def load_data(selected_surah_name):
    if selected_surah_name == "القرآن كله":
        all_rows = []
        for v in surah_files_dict.values():
            if v["path"] is None:
                continue
            df_temp = pd.read_excel(v["path"])
            df_temp["surah_name"] = v["name"]
            all_rows.append(df_temp)

        return (
            pd.concat(all_rows, ignore_index=True)
            .sort_values(["surah_id", "ayah_number"])
            .reset_index(drop=True)
        )
    else:
        return pd.read_excel(get_file_path_by_name(selected_surah_name))

df = load_data(selected_surah)

# =========================
# عنوان الصفحة
# =========================
st.markdown(
    f"""
    <div style="background-color:#f0f8ff; padding:15px; border-radius:10px;">
        <h1 style="color:#003366; text-align:center;">📖 البحث في القرآن الكريم</h1>
        <h3 style="color:#006699; text-align:center;">
             {clean_surah_name(selected_surah)}
        </h3>
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
    ["بحث بكلمة", "بحث برقم الآية", "عرض السورة كاملة"],
    horizontal=True
)
st.divider()

# =========================
# تلوين الحروف
# =========================
def highlight_chars(original, keyword_clean):
    result = ""
    seen = set()
    for char in original:
        clean = remove_tashkeel(char)
        if clean in keyword_clean and clean not in seen:
            result += f'<span style="color:green; font-weight:bold;">{char}</span>'
            seen.add(clean)
        else:
            result += char
    return result

# =========================
# 🔍 بحث بالكلمة
# =========================
if search_type == "بحث بكلمة":
    keyword = st.text_input("اكتب الحروف للبحث داخل الآيات")

    if keyword:
        keyword_clean = remove_tashkeel(keyword)

        results = df[df["ayah_text"].apply(
            lambda x: all(c in remove_tashkeel(x) for c in keyword_clean)
        )]

        # ترتيب عند القرآن كله فقط
        if selected_surah == "القرآن كله":
            results = results.sort_values(
                ["surah_name","ayah_number"]
            ).reset_index(drop=True)

        st.write(f"عدد النتائج: {len(results)}")

        for _, row in results.iterrows():
            surah_clean = clean_surah_name(row["surah_name"])

            st.markdown(
                f"""
                <div style="direction:rtl; unicode-bidi:isolate; text-align:right; font-size:18px; margin-bottom:10px;">
                    <b> {surah_clean} ({row['ayah_number']})</b><br>
                    {highlight_chars(row["ayah_text"], keyword_clean)}
                </div>
                """,
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

    # ترتيب عند القرآن كله فقط
    if selected_surah == "القرآن كله":
        result = result.sort_values(
            ["surah_name","ayah_number"]
        ).reset_index(drop=True)

    for _, row in result.iterrows():
        surah_clean = clean_surah_name(row["surah_name"])

        st.markdown(
            f"""
            <div style="direction:rtl; unicode-bidi:isolate; text-align:right; font-size:20px; margin-bottom:10px;">
                <b> {surah_clean} ({ayah_number})</b><br>
                {row["ayah_text"]}
            </div>
            """,
            unsafe_allow_html=True
        )

# =========================
# 📖 عرض السورة كاملة
# =========================
elif search_type == "عرض السورة كاملة":

    df_display = df

    if selected_surah == "القرآن كله":
        df_display = df.sort_values(
            ["surah_name"]
        ).reset_index(drop=True)

    for _, row in df_display.iterrows():
        surah_clean = clean_surah_name(row["surah_name"])

        st.markdown(
            f"""
            <div style="direction:rtl; unicode-bidi:isolate; text-align:right; font-size:18px; margin-bottom:10px;">
                <b> {surah_clean} ({row['ayah_number']})</b><br>
                {row["ayah_text"]}
            </div>
            """,
            unsafe_allow_html=True
        )



