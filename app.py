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
st.set_page_config(page_title="البحث في القرآن الكريم", page_icon="📖", layout="wide")

st.markdown("""
<style>
* {
    direction: rtl;
    text-align: right !important;
}
.copy-icon:hover{
    color:green;
    cursor:pointer;
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
    tashkeel = re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED]')
    return tashkeel.sub('', str(text))

# =========================
# تلوين التشكيل باللون الذهبي
# =========================
def highlight_tashkeel(text):
    return re.sub(r'([\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED])',
                  r'<span style="color:#CFA500; font-weight:bold;">\1</span>', text)

# =========================
# تنظيف اسم السورة
# =========================
def clean_surah_name(name):
    name = re.sub(r'^\d+[_-]*', '', name)
    name = re.sub(r'\.xlsx$', '', name)
    return name.strip()

# =========================
# إبراز الحروف المتطابقة باللون الأخضر
# =========================
def highlight_chars_as_input(text, keyword):
    keyword_clean = remove_tashkeel(keyword)
    highlighted, used = "", []

    for char in text:
        char_clean = remove_tashkeel(char)

        # تشكيل → ذهبي
        if re.match(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]', char):
            highlighted += f'<span style="color:#CFA500; font-weight:bold;">{char}</span>'
            continue

        # الحروف المطابقة → أخضر
        if char_clean in keyword_clean and used.count(char_clean) < keyword_clean.count(char_clean):
            highlighted += f'<span style="color:green; font-weight:900;">{char}</span>'
            used.append(char_clean)
        else:
            highlighted += f'<span style="font-weight:900;color:black;">{char}</span>'

    return highlighted

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
surah_list = [v["name"] for v in surah_files.values()]
selected_surah = st.sidebar.selectbox("اختر السورة", surah_list)

def get_file(surah_name):
    for v in surah_files.values():
        if v["name"] == surah_name: return v["path"]
    return None

# =========================
# تحميل البيانات
# =========================
@st.cache_data
def load_data(surah):
    if surah == "القرآن كله":
        all_rows = []
        for v in surah_files.values():
            if v["path"]:
                df_t = pd.read_excel(v["path"])
                surah_id = int(re.match(r"^(\d+)", os.path.basename(v["path"])).group(1))
                df_t["surah_id"], df_t["surah_name"] = surah_id, clean_surah_name(v["name"])
                all_rows.append(df_t)
        return pd.concat(all_rows).sort_values(["surah_id","ayah_number"]).reset_index(drop=True)
    else:
        path = get_file(surah)
        df_single = pd.read_excel(path)
        surah_id = int(re.match(r"^(\d+)", os.path.basename(path)).group(1))
        df_single["surah_id"] = surah_id
        df_single["surah_name"] = clean_surah_name(surah)
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
    alert("تم نسخ الآية بنجاح");
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
# عرض آية + تلوين + نسخ
# =========================
def render_ayah(row, keyword=None):
    ayah = row['ayah_text']
    if keyword: ayah = highlight_chars_as_input(ayah, keyword)
    ayah = highlight_tashkeel(ayah)

    st.markdown(f"""
    <div style="padding:10px; border-bottom:1px solid #ddd;">
        <b>{row['surah_name']} ({row['ayah_number']})</b>
        <span class="copy-icon" style="font-size:20px; margin-right:8px;" 
        onclick="copyText('ayah-{row['ayah_number']}')" 
        data-target="ayah-{row['ayah_number']}">📋</span><br>
        <span id="ayah-{row['ayah_number']}" style="font-size:22px; line-height:2;">
        {ayah}</span>
    </div>
    """, unsafe_allow_html=True)

# =========================
# واجهة البحث
# =========================
st.markdown("## 🔎 ابحث في القرآن")
search_type = st.radio("نوع البحث:", ["بحث حروف الكلمة","بحث برقم الآية","عرض السورة كاملة"], horizontal=True)
st.divider()

results = pd.DataFrame()

# بحث بحروف
if search_type == "بحث حروف الكلمة":
    keyword = st.text_input("اكتب الحروف")
    if keyword:
        key = remove_tashkeel(keyword)
        matched = lambda a: all(remove_tashkeel(a).count(c) >= key.count(c) for c in set(key))
        results = df[df["ayah_text"].apply(matched)]
        st.write(f"عدد النتائج: {len(results)}")
        for _, r in results.iterrows(): render_ayah(r, keyword)

# بحث برقم آية
elif search_type == "بحث برقم الآية":
    num = st.number_input("رقم الآية", 1, int(df["ayah_number"].max()))
    results = df[df["ayah_number"] == num]
    for _, r in results.iterrows(): render_ayah(r)

# عرض كامل
elif search_type == "عرض السورة كاملة":
    results = df
    for _, r in results.iterrows(): render_ayah(r)

# =========================
# حفظ TXT / PDF
# =========================
if len(results) > 0:
    txt = "\n".join(f"{r['surah_name']}({r['ayah_number']}): {r['ayah_text']}" for _, r in results.iterrows())
    st.download_button("📥 حفظ TXT", BytesIO(txt.encode()), file_name="نتيجة_البحث.txt")

    pdf_buffer = BytesIO()
    p = canvas.Canvas(pdf_buffer, pagesize=A4)
    p.setFont("Helvetica", 14)
    y = 800
    for _, r in results.iterrows():
        p.drawRightString(550, y, f"{r['surah_name']} ({r['ayah_number']}): {r['ayah_text']}")
        y -= 22
        if y < 50: p.showPage(); p.setFont("Helvetica", 14); y = 800
    p.save(); pdf_buffer.seek(0)
    st.download_button("📄 حفظ PDF", pdf_buffer, file_name="نتيجة_البحث.pdf")

# =========================
# صورة النهاية
# =========================
st.markdown("---")
if os.path.exists("assets/footer.png"):
    st.image("assets/footer.png")
else:
    st.warning("لا يوجد footer.png داخل assets")
