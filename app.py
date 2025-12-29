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
    tashkeel = re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED]')
    return tashkeel.sub('', str(text))

# =========================
# توحيد الهمزات كلها إلى ء
# =========================
def normalize_hamza(text):
    return re.sub(r'[أإآؤئ]', 'ء', text)

# =========================
# استخراج الحروف الأصلية الفريدة للآية
# =========================
def extract_original_letters(ayah):
    txt = remove_tashkeel(ayah)
    txt = normalize_hamza(txt)

    txt = re.sub(r'[^ءابتثجحخدذرزسشصضطظعغفقكلمنهوي]', '', txt)
    txt = txt.replace(" ", "")

    seen = []
    for c in txt:
        if c not in seen:
            seen.append(c)

    return "".join(seen)

# =========================
# تلوين التشكيل الذهبي
# =========================
def highlight_tashkeel(text):
    return re.sub(
        r'([\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED])',
        r'<span style="color:#CFA500; font-weight:bold;">\1</span>', text
    )

# =========================
# تلوين الحروف المطابقة
# =========================
def highlight_chars_as_input(text, keyword):
    keyword_clean = remove_tashkeel(keyword)
    highlighted = ""
    used = []
    for char in text:
        char_clean = remove_tashkeel(char)
        if re.match(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]', char):
            highlighted += f'<span style="color:#CFA500;font-weight:bold;">{char}</span>'
            continue
        if char_clean in keyword_clean and used.count(char_clean) < keyword_clean.count(char_clean):
            highlighted += f'<span style="color:green;font-weight:900;">{char}</span>'
            used.append(char_clean)
        else:
            highlighted += f'<span style="font-weight:900;">{char}</span>'
    return highlighted

# =========================
# قراءة السور
# =========================
def clean_surah_name(name):
    name = re.sub(r'^\d+[_-]*', '', name)
    return re.sub(r'\.xlsx$', '', name).strip()

@st.cache_data
def get_surah_files():
    files = {0: {"name":"القرآن كله","path":None}}
    for f in os.listdir("data"):
        if f.endswith(".xlsx"):
            num = int(re.match(r"^(\d+)", f).group(1))
            files[num] = {"name": clean_surah_name(f.replace(".xlsx","")), "path": "data/"+f}
    return dict(sorted(files.items()))

surah_files = get_surah_files()
surah_list = [v["name"] for v in surah_files.values()]
selected_surah = st.sidebar.selectbox("اختر السورة", surah_list)

def get_file(name):
    for v in surah_files.values():
        if v["name"] == name:
            return v["path"]
    return None

@st.cache_data
def load_data(surah):
    if surah == "القرآن كله":
        all_rows=[]
        for v in surah_files.values():
            if v["path"]:
                df=pd.read_excel(v["path"])
                df["surah_name"]=clean_surah_name(v["name"])
                all_rows.append(df)
        return pd.concat(all_rows).reset_index(drop=True)
    df = pd.read_excel(get_file(surah))
    df["surah_name"]=surah
    return df

df = load_data(selected_surah)

# =========================
# نوع البحث (أضفنا الرابع)
# =========================
search_type = st.radio(
    "اختر نوع البحث",
    ["بحث برقم الآية","عرض السورة كاملة","بحث حروف الكلمة","بحث الحروف الأصلية"],
    horizontal=True
)
st.divider()

# =========================
# 1️⃣ بحث حروف الكلمة
# =========================
if search_type == "بحث حروف الكلمة":
    keyword = st.text_input("اكتب الحروف:")
    if keyword:
        key=remove_tashkeel(keyword)
        match=lambda a: all(remove_tashkeel(a).count(c)>=key.count(c) for c in set(key))
        results=df[df["ayah_text"].apply(match)]
        st.write(f"النتائج: {len(results)}")
        for _,r in results.iterrows():
            st.markdown(f"<b>{r['surah_name']} ({r['ayah_number']})</b><br>"
                        f"{highlight_tashkeel(highlight_chars_as_input(r['ayah_text'],keyword))}<br>",
                        unsafe_allow_html=True)

# =========================
# 2️⃣ بحث برقم الآية
# =========================
elif search_type=="بحث برقم الآية":
    num=st.number_input("رقم الآية",1,int(df["ayah_number"].max()))
    res=df[df["ayah_number"]==num]
    for _,r in res.iterrows():
        st.markdown(f"<b>{r['surah_name']} ({r['ayah_number']})</b><br>"
                    f"{highlight_tashkeel(r['ayah_text'])}<br>",
                    unsafe_allow_html=True)

# =========================
# 3️⃣ عرض السورة كاملة
# =========================
elif search_type=="عرض السورة كاملة":
    for _,r in df.iterrows():
        st.markdown(f"<b>{r['surah_name']} ({r['ayah_number']})</b><br>"
                    f"{highlight_tashkeel(r['ayah_text'])}<br>",
                    unsafe_allow_html=True)

# =========================
# 4️⃣ بحث الحروف الأصلية
# =========================
elif search_type=="بحث الحروف الأصلية":
    st.markdown("### 🔠 الحروف الأصلية بدون تكرار ")
    for _,r in df.iterrows():
        letters = extract_original_letters(r['ayah_text'])
        st.markdown(
            f"<b>{r['surah_name']} ({r['ayah_number']})</b><br>"
            f"<span style='font-size:22px;color:green;font-weight:bold;'>{letters}</span><br><hr>",
            unsafe_allow_html=True
        )

# =========================
# صورة النهاية
# =========================
try:
    st.image("assets/footer.png")
except:
    st.warning("أضف footer.png داخل مجلد assets")
