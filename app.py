import streamlit as st
import pandas as pd
import re
from io import BytesIO
from PIL import Image
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# =========================
# إعداد الصفحة + RTL
# =========================
st.set_page_config(
    page_title="البحث في القرآن الكريم",
    page_icon="📖",
    layout="wide"
)

st.markdown("""
<style>
* {
    direction: rtl;
    text-align: right !important;
    font-weight: 800;
}
.copy-icon {
    cursor:pointer; 
    color:#CFA500; 
    font-size:20px; 
    margin-right:8px;
}
</style>
""", unsafe_allow_html=True)

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
    return tashkeel_marks.sub(r'<span style="color:#CFA500;font-weight:bold;">\1</span>', text)

# =========================
# تنظيف اسم السورة
# =========================
def clean_surah_name(name):
    name = re.sub(r'^\d+[_-]*', '', name)
    name = re.sub(r'\.xlsx$', '', name)
    return name.strip()

# =========================
# قراءة ملفات السور
# =========================
@st.cache_data
def get_surah_files():
    files = {0: {"name": "القرآن كله", "path": None}}
    for file in os.listdir("data"):
        if file.endswith(".xlsx"):
            surah_num = int(re.match(r"^(\d+)", file).group(1))
            files[surah_num] = {
                "name": clean_surah_name(file.replace(".xlsx","")),
                "path": os.path.join("data", file)
            }
    return dict(sorted(files.items()))

surah_files = get_surah_files()
surah_options = [v["name"] for v in surah_files.values()]
selected_surah = st.sidebar.selectbox("اختر السورة", surah_options)

def get_file_path(surah_name):
    for v in surah_files.values():
        if v["name"] == surah_name:
            return v["path"]
    return None

# =========================
# تحميل الداتا
# =========================
@st.cache_data
def load_data(surah_name):
    if surah_name == "القرآن كله":
        all_rows = []
        for v in surah_files.values():
            if v["path"]:
                df_temp = pd.read_excel(v["path"])
                surah_id = int(re.match(r"^(\d+)", os.path.basename(v["path"])).group(1))
                df_temp["surah_id"] = surah_id
                df_temp["surah_name"] = clean_surah_name(v["name"])
                all_rows.append(df_temp)
        return pd.concat(all_rows).sort_values(["surah_id","ayah_number"]).reset_index(drop=True)
    else:
        path = get_file_path(surah_name)
        df_single = pd.read_excel(path)
        surah_id = int(re.match(r"^(\d+)", os.path.basename(path)).group(1))
        df_single["surah_id"] = surah_id
        df_single["surah_name"] = clean_surah_name(surah_name)
        return df_single.sort_values("ayah_number").reset_index(drop=True)

df = load_data(selected_surah)

# =========================
# سكربت النسخ + لمس الموبايل
# =========================
st.markdown("""
<script>
function copyText(id){
    const text = document.getElementById(id).innerText;
    navigator.clipboard.writeText(text);
    alert("تم النسخ بنجاح");
}
document.body.addEventListener('touchstart', function(e){
    if(e.target.classList.contains('copy-icon')){
        let id = e.target.getAttribute('data-target');
        navigator.clipboard.writeText(document.getElementById(id).innerText);
        alert("تم النسخ باللمس");
    }
});
</script>
""", unsafe_allow_html=True)

# =========================
# صندوق عرض النتيجة + أيقونة نسخ
# =========================
def render_ayah(row):
    ayah = highlight_tashkeel(row['ayah_text'])
    surah = row['surah_name']
    num = row['ayah_number']
    
    st.markdown(f"""
    <div style="border-bottom:1px solid #ddd; padding:10px;">
        <b>{surah} ({num})</b>
        <span class="copy-icon" onclick="copyText('ayah-{num}')" data-target="ayah-{num}">📋</span>
        <br><span id="ayah-{num}" style="font-size:22px;">{ayah}</span>
    </div>
    """, unsafe_allow_html=True)

# =========================
# واجهة البحث
# =========================
st.markdown("## 🔎 البحث في الآيات")
search_type = st.radio("نوع البحث", ["بحث برقم الآية","عرض السورة كاملة","بحث حروف الكلمة"], horizontal=True)
st.divider()

# بحث الحروف
if search_type == "بحث حروف الكلمة":
    keyword = st.text_input("اكتب الحروف")
    if keyword:
        key_clean = remove_tashkeel(keyword)
        def match(ayah):
            txt = remove_tashkeel(ayah)
            return all(txt.count(c) >= key_clean.count(c) for c in set(key_clean))
        results = df[df["ayah_text"].apply(match)]
        st.write(f"النتائج: {len(results)}")
        for _, r in results.iterrows(): render_ayah(r)

# بحث برقم آية
elif search_type == "بحث برقم الآية":
    num = st.number_input("رقم الآية", min_value=1, max_value=int(df["ayah_number"].max()))
    results = df[df["ayah_number"] == num]
    for _, r in results.iterrows(): render_ayah(r)

# عرض السورة كاملة
elif search_type == "عرض السورة كاملة":
    results = df
    for _, r in results.iterrows(): render_ayah(r)

# =========================
# حفظ TXT / PDF
# =========================
if 'results' in locals() and len(results)>0:
    txt_data = "\n".join(f"{r['surah_name']} ({r['ayah_number']}) - {r['ayah_text']}" for _, r in results.iterrows())
    txt_file = BytesIO(txt_data.encode('utf-8'))
    st.download_button("📥 حفظ TXT", txt_file, "نتيجة_البحث.txt")

    pdf_buffer = BytesIO()
    pdf = canvas.Canvas(pdf_buffer, pagesize=A4)
    pdf.setFont("Helvetica", 14)
    y = 800
    for _, r in results.iterrows():
        line = f"{r['surah_name']} ({r['ayah_number']}) - {r['ayah_text']}"
        pdf.drawRightString(550, y, line)
        y -= 20
        if y < 50: pdf.showPage(); pdf.setFont("Helvetica",14); y=800
    pdf.save(); pdf_buffer.seek(0)

    st.download_button("📥 حفظ PDF", pdf_buffer, "نتيجة_البحث.pdf")

# =========================
# صورة "صدق الله العظيم"
# =========================
st.markdown("---")
try:
    st.image("assets/footer.png", use_container_width=False)
except:
    st.warning("⚠ أضف footer.png داخل assets")
