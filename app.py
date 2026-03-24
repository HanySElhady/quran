import streamlit as st
import pandas as pd
import re
from PIL import Image
import os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import arabic_reshaper
from bidi.algorithm import get_display

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
try:
    header_img = Image.open("assets/header.png")
    st.image(header_img, use_container_width=True)
except:
    pass

# =========================
# أدوات النص
# =========================
def remove_tashkeel(text):
    return re.sub(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]', '', str(text))

def highlight_tashkeel(text):
    return re.sub(
        r'([\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED])',
        r'<span style="color:#CFA500;font-weight:bold;">\1</span>',
        text
    )

def normalize_hamza_to_alif(text):
    return re.sub(r"[أإآؤئء]", "ا", text)

def normalize_for_word_search(text):
    return normalize_hamza_to_alif(remove_tashkeel(text))

# =========================
# البحث الشامل
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
# الحروف الأصلية
# =========================
def extract_original_letters(text):
    text = remove_tashkeel(text)
    text = re.sub(r'[^ءابتثجحخدذرزسشصضطظعغفقكلمنهوي]', '', text)
    seen = []
    for c in text:
        if c not in seen:
            seen.append(c)
    return "".join(seen)

# =========================
# تظليل
# =========================
def highlight_chars(text, keyword):
    k = remove_tashkeel(keyword)
    return "".join(
        f'<span style="color:green;font-weight:bold;">{c}</span>' if remove_tashkeel(c) in k else c
        for c in text
    )

def highlight_chars_normalized(text, keyword):
    k = normalize_letters_for_new_search(keyword)
    used = []
    result = ""

    for c in text:
        cn = normalize_letters_for_new_search(c)
        if cn in k and used.count(cn) < k.count(cn):
            result += f'<span style="color:#CFA500;font-weight:900;">{c}</span>'
            used.append(cn)
        else:
            result += c
    return result

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
    for f in os.listdir("data"):
        if f.endswith(".xlsx"):
            num = int(re.match(r"^(\d+)", f).group(1))
            files[num] = {
                "name": clean_surah_name(f),
                "path": os.path.join("data", f)
            }
    return dict(sorted(files.items()))

surah_files = get_surah_files()
selected_surah = st.sidebar.selectbox("اختر السورة", [v["name"] for v in surah_files.values()])

# =========================
# تحميل البيانات
# =========================
@st.cache_data
def load_data(name):
    rows = []
    for v in surah_files.values():
        if name != "القرآن كله" and v["name"] != name:
            continue
        if v["path"]:
            df = pd.read_excel(v["path"])
            num = int(re.match(r"^(\d+)", os.path.basename(v["path"])).group(1))
            df["surah_id"] = num
            df["surah_name"] = clean_surah_name(v["name"])
            rows.append(df)
    return pd.concat(rows).sort_values(["surah_id","ayah_number"]).reset_index(drop=True)

df = load_data(selected_surah)

# =========================
# 📊 الإحصائيات (ذهبي)
# =========================
st.markdown("## 📊 إحصاءات")

if selected_surah == "القرآن كله":
    stats = (
        df.groupby(["surah_id","surah_name"])["ayah_number"]
        .max()
        .reset_index()
        .rename(columns={
            "surah_id":"رقم السورة",
            "surah_name":"اسم السورة",
            "ayah_number":"عدد الآيات"
        })
    )

    total = stats["عدد الآيات"].sum()

    st.markdown(f"""
    <div style="background:black;padding:15px;border-radius:10px;text-align:center;">
    <h3>📖 إجمالي عدد الآيات</h3>
    <h1 style="color:white;">{total}</h1>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <style>
    .gold-table {
        border-collapse: collapse;
        width: 100%;
        font-size: 20px;
        font-weight: bold;
    }
    .gold-table th, .gold-table td {
        border: 2px solid #CFA500;
        padding: 10px;
        text-align: center;
    }
    .gold-table th {
        background-color: #fff7e6;
        color: #CFA500;
        font-size: 22px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(
        f'<div style="border:3px solid #CFA500;border-radius:10px;padding:5px;">{stats.to_html(index=False, classes="gold-table")}</div>',
        unsafe_allow_html=True
    )

# =========================
# نوع البحث
# =========================
search_type = st.radio(
    "اختر نوع البحث",
    ["بحث برقم الآية","عرض السورة","بحث بالكلمة","بحث بحروف الكلمة","بحث بالحروف شامل","بحث الحروف الأصلية"],
    horizontal=True
)

# =========================
# عرض النتائج
# =========================
def show_results(results, keyword=None, mode="normal"):
    st.markdown(f"### 📌 عدد النتائج: {len(results)}")
    for _, r in results.iterrows():
        text = r["ayah_text"]

        if keyword:
            if mode == "chars":
                text = highlight_chars(text, keyword)
            elif mode == "normalized":
                text = highlight_chars_normalized(text, keyword)

        text = highlight_tashkeel(text)

        st.markdown(
            f"<b>{r['surah_name']} ({r['ayah_number']})</b><br>{text}<hr>",
            unsafe_allow_html=True
        )

# =========================
# دالة تصدير PDF
# =========================
def export_to_pdf_arabic_long(df, search_term, filename="نتائج.pdf"):
    font_path = os.path.join(os.path.dirname(__file__), "assets", "fonts", "Amiri-Regular.ttf")
    pdfmetrics.registerFont(TTFont('Amiri', font_path))
    
    doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    
    styles = getSampleStyleSheet()
    arabic_style = ParagraphStyle(
        'Arabic',
        parent=styles['Normal'],
        fontName='Amiri',
        fontSize=10,
        leading=24,
        alignment=2,  # 2 = RIGHT alignment
    )
    
    elements = []
    
    # العنوان
    reshaped_title = arabic_reshaper.reshape(f"نتائج البحث عن: {search_term}")
    bidi_title = get_display(reshaped_title)
    elements.append(Paragraph(f"<b>{bidi_title}</b>", arabic_style))
    elements.append(Spacer(-1, 8))
    
    # الآيات
    for _, row in df.iterrows():
        ayah_text = f"{row['surah_name']} ({row['ayah_number']}): {row['ayah_text']}"
        reshaped_text = arabic_reshaper.reshape(ayah_text)
        bidi_text = get_display(reshaped_text)
        elements.append(Paragraph(bidi_text, arabic_style))
        elements.append(Spacer(-1, 8))
    
    doc.build(elements)
    return filename

# =========================
# أنواع البحث
# =========================
if search_type == "عرض السورة":
    show_results(df)

elif search_type == "بحث بالكلمة":
    k = st.text_input("اكتب الكلمة")
    if k:
        res = df[df["ayah_text"].apply(lambda x: normalize_for_word_search(k) in normalize_for_word_search(x))]
        show_results(res, k)

elif search_type == "بحث بحروف الكلمة":
    k = st.text_input("بحث بحروف الكلمة")
    if k:
        kk = remove_tashkeel(k)
        res = df[df["ayah_text"].apply(lambda x: all(x.count(c) >= kk.count(c) for c in set(kk)))]
        show_results(res, k, "chars")
        if not res.empty:
            if st.button("تصدير النتائج إلى PDF"):
                filename = export_to_pdf_arabic_long(res, k)
                with open(filename, "rb") as f:
                    st.download_button("تحميل PDF", f, file_name=filename)

elif search_type == "بحث بالحروف شامل":
    k = st.text_input("بحث بالحروف شامل")
    if k:
        kk = normalize_letters_for_new_search(k)
        res = df[df["ayah_text"].apply(lambda x: all(normalize_letters_for_new_search(x).count(c) >= kk.count(c) for c in set(kk)))]
        show_results(res, k, "normalized")
        if not res.empty:
            if st.button("تصدير النتائج إلى PDF"):
                filename = export_to_pdf_arabic_long(res, k)
                with open(filename, "rb") as f:
                    st.download_button("تحميل PDF", f, file_name=filename)

elif search_type == "بحث الحروف الأصلية":
    st.markdown("### 🔠 البحث بالحروف الأصلية")
    user_input = st.text_input("اكتب آية أو كلمة لاستخراج الحروف الأصلية ثم البحث بها", placeholder="مثال: الحمد لله رب العالمين")
    if user_input:
        extracted = extract_original_letters(user_input)
        st.markdown(f"### الحروف الأصلية المستخرجة: **{extracted}**")
        st.divider()
        def match_original(ayah):
            ayah_letters = extract_original_letters(ayah)
            return all(ayah_letters.count(c) >= extracted.count(c) for c in set(extracted))
        results = df[df["ayah_text"].apply(match_original)]
        for _, r in results.iterrows():
            st.markdown(
                f"""
                <b>{r['surah_name']} ({r['ayah_number']})</b><br>
                <span style="color:green;font-weight:bold;">
                    {extract_original_letters(r['ayah_text'])}
                </span><br>
                {highlight_tashkeel(r['ayah_text'])}
                <hr>
                """,
                unsafe_allow_html=True
            )

elif search_type == "بحث برقم الآية":
    num = st.number_input("رقم الآية", 1)
    res = df[df["ayah_number"] == num]
    show_results(res)

# =========================
# Footer
# =========================
try:
    footer_img = Image.open("assets/footer.png")
    st.image(footer_img)
except:
    pass
