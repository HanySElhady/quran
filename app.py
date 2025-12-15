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
    #layout="wide"
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
# قراءة ملفات السور من فولدر data وترتيبها
# =========================
@st.cache_data
def get_surah_files():
    files = []
    for file in os.listdir("data"):
        if file.endswith(".xlsx"):
            match = re.match(r"(\d+)_", file)
            number = int(match.group(1)) if match else 0
            surah_name = file.replace(".xlsx", "").replace("_", " ")
            files.append((number, surah_name, os.path.join("data", file)))
    # ترتيب القائمة حسب الرقم
    files.sort(key=lambda x: x[0])
    return files  # نعيدها كقائمة مرتبة

surah_files = get_surah_files()

if not surah_files:
    st.error("لا يوجد ملفات سور داخل مجلد data")
    st.stop()

# =========================
# اختيار السورة مع الاحتفاظ بالترتيب
# =========================
surah_names = [name for _, name, _ in surah_files]  # قائمة الأسماء فقط
selected_surah = st.selectbox(
    "اختر السورة",
    surah_names
)

# مسار الملف المختار
selected_file_path = next(path for number, name, path in surah_files if name == selected_surah)# =========================
# تحميل السورة المختارة
# =========================
@st.cache_data
def load_data(file_path):
    return pd.read_excel(file_path)

df = load_data(surah_files[selected_surah])

# =========================
# العنوان الرئيسي
# =========================
st.title("📖 البحث في القرآن الكريم")
st.subheader(selected_surah)
st.divider()

# =========================
# اختيار نوع البحث
# =========================
search_type = st.radio(
    "اختر نوع البحث",
    [
        "بحث بكلمة",
        "بحث برقم الآية",
        "عرض السورة كاملة"
    ],
    horizontal=True
)
st.divider()

# =========================
# تلوين الحروف (بدون تكرار)
# =========================
def highlight_chars(original, keyword_clean):
    result = ""
    seen = set()
    for char in original:
        char_clean = remove_tashkeel(char)
        if char_clean in keyword_clean and char_clean not in seen:
            result += f'<span style="color:green; font-weight:bold;">{char}</span>'
            seen.add(char_clean)
        else:
            result += char
    return result

# =========================
# 🔍 بحث بالكلمة / الحروف (كما هو)
# =========================
if search_type == "بحث بكلمة":
    keyword = st.text_input("اكتب الحروف للبحث داخل الآيات")

    if keyword:
        keyword_clean = remove_tashkeel(keyword)

        def matches_all_chars(ayah):
            ayah_clean = remove_tashkeel(ayah)
            return all(char in ayah_clean for char in keyword_clean)

        results = df[df["ayah_text"].apply(matches_all_chars)]
        st.write(f"عدد النتائج: {len(results)}")

        export_rows = []

        for _, row in results.iterrows():
            highlighted_ayah = highlight_chars(row["ayah_text"], keyword_clean)
            st.markdown(f"**آية رقم {row['ayah_number']}**")
            st.markdown(
                f'<div style="font-size:18px; line-height:2;">{highlighted_ayah}</div>',
                unsafe_allow_html=True
            )

            export_rows.append({
                "ayah_number": row["ayah_number"],
                "ayah_text": row["ayah_text"]
            })

        # تصدير Excel
        if export_rows:
            buffer = BytesIO()
            pd.DataFrame(export_rows).to_excel(buffer, index=False)

            st.download_button(
                label="تصدير النتائج Excel",
                data=buffer.getvalue(),
                file_name=f"{selected_surah}_search_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
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
    if not result.empty:
        ayah_text = result.iloc[0]["ayah_text"]
        st.markdown(f"### آية رقم {ayah_number}")
        st.markdown(
            f'<div style="font-size:20px; line-height:2;">{ayah_text}</div>',
            unsafe_allow_html=True
        )

# =========================
# 📖 عرض السورة كاملة
# =========================
elif search_type == "عرض السورة كاملة":
    for _, row in df.iterrows():
        st.markdown(f"**({row['ayah_number']})**")
        st.markdown(
            f'<div style="font-size:18px; line-height:2;">{row["ayah_text"]}</div>',
            unsafe_allow_html=True
        )


