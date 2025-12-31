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
# تلوين التشكيل باللون الذهبي Bold
# =========================
def highlight_tashkeel(text):
    tashkeel_marks = re.compile(r'([\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED])')
    return tashkeel_marks.sub(r'<span style="color:#CFA500; font-weight:bold;">\1</span>', text)

# =========================
# استخراج الحروف الأصلية
# =========================
def extract_original_letters(ayah):
    txt = remove_tashkeel(ayah)
    txt = normalize_hamza_to_alif(txt)
    txt = re.sub(r'[^ا-ي]', '', txt)  # حذف كل شيء غير الحروف العربية
    letters = []
    for c in txt:
        if c not in letters:
            letters.append(c)
    return "".join(letters)

# =========================
# توحيد الهمزات للبحث الجديد
# =========================
def normalize_hamza(text):
    return re.sub(r'[أإآؤئ]', 'ء', text)

# =========================
# استخراج الحروف الأصلية بدون تكرار
# =========================
def extract_original_letters(ayah):
    txt = remove_tashkeel(ayah)
    txt = normalize_hamza(txt)
    txt = re.sub(r'[^ءابتثجحخدذرزسشصضطظعغفقكلمنهوي]', '', txt)
    txt = txt.replace(" ", "")
    letters = []
    for c in txt:
        if c not in letters:
            letters.append(c)
    return "".join(letters)

# =========================
# توحيد الهمزات وتحويلها إلى "ا"
# =========================
def normalize_hamza_to_alif(text):
    return re.sub(r"[أإآؤئء]", "ا", text)
# =========================
# توحيد الهمزات للبحث الجديد
# =========================
def normalize_hamza(text):
    return re.sub(r'[أإآؤئ]', 'ء', text)

# =========================
# استخراج الحروف الأصلية بدون تكرار
# =========================
def extract_original_letters(ayah):
    txt = remove_tashkeel(ayah)
    txt = normalize_hamza(txt)
    txt = re.sub(r'[^ءابتثجحخدذرزسشصضطظعغفقكلمنهوي]', '', txt)
    txt = txt.replace(" ", "")
    letters = []
    for c in txt:
        if c not in letters:
            letters.append(c)
    return "".join(letters)

# =========================
# تنظيف اسم السورة النهائي
# =========================
def clean_surah_name(name):
    name = re.sub(r'^\d+[_-]*', '', name)
    name = re.sub(r'\.xlsx$', '', name)
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
            files[surah_num] = {"name": surah_name, "path": os.path.join("data", file)}
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
# تحميل الداتا حسب الاختيار
# =========================
@st.cache_data
def load_data(selected_surah_name):
    if selected_surah_name == "القرآن كله":
        all_rows = []
        for k, v in surah_files_dict.items():
            if v["path"] is None:
                continue
            df_temp = pd.read_excel(v["path"])
            file_num_match = re.match(r"^(\d+)", os.path.basename(v["path"]))
            surah_id = int(file_num_match.group(1)) if file_num_match else 999
            df_temp["surah_id"] = surah_id
            df_temp["surah_name"] = clean_surah_name(v["name"])
            all_rows.append(df_temp)
        df_all = pd.concat(all_rows, ignore_index=True).sort_values(["surah_id", "ayah_number"]).reset_index(drop=True)
        return df_all
    else:
        path = get_file_path_by_name(selected_surah_name)
        df_single = pd.read_excel(path)
        file_num_match = re.match(r"^(\d+)", os.path.basename(path))
        surah_id = int(file_num_match.group(1)) if file_num_match else 999
        df_single["surah_id"] = surah_id
        df_single["surah_name"] = clean_surah_name(selected_surah_name)
        return df_single.sort_values("ayah_number").reset_index(drop=True)

df = load_data(selected_surah)

# =========================
# إحصاءات السور والآيات
# =========================
st.markdown("## 📊 إحصاءات")

if selected_surah == "القرآن كله":
    surah_order = df[["surah_id", "surah_name"]].drop_duplicates().sort_values("surah_id").copy()
    surah_order["surah_name"] = surah_order["surah_name"].apply(clean_surah_name)
    stats_df = (
    df.groupby(["surah_id", "surah_name"])["ayah_number"]
    .max()   #<<<< بدل nunique
    .reset_index()
    .rename(columns={"surah_id":"رقم السورة","surah_name":"اسم السورة","ayah_number":"عدد الآيات"})
)

    stats_df = stats_df if 'stats_df' in locals() else None
    total_ayahs = stats_df["عدد الآيات"].sum()
    st.markdown(f"""
        <div style="background-color:black; padding:15px; border-radius:10px; text-align:center;">
            <h3>📖 إجمالي عدد آيات القرآن الكريم</h3>
            <h1 style="color:white;">{total_ayahs}</h1>
        </div>""", unsafe_allow_html=True)
    st.divider()
    st.markdown("### 📘 عدد الآيات في كل سورة بترتيب المصحف")
    
    # =========================
    # جدول إحصاءات بإطار ذهبي
    # =========================
    def render_gold_table_scroll(df, max_rows_visible=15):
        # نحسب ارتفاع الحاوية تقريبا: 40px لكل صف + 45px للرأس
        container_height = max_rows_visible * 40 + 45
        return f"""
        <div style="overflow-x:auto; overflow-y:auto; max-height:{container_height}px; border:3px solid #CFA500; border-radius:10px; padding:5px;">
            {df.to_html(index=False, classes="gold-table", escape=False)}
        </div>
        """

    st.markdown("""
    <style>
    .gold-table {
        border-collapse: collapse;
        width: 100%;
        font-size: 18px;
        font-weight: bold;
    }
    .gold-table th, .gold-table td {
        border: 1px solid #CFA500;
        padding: 8px 12px;
        text-align: center;
    }
    .gold-table th {
        background-color: #fff7e6;
        color: #CFA500;
        font-size: 20px;
    }
    .gold-table tbody tr:hover {
        background-color: #fff3cc;
    }
    </style>
    """, unsafe_allow_html=True)

    # عرض الجدول مع التمرير
    st.markdown(render_gold_table_scroll(stats_df, max_rows_visible=15), unsafe_allow_html=True)
# =========================
# عنوان الصفحة
# =========================
st.markdown(f"""
    <div style="background-color:#f0f8ff; padding:15px; border-radius:10px;">
        <h1 style="color:#003366; text-align:center;">📖 البحث في القرآن الكريم</h1>
        <h3 style="color:#006699; text-align:center;">{clean_surah_name(selected_surah)}</h3>
    </div>""", unsafe_allow_html=True)
st.divider()

# =========================
# نوع البحث
# =========================
search_type = st.radio("اختر نوع البحث", ["بحث برقم الآية", "عرض السورة كاملة", "بحث حروف الكلمة","بحث الحروف الأصلية"], horizontal=True)
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
        # تشكيل → ذهبي
        if re.match(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]', char):
            highlighted += f'<span style="color:#CFA500; font-weight:bold;">{char}</span>'
            continue
        # الحروف المطابقة → أخضر بولد أقوى
        if char_clean in keyword_clean and used.count(char_clean) < keyword_clean.count(char_clean):
            highlighted += f'<span style="color:green; font-weight:900;">{char}</span>'
            used.append(char_clean)
        else:
            # باقي النص → بولد أقوى
            highlighted += f'<span style="font-weight:900;">{char}</span>'
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
                f"<b>{row['surah_name']} ({row['ayah_number']})</b><br>"
                f"{highlight_tashkeel(highlight_chars_as_input(row['ayah_text'], keyword))}<br><br>",
                unsafe_allow_html=True
            )

# =========================
# 🔢 بحث برقم الآية
# =========================
elif search_type == "بحث برقم الآية":
    ayah_number = st.number_input("أدخل رقم الآية", min_value=1, max_value=int(df["ayah_number"].max()), step=1)
    result = df[df["ayah_number"] == ayah_number]
    for _, row in result.iterrows():
        ayah_html = highlight_tashkeel(highlight_chars_as_input(row['ayah_text'], keyword)) if 'keyword' in locals() and keyword else highlight_tashkeel(row['ayah_text'])
        st.markdown(
            f"<b>{row['surah_name']} ({row['ayah_number']})</b><br>"
            f"{ayah_html}<br><br>",
            unsafe_allow_html=True
        )

# =========================
# 📖 عرض السورة كاملة
# =========================
elif search_type == "عرض السورة كاملة":
    for _, row in df.iterrows():
        st.markdown(
            f"<b>{row['surah_name']} ({row['ayah_number']})</b><br>"
            f"{highlight_tashkeel(row['ayah_text'])}<br><br>",
            unsafe_allow_html=True
        )

# =========================
# ⭐ البحث الجديد: الحروف الأصلية ⭐
# =========================
# =========================
# ⭐ البحث بالحروف الأصلية ⭐
# =========================
elif search_type == "بحث الحروف الأصلية":

    st.markdown("### 🔠 البحث بالحروف الأصلية (بدون تكرار – بدون همزات – بدون مسافات)")
    search_letters = st.text_input("اكتب الحروف الأصلية للبحث", placeholder="مثل: الم  | كهعص  | يس  | طسم")

    # -------------------------
    # في حالة عدم كتابة أي شيء → عرض المصحف كامل
    # -------------------------
    if not search_letters:
        st.markdown("#### 📖 عرض الحروف الأصلية لكل آية (بدون بحث)")
        for _, row in df.iterrows():
            ayah_letters = extract_original_letters(row["ayah_text"])
            st.markdown(f"""
                <b>{row['surah_name']} ({row['ayah_number']})</b><br>
                <span style="font-size:22px; color:green; font-weight:bold;">{ayah_letters}</span><br>
            """, unsafe_allow_html=True)
        st.stop()  # إيقاف الكود هنا حتى لا ينفذ الجزء التالي

    # -------------------------
    # عند وجود بحث → نفذ التصفية فقط
    # -------------------------
    user_letters = normalize_hamza_to_alif(remove_tashkeel(search_letters))
    user_letters = re.sub(r'[^ا-ي]', '', user_letters)  # حذف أي شيء غير الحروف
    user_unique = "".join(sorted(set(user_letters)))    # ترتيب وتفريد

    st.markdown(f"### الحروف المعتمدة في البحث: **{user_unique}**")
    st.markdown("---")

    results = []
    for _, row in df.iterrows():
        ayah_letters = extract_original_letters(row["ayah_text"])
        ayah_unique = "".join(sorted(set(normalize_hamza_to_alif(ayah_letters))))

        if ayah_unique == user_unique:
            results.append(row)

    # -------------------------
    # عرض النتائج بدون تكرار
    # -------------------------

    for r in results:
        lets = extract_original_letters(r['ayah_text'])
        st.markdown(f"""
            <b>{r['surah_name']} ({r['ayah_number']})</b><br>
            <span style="font-size:22px; color:green; font-weight:bold;">{lets}</span><br>
            <i>{r['ayah_text']}</i>
            <hr>
        """, unsafe_allow_html=True)


try:
    footer_img = Image.open("assets/footer.png")
    st.image(footer_img, use_container_width=False)
except:
    st.warning("⚠ لم يتم العثور على صورة footer.png داخل مجلد assets")
