import streamlit as st
import pandas as pd
import re
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
# تلوين التشكيل
# =========================
def highlight_tashkeel(text):
    tashkeel_marks = re.compile(r'([\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED])')
    return tashkeel_marks.sub(
        r'<span style="color:#CFA500; font-weight:bold;">\1</span>', text
    )

# =========================
# توحيد الهمزات إلى ألف
# =========================
def normalize_hamza_to_alif(text):
    return re.sub(r"[أإآؤئء]", "ا", text)

# =========================
# 🔥 normalize البحث الجديد (بدون دمج ع/غ)
# =========================
def normalize_letters_for_new_search(text):
    text = remove_tashkeel(text)

    text = re.sub(r"[أإآء]", "ا", text)
    text = re.sub(r"[يى]", "ي", text)
    text = re.sub(r"[هة]", "ه", text)
    text = re.sub(r"[ؤ]", "و", text)

    text = re.sub(r'[^ا-ي]', '', text)
    return text

# =========================
# استخراج الحروف الأصلية
# =========================
def extract_original_letters(ayah):
    txt = remove_tashkeel(ayah)
    txt = re.sub(r'[^ءابتثجحخدذرزسشصضطظعغفقكلمنهوي]', '', txt)
    txt = txt.replace(" ", "")
    letters = []
    for c in txt:
        if c not in letters:
            letters.append(c)
    return "".join(letters)

# =========================
# تنظيف اسم السورة
# =========================
def clean_surah_name(name):
    name = re.sub(r'^\d+[_-]*', '', name)
    name = re.sub(r'\.xlsx$', '', name)
    return name.strip()

# =========================
# قراءة الملفات
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
            file_num = int(re.match(r"^(\d+)", os.path.basename(v["path"])).group(1))
            df_temp["surah_id"] = file_num
            df_temp["surah_name"] = v["name"]
            all_rows.append(df_temp)

        return pd.concat(all_rows).sort_values(
            ["surah_id", "ayah_number"]
        ).reset_index(drop=True)

    else:
        path = get_file_path_by_name(selected_surah_name)
        df = pd.read_excel(path)
        df["surah_name"] = selected_surah_name
        return df.sort_values("ayah_number").reset_index(drop=True)

df = load_data(selected_surah)

# =========================
# نوع البحث
# =========================
search_type = st.radio(
    "اختر نوع البحث",
    ["بحث حروف الكلمة شاملة","بحث بالكلمة","بحث برقم الآية","عرض السورة كاملة","بحث حروف الكلمة","بحث الحروف الأصلية"],
    horizontal=True
)

# =========================
# 🔍 البحث الجديد
# =========================
if search_type == "بحث جديد":

    st.markdown("### 🔍 بحث بالحروف مع توحيد المتشابه")

    search_input = st.text_input("اكتب الحروف")

    if search_input:
        user = normalize_letters_for_new_search(search_input)
        user_unique = "".join(sorted(set(user)))

        results = []

        for _, row in df.iterrows():
            ayah = normalize_letters_for_new_search(row["ayah_text"])
            ayah_unique = "".join(sorted(set(ayah)))

            if ayah_unique == user_unique:
                results.append(row)

        st.write(f"عدد النتائج: {len(results)}")

        for r in results:
            st.markdown(f"""
            <b>{r['surah_name']} ({r['ayah_number']})</b><br>
            <i>{r['ayah_text']}</i>
            <hr>
            """, unsafe_allow_html=True)

# =========================
# 🔎 بحث بالكلمة
# =========================
elif search_type == "بحث بالكلمة":

    keyword = st.text_input("اكتب الكلمة")

    if keyword:
        keyword_clean = normalize_letters_for_new_search(keyword)

        results = df[df["ayah_text"].apply(
            lambda x: keyword_clean in normalize_letters_for_new_search(x)
        )]

        for _, row in results.iterrows():
            st.markdown(f"""
            <b>{row['surah_name']} ({row['ayah_number']})</b><br>
            {highlight_tashkeel(row['ayah_text'])}
            <hr>
            """, unsafe_allow_html=True)

# =========================
# 🔢 بحث برقم الآية
# =========================
elif search_type == "بحث برقم الآية":
    num = st.number_input("رقم الآية", 1, int(df["ayah_number"].max()))

    result = df[df["ayah_number"] == num]

    for _, row in result.iterrows():
        st.markdown(f"""
        <b>{row['surah_name']} ({row['ayah_number']})</b><br>
        {highlight_tashkeel(row['ayah_text'])}
        """, unsafe_allow_html=True)

# =========================
# 📖 عرض السورة
# =========================
elif search_type == "عرض السورة كاملة":
    for _, row in df.iterrows():
        st.markdown(f"""
        <b>{row['surah_name']} ({row['ayah_number']})</b><br>
        {highlight_tashkeel(row['ayah_text'])}
        """, unsafe_allow_html=True)
