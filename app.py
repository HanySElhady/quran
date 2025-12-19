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
# قراءة ملفات السور من فولدر data
# =========================
@st.cache_data
def get_surah_files():
    files = {}
    for file in os.listdir("data"):
        if file.endswith(".xlsx"):
            # الرقم في بداية الملف
            match = re.match(r"(\d+)", file)
            if match:
                surah_num = int(match.group(1))
            else:
                surah_num = 999  # للقرآن كله في آخر القائمة
            surah_name = file.replace(".xlsx","").replace("_"," ")
            files[surah_num] = {"name": surah_name, "path": os.path.join("data", file)}
    # إضافة خيار القرآن كله في آخر القائمة
    files[1000] = {"name": "القرآن كله", "path": None}
    return dict(sorted(files.items()))

surah_files_dict = get_surah_files()
if not surah_files_dict:
    st.error("لا يوجد ملفات سور داخل مجلد data")
    st.stop()

# =========================
# قائمة السور بالترتيب
# =========================
surah_options = [v["name"] for k,v in surah_files_dict.items()]

# =========================
# اختيار السورة
# =========================
selected_surah = st.sidebar.selectbox(
    "اختر السورة",
    surah_options
)

# =========================
# دالة للحصول على مسار الملف بناءً على اسم السورة
# =========================
def get_file_path_by_name(surah_name, surah_files_dict):
    for v in surah_files_dict.values():
        if v["name"] == surah_name:
            return v["path"]
    return None

# =========================
# تحميل البيانات للسورة أو القرآن كله
# =========================
@st.cache_data
def load_data(selected_surah_name, surah_files_dict):
    if selected_surah_name == "القرآن كله":
        all_rows = []
        for key, v in surah_files_dict.items():
            file_name = v["name"]
            file_path = v["path"]
            if file_path is None:
                continue
            # تجاهل الملف quran_all.xlsx
            if os.path.basename(file_path).lower() == "quran_all.xlsx":
                continue
            df_temp = pd.read_excel(file_path)
            # إضافة اسم السورة لكل صف
            df_temp["surah_name"] = file_name
            all_rows.append(df_temp)
        if all_rows:
            df_all = pd.concat(all_rows, ignore_index=True)
            # ترتيب حسب surah_id ثم ayah_number
            df_all = df_all.sort_values(["surah_id", "ayah_number"]).reset_index(drop=True)
            return df_all
        else:
            return pd.DataFrame(columns=["surah_id", "surah_name", "ayah_number", "ayah_text"])
    else:
        # السورة واحدة
        file_path = get_file_path_by_name(selected_surah_name, surah_files_dict)
        if file_path is None:
            return pd.DataFrame(columns=["surah_id", "surah_name", "ayah_number", "ayah_text"])
        return pd.read_excel(file_path)

# 🔹 استدعاء الدالة لتحميل البيانات
df = load_data(selected_surah, surah_files_dict)

# =========================
# عنوان الصفحة
# =========================
st.markdown(
    f"""
    <div style="background-color:#f0f8ff; padding:15px; border-radius:10px;">
        <h1 style="color:#003366; text-align:center;">📖 البحث في القرآن الكريم</h1>
        <h3 style="color:#006699; text-align:center;">{selected_surah}</h3>
    </div>
    """,
    unsafe_allow_html=True
)
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
# 🔍 بحث بالكلمة
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
            st.markdown(f"**{row['surah_name']} - آية رقم {row['ayah_number']}**")
            st.markdown(
                f'<div style="font-size:18px; line-height:2;">{highlighted_ayah}</div>',
                unsafe_allow_html=True
            )
            export_rows.append({
                "surah_name": row["surah_name"],
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
        st.markdown(f"### {result.iloc[0]['surah_name']} - آية رقم {ayah_number}")
        st.markdown(
            f'<div style="font-size:20px; line-height:2;">{ayah_text}</div>',
            unsafe_allow_html=True
        )

# =========================
# 📖 عرض السورة كاملة
# =========================
elif search_type == "عرض السورة كاملة":
    for _, row in df.iterrows():
        surah_name_clean = row["surah_name"].split("-")[1]  # اسم السورة فقط

        st.markdown(f"**{surah_name_clean} ({row['ayah_number']})**")
        st.markdown(
            f'<div style="font-size:18px; line-height:2;">{row["ayah_text"]}</div>',
            unsafe_allow_html=True
        )


