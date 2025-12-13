import streamlit as st
import pandas as pd
import re
from io import BytesIO

# =========================
# إعداد الصفحة
# =========================
st.set_page_config(
    page_title="البحث في القرآن الكريم",
    page_icon="📖",
    layout="wide"
)

# =========================
# دالة إزالة التشكيل
# =========================
def remove_tashkeel(text):
    tashkeel = re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED]')
    return tashkeel.sub('', text)

# =========================
# تحميل البيانات
# =========================
@st.cache_data
def load_data():
    try:
        return pd.read_excel("data/surat_al_baqara.xlsx")
    except FileNotFoundError:
        st.error("ملف البيانات غير موجود")
        st.stop()

df = load_data()

# =========================
# العنوان الرئيسي
# =========================
st.title("📖 البحث في القرآن الكريم")
st.subheader("سورة البقرة")
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
# دالة لتلوين الحروف الموجودة في البحث
# =========================
def highlight_chars(original, keyword_clean):
    result = ""
    seen = set()
    for char in original:
        char_clean = remove_tashkeel(char)
        if char_clean in keyword_clean and char_clean not in seen:
            result += f'<span style="color:lightgreen; font-weight:bold;">{char}</span>'
            seen.add(char_clean)
        else:
            result += char
    return result

# =========================
# 🔍 بحث بالكلمة / الحروف
# =========================
if search_type == "بحث بكلمة":
    keyword = st.text_input("اكتب الحروف للبحث داخل الآيات")
    if keyword:
        keyword_clean = remove_tashkeel(keyword)

        # البحث: أي آية تحتوي على جميع الحروف الموجودة في البحث
        def matches_all_chars(ayah):
            ayah_clean = remove_tashkeel(ayah)
            return all(char in ayah_clean for char in keyword_clean)

        results = df[df["ayah_text"].apply(matches_all_chars)]
        st.write(f"عدد النتائج: {len(results)}")

        ayah_list_for_export = []

        # عرض النتائج مباشرة بدون Expander
        for _, row in results.iterrows():
            highlighted_ayah = highlight_chars(row["ayah_text"], keyword_clean)
            st.markdown(f"**آية رقم {row['ayah_number']}**")
            st.markdown(f'<div style="font-size:18px; line-height:2;">{highlighted_ayah}</div>', unsafe_allow_html=True)
            ayah_list_for_export.append({"ayah_number": row['ayah_number'], "ayah_text": row['ayah_text']})

        # =========================
        # تصدير النتائج Excel
        # =========================
        excel_buffer = BytesIO()
        pd.DataFrame(ayah_list_for_export).to_excel(excel_buffer, index=False)
        st.download_button(
            label="تصدير النتائج Excel",
            data=excel_buffer.getvalue(),
            file_name="search_results.xlsx",
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
        st.markdown(f'<div style="font-size:20px; line-height:2;">{ayah_text}</div>', unsafe_allow_html=True)

# =========================
# 📖 عرض السورة كاملة
# =========================
elif search_type == "عرض السورة كاملة":
    for _, row in df.iterrows():
        st.markdown(f"**({row['ayah_number']})**")
        st.markdown(f'<div style="font-size:18px; line-height:2;">{row["ayah_text"]}</div>', unsafe_allow_html=True)
