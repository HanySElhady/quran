import streamlit as st
import pandas as pd
import re
import openpyxl
# إعداد الصفحة
st.set_page_config(
    page_title="البحث في القرآن الكريم",
    page_icon="📖",
    layout="wide"
)

# دالة لإزالة التشكيل
def remove_tashkeel(text):
    tashkeel = re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED]')
    return tashkeel.sub('', text)

# تحميل البيانات
@st.cache_data
def load_data():
    try:
        return pd.read_excel("data/surat_al_baqara.xlsx")
    except FileNotFoundError:
        st.error("ملف البيانات غير موجود")
        st.stop()

df = load_data()

# العنوان الرئيسي
st.title("📖 البحث في القرآن الكريم")
st.subheader("سورة البقرة")

st.divider()

# اختيار نوع البحث
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
# 🔍 بحث بالحروف بغض النظر عن الترتيب مع تلوين
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

        # تلوين الحروف الموجودة في كلمة البحث
        def highlight_chars(original, keyword_clean):
            result = ""
            for char in original:
                if remove_tashkeel(char) in keyword_clean:
                    result += f'<span style="color:red;">{char}</span>'
                else:
                    result += char
            return result

        for _, row in results.iterrows():
            highlighted_ayah = highlight_chars(row["ayah_text"], keyword_clean)
            st.markdown(
                f"""
                **({row.ayah_number})**
                <div style="font-size:18px; line-height:2;">
                {highlighted_ayah}
                </div>
                """,
                unsafe_allow_html=True
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
        st.markdown(
            f"""
            ### آية رقم {ayah_number}
            <div style="font-size:20px; line-height:2;">
            {ayah_text}
            </div>
            """,
            unsafe_allow_html=True
        )

# =========================
# 📖 عرض السورة كاملة
# =========================
elif search_type == "عرض السورة كاملة":
    for _, row in df.iterrows():
        st.markdown(
            f"""
            **({row.ayah_number})**
            <div style="font-size:18px; line-height:2;">
            {row["ayah_text"]}
            </div>
            """,
            unsafe_allow_html=True
        )

