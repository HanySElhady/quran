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
    return re.sub(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]', '', str(text))

# =========================
# تلوين التشكيل
# =========================
def highlight_tashkeel(text):
    return re.sub(
        r'([\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED])',
        r'<span style="color:#CFA500; font-weight:bold;">\1</span>',
        text
    )

# =========================
# توحيد الهمزات
# =========================
def normalize_hamza_to_alif(text):
    return re.sub(r"[أإآؤئء]", "ا", text)

# =========================
# 🔥 البحث الجديد (بدون ع/غ)
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
    files = {0: {"name": "القرآن كله", "path": None}}

    for file in os.listdir("data"):
        if file.endswith(".xlsx"):
            num = int(re.match(r"^(\d+)", file).group(1))
            files[num] = {
                "name": clean_surah_name(file),
                "path": os.path.join("data", file)
            }

    return dict(sorted(files.items()))

surah_files = get_surah_files()
surah_names = [v["name"] for v in surah_files.values()]
selected_surah = st.sidebar.selectbox("اختر السورة", surah_names)

def get_path(name):
    for v in surah_files.values():
        if v["name"] == name:
            return v["path"]

# =========================
# تحميل البيانات
# =========================
@st.cache_data
def load_data(name):
    if name == "القرآن كله":
        all_df = []
        for v in surah_files.values():
            if v["path"] is None:
                continue

            df = pd.read_excel(v["path"])
            surah_id = int(re.match(r"^(\d+)", os.path.basename(v["path"])).group(1))
            df["surah_id"] = surah_id
            df["surah_name"] = v["name"]
            all_df.append(df)

        return pd.concat(all_df).sort_values(["surah_id","ayah_number"]).reset_index(drop=True)

    else:
        path = get_path(name)
        df = pd.read_excel(path)
        df["surah_name"] = name
        return df.sort_values("ayah_number").reset_index(drop=True)

df = load_data(selected_surah)

# =========================
# الإحصاءات (مهم جدًا)
# =========================
if selected_surah == "القرآن كله":
    stats_df = (
        df.groupby(["surah_id","surah_name"])["ayah_number"]
        .max()
        .reset_index()
        .rename(columns={
            "surah_id":"رقم السورة",
            "surah_name":"اسم السورة",
            "ayah_number":"عدد الآيات"
        })
    )

    total = stats_df["عدد الآيات"].sum()

    st.markdown(f"""
    <div style="background:black;padding:15px;border-radius:10px;text-align:center;">
        <h3>📖 إجمالي عدد الآيات</h3>
        <h1 style="color:white;">{total}</h1>
    </div>
    """, unsafe_allow_html=True)

# =========================
# العنوان
# =========================
st.markdown(f"""
<h2 style='text-align:center;'>📖 {selected_surah}</h2>
""", unsafe_allow_html=True)

# =========================
# نوع البحث
# =========================
search_type = st.radio(
    "اختر نوع البحث",
    ["بحث جديد","بحث بالكلمة","بحث برقم الآية","عرض السورة كاملة","بحث حروف الكلمة","بحث الحروف الأصلية"],
    horizontal=True
)

# =========================
# 🔥 البحث الجديد
# =========================
if search_type == "بحث جديد":

    query = st.text_input("اكتب الحروف")

    if query:
        user = normalize_letters_for_new_search(query)
        user_unique = "".join(sorted(set(user)))

        results = []
        for _, row in df.iterrows():
            ayah = normalize_letters_for_new_search(row["ayah_text"])
            if "".join(sorted(set(ayah))) == user_unique:
                results.append(row)

        st.write("عدد النتائج:", len(results))

        for r in results:
            st.markdown(f"""
            <b>{r['surah_name']} ({r['ayah_number']})</b><br>
            {highlight_tashkeel(r['ayah_text'])}
            <hr>
            """, unsafe_allow_html=True)

# =========================
# 🔎 بحث بالكلمة
# =========================
elif search_type == "بحث بالكلمة":

    word = st.text_input("اكتب الكلمة")

    if word:
        clean = normalize_letters_for_new_search(word)

        results = df[df["ayah_text"].apply(
            lambda x: clean in normalize_letters_for_new_search(x)
        )]

        for _, r in results.iterrows():
            st.markdown(f"""
            <b>{r['surah_name']} ({r['ayah_number']})</b><br>
            {highlight_tashkeel(r['ayah_text'])}
            <hr>
            """, unsafe_allow_html=True)

# =========================
# 🔢 بحث آية
# =========================
elif search_type == "بحث برقم الآية":

    num = st.number_input("رقم الآية", 1, int(df["ayah_number"].max()))

    res = df[df["ayah_number"] == num]

    for _, r in res.iterrows():
        st.markdown(f"""
        <b>{r['surah_name']} ({r['ayah_number']})</b><br>
        {highlight_tashkeel(r['ayah_text'])}
        """, unsafe_allow_html=True)

# =========================
# 📖 عرض السورة
# =========================
elif search_type == "عرض السورة كاملة":

    for _, r in df.iterrows():
        st.markdown(f"""
        <b>{r['surah_name']} ({r['ayah_number']})</b><br>
        {highlight_tashkeel(r['ayah_text'])}
        """, unsafe_allow_html=True)

# =========================
# 🔠 بحث الحروف الأصلية
# =========================
elif search_type == "بحث الحروف الأصلية":

    for _, r in df.iterrows():
        lets = extract_original_letters(r["ayah_text"])
        st.markdown(f"""
        <b>{r['surah_name']} ({r['ayah_number']})</b><br>
        <span style="color:green;font-weight:bold;">{lets}</span>
        <hr>
        """, unsafe_allow_html=True)

# =========================
# الفوتر
# =========================
try:
    footer_img = Image.open("assets/footer.png")
    st.image(footer_img)
except:
    st.warning("⚠ لم يتم العثور على صورة الفوتر")
