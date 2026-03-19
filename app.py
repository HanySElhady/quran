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
# توحيد الهمزات → ألف
# =========================
def normalize_hamza_to_alif(text):
    return re.sub(r"[أإآؤئء]", "ا", text)

# =========================
# 🔥 البحث الشامل (توحيد الحروف)
# =========================
def normalize_letters_for_new_search(text):
    text = remove_tashkeel(text)
    text = re.sub(r"[أإآء]", "ا", text)
    text = re.sub(r"[يى]", "ي", text)
    text = re.sub(r"[ةه]", "ه", text)
    text = re.sub(r"[ؤ]", "و", text)
    text = re.sub(r"[غ]", "ع", text)
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
# تجهيز نص للبحث بالكلمة
# =========================
def normalize_for_word_search(text):
    text = remove_tashkeel(text)
    text = normalize_hamza_to_alif(text)
    return text

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
            surah_name = clean_surah_name(file)
            files[surah_num] = {"name": surah_name, "path": os.path.join("data", file)}
    return dict(sorted(files.items()))

surah_files_dict = get_surah_files()
selected_surah = st.sidebar.selectbox("اختر السورة", [v["name"] for v in surah_files_dict.values()])

def get_file_path_by_name(name):
    for v in surah_files_dict.values():
        if v["name"] == name:
            return v["path"]
    return None

# =========================
# تحميل البيانات
# =========================
@st.cache_data
def load_data(name):
    if name == "القرآن كله":
        dfs = []
        for v in surah_files_dict.values():
            if v["path"]:
                df = pd.read_excel(v["path"])
                num = int(re.match(r"^(\d+)", os.path.basename(v["path"])).group(1))
                df["surah_id"] = num
                df["surah_name"] = clean_surah_name(v["name"])
                dfs.append(df)
        return pd.concat(dfs).sort_values(["surah_id","ayah_number"])
    else:
        path = get_file_path_by_name(name)
        df = pd.read_excel(path)
        num = int(re.match(r"^(\d+)", os.path.basename(path)).group(1))
        df["surah_id"] = num
        df["surah_name"] = clean_surah_name(name)
        return df

df = load_data(selected_surah)

# =========================
# نوع البحث
# =========================
search_type = st.radio(
    "اختر نوع البحث",
    ["بحث برقم الآية","عرض السورة كاملة","بحث بالكلمة","بحث حروف الكلمة","بحث الحروف الشاملة","بحث الحروف الأصلية"],
    horizontal=True
)

# =========================
# تظليل
# =========================
def highlight_chars_as_input(text, keyword):
    keyword_clean = remove_tashkeel(keyword)
    result = ""
    for c in text:
        if remove_tashkeel(c) in keyword_clean:
            result += f'<span style="color:green;font-weight:bold;">{c}</span>'
        else:
            result += c
    return result
# =========================
# تظليل متوافق مع البحث الشامل
# =========================
def highlight_chars_normalized(text, keyword):
    keyword_norm = normalize_letters_for_new_search(keyword)
    result = ""
    used = []

    for c in text:
        c_norm = normalize_letters_for_new_search(c)

        if c_norm in keyword_norm and used.count(c_norm) < keyword_norm.count(c_norm):
            result += f'<span style="color:gold;font-weight:900;">{c}</span>'
            used.append(c_norm)
        else:
            result += c

    return result
# =========================
# 🔎 بحث بالكلمة
# =========================
if search_type == "بحث بالكلمة":
    keyword = st.text_input("اكتب الكلمة")
    if keyword:
        results = df[df["ayah_text"].apply(lambda x: normalize_for_word_search(keyword) in normalize_for_word_search(x))]
        st.write(len(results))
        for _, r in results.iterrows():
            st.markdown(f"<b>{r['surah_name']} ({r['ayah_number']})</b><br>{highlight_tashkeel(r['ayah_text'])}", unsafe_allow_html=True)

# =========================
# 🔍 بحث حروف الكلمة
# =========================
elif search_type == "بحث حروف الكلمة":
    keyword = st.text_input("اكتب الحروف")
    if keyword:
        k = remove_tashkeel(keyword)
        results = df[df["ayah_text"].apply(lambda x: all(x.count(c) >= k.count(c) for c in set(k)))]
        st.write(len(results))
        for _, r in results.iterrows():
            st.markdown(f"<b>{r['surah_name']} ({r['ayah_number']})</b><br>{highlight_tashkeel(highlight_chars_as_input(r['ayah_text'], keyword))}", unsafe_allow_html=True)

# =========================
# 🔥 البحث بالحروف الشاملة
# =========================
elif search_type == "بحث الحروف الشاملة":
    keyword = st.text_input("اكتب الحروف (بحث شامل)")

    if keyword:
        k = normalize_letters_for_new_search(keyword)

        def match(ayah):
            a = normalize_letters_for_new_search(ayah)
            return all(a.count(c) >= k.count(c) for c in set(k))

        results = df[df["ayah_text"].apply(match)]

        st.write(len(results))

        for _, r in results.iterrows():
            st.markdown(
                f"<b>{r['surah_name']} ({r['ayah_number']})</b><br>"
                f"{highlight_tashkeel(highlight_chars_normalized(r['ayah_text'], keyword))}",
                unsafe_allow_html=True
            )

# =========================
# 🔢 رقم الآية
# =========================
elif search_type == "بحث برقم الآية":
    num = st.number_input("رقم الآية", 1)
    results = df[df["ayah_number"] == num]
    for _, r in results.iterrows():
        st.markdown(f"<b>{r['surah_name']} ({r['ayah_number']})</b><br>{highlight_tashkeel(r['ayah_text'])}", unsafe_allow_html=True)

# =========================
# 📖 عرض السورة
# =========================
elif search_type == "عرض السورة كاملة":
    for _, r in df.iterrows():
        st.markdown(f"<b>{r['surah_name']} ({r['ayah_number']})</b><br>{highlight_tashkeel(r['ayah_text'])}", unsafe_allow_html=True)

# =========================
# 🔠 الحروف الأصلية
# =========================
elif search_type == "بحث الحروف الأصلية":
    for _, r in df.iterrows():
        st.markdown(f"<b>{r['surah_name']} ({r['ayah_number']})</b><br>{extract_original_letters(r['ayah_text'])}", unsafe_allow_html=True)

# =========================
# Footer
# =========================
try:
    footer_img = Image.open("assets/footer.png")
    st.image(footer_img)
except:
    st.warning("⚠ لم يتم العثور على صورة الفوتر")
