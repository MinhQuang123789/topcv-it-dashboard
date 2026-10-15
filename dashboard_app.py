"""
GIAO DIỆN WEB DASHBOARD TUYỂN DỤNG IT BẰNG STREAMLIT
Sinh viên: Đồng Quang Minh (2374802010308)
"""
import re
import pandas as pd
import numpy as np
import streamlit as st

# CẤU HÌNH TRANG WEB
st.set_page_config(page_title="Vietnam IT Job Dashboard", page_icon="📊", layout="wide")

st.markdown("""
<style>
    .main-title { font-size: 26px; font-weight: 800; color: #1e3a8a; margin-bottom: 5px; }
    .wc-container { background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 12px; padding: 20px; text-align: center; line-height: 2.5; }
    .wc-tag { display: inline-block; margin: 4px 8px; padding: 5px 14px; border-radius: 20px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# HÀM XỬ LÝ DỮ LIỆU TỰ ĐỘNG
@st.cache_data(show_spinner="Đang xử lý dữ liệu...")
def load_and_process():
    df = pd.read_csv("topcv_jobs.csv")
    df = df.drop_duplicates(subset=["title", "company", "location", "date_posted"]).reset_index(drop=True)
    df["date_posted"] = pd.to_datetime(df["date_posted"])

    # Xử lý kinh nghiệm
    def clean_exp(val, title):
        if pd.isna(val):
            if any(k in str(title).lower() for k in ["senior", "lead"]): return "Senior"
            if "middle" in str(title).lower(): return "Middle"
            if "junior" in str(title).lower(): return "Junior"
            return "Intern/Fresher"
        v = str(val).lower()
        if "dưới 1 năm" in v: return "Intern/Fresher"
        nums = re.findall(r"\d+", v)
        if nums:
            y = float(nums[0])
            if y == 1: return "Junior"
            if 2 <= y <= 3: return "Middle"
            return "Senior"
        return "Intern/Fresher"
    
    df["exp_level"] = df.apply(lambda r: clean_exp(r["experience"], r["title"]), axis=1)

    # Xử lý khu vực
    df["region_group"] = df["location"].apply(lambda loc: "Hà Nội" if "Hà Nội" in str(loc) else ("TP.HCM" if "Hồ Chí Minh" in str(loc) else "Tỉnh thành khác"))

    # Xử lý lương
    def clean_salary(val):
        if pd.isna(val) or "thỏa thuận" in str(val).lower(): return np.nan
        s = str(val).lower().replace(",", "")
        nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", s)]
        if not nums: return np.nan
        conv = [round(n/1e6, 2) if n >= 1e6 else (round(n*0.0254, 2) if "usd" in s or "$" in s else round(n, 2)) for n in nums]
        mn, mx = (conv[0], conv[1]) if len(conv) >= 2 else (conv[0], conv[0])
        if "tới" in s: mn = np.nan
        if "từ" in s: mx = np.nan
        if np.nanmean([mn, mx]) > 200: return np.nan
        return np.nanmean([mn, mx])
    
    df["avg_salary"] = df["salary"].apply(clean_salary)

    # Trích xuất kỹ năng
    skills_map = {
        "BA/PM/Product": r"\b(ba|business analyst|pm|product owner|scrum)\b",
        "Mobile": r"\b(flutter|android|ios|swift|kotlin|react native)\b",
        "QA/Tester": r"\b(tester|qa|qc)\b",
        "DevOps/Cloud": r"\b(devops|cloud|aws|azure|docker|k8s|linux)\b",
        "Java": r"\bjava\b(?!\s*script)", "Python": r"\b(python|py)\b",
        "Data/AI": r"\b(data|ai|machine learning|nlp)\b",
        "React": r"\b(react|reactjs)\b", "NodeJS": r"\b(node|nodejs)\b",
        "C#/.NET": r"\b(c#|\.net)\b", "PHP": r"\b(php|laravel)\b"
    }
    df["skills_list"] = df["title"].apply(lambda t: [k for k, p in skills_map.items() if re.search(p, str(t), re.I)] or ["Khác"])
    
    return df

df = load_and_process()

# THANH BÊN (SIDEBAR) BỘ LỌC
st.sidebar.markdown("### 🔍 BỘ LỌC DỮ LIỆU")
kw = st.sidebar.text_input("Từ khóa (Tiêu đề):", "").lower()
reg = st.sidebar.selectbox("Khu vực:", ["Tất cả", "Hà Nội", "TP.HCM", "Tỉnh thành khác"])
exp = st.sidebar.selectbox("Kinh nghiệm:", ["Tất cả", "Intern/Fresher", "Junior", "Middle", "Senior"])
skills = st.sidebar.multiselect("Kỹ năng IT:", sorted(list({s for l in df["skills_list"] for s in l if s != "Khác"})))

f_df = df.copy()
if kw: f_df = f_df[f_df["title"].str.lower().str.contains(kw)]
if reg != "Tất cả": f_df = f_df[f_df["region_group"] == reg]
if exp != "Tất cả": f_df = f_df[f_df["exp_level"] == exp]
if skills: f_df = f_df[f_df["skills_list"].apply(lambda sl: any(k in sl for k in skills))]

# GIAO DIỆN CHÍNH
st.markdown('<div class="main-title">📊 DASHBOARD PHÂN TÍCH TUYỂN DỤNG IT TOPCV</div>', unsafe_allow_html=True)
k1, k2, k3 = st.columns(3)
k1.metric("Số lượng tin đăng", f"{len(f_df):,} tin")
mean_s = f_df["avg_salary"].mean()
k2.metric("Mức lương trung bình", f"{mean_s:.1f} Tr VNĐ" if pd.notna(mean_s) else "Thỏa thuận")
k3.metric("Khu vực phổ biến", f_df["region_group"].mode()[0] if len(f_df)>0 else "N/A")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📌 Phân Tích (EDA) & Word Cloud", "🎯 Ước Lượng Lương", "📋 Dữ Liệu Dạng Bảng"])

with tab1:
    c1, c2 = st.columns([1.2, 1])
    with c1:
        st.subheader("Top Công Nghệ Tuyển Dụng")
        sk_counts = f_df.explode("skills_list").loc[lambda x: x["skills_list"] != "Khác"]["skills_list"].value_counts()
        if not sk_counts.empty: st.bar_chart(sk_counts, color="#2563eb")
        
    with c2:
        st.subheader("Word Cloud Kỹ Năng")
        if not sk_counts.empty:
            colors = ["#1d4ed8", "#047857", "#b45309", "#7c3aed", "#be123c"]
            tags = "".join([f'<span class="wc-tag" style="font-size:{int(14 + (c-sk_counts.min())/(sk_counts.max()-sk_counts.min()+1)*20)}px; background:{colors[i%5]}15; color:{colors[i%5]}; border:1px solid {colors[i%5]}50;">{k} ({c})</span>' for i, (k, c) in enumerate(sk_counts.items())])
            st.markdown(f'<div class="wc-container">{tags}</div>', unsafe_allow_html=True)

    st.subheader("Lương trung bình theo Kinh nghiệm (Triệu VNĐ)")
    sal_exp = f_df.groupby("exp_level")["avg_salary"].mean().reindex(["Intern/Fresher", "Junior", "Middle", "Senior"]).dropna()
    st.bar_chart(sal_exp, color="#059669")

with tab2:
    st.subheader("🎯 Máy Tính Ước Lượng Lương")
    e_exp = st.selectbox("Chọn Kinh nghiệm:", ["Intern/Fresher", "Junior", "Middle", "Senior"], 1)
    e_reg = st.selectbox("Chọn Khu vực:", ["Hà Nội", "TP.HCM", "Tỉnh thành khác"])
    
    base = {"Intern/Fresher": 10.5, "Junior": 17.5, "Middle": 26.0, "Senior": 41.0}[e_exp]
    mult = {"Hà Nội": 1.03, "TP.HCM": 1.05, "Tỉnh thành khác": 0.88}[e_reg]
    est = base * mult
    
    st.success(f"💡 **Mức lương tham khảo cho {e_exp} tại {e_reg}:** {round(est, 1)} Triệu VNĐ (Dao động: {round(est*0.85, 1)} - {round(est*1.15, 1)} Triệu)")

with tab3:
    st.subheader(f"Danh sách {len(f_df)} tin tuyển dụng")
    st.dataframe(f_df[["title", "company", "region_group", "exp_level", "avg_salary", "date_posted"]], use_container_width=True)
    st.download_button("📥 Tải Báo Cáo CSV", f_df.to_csv(index=False).encode("utf-8-sig"), "dashboard_report.csv", "text/csv")