import re
import pandas as pd
import numpy as np

# -------------------------------------------------------------
# 1. HÀM CHUẨN HÓA MỨC LƯƠNG (clean_salary)
# -------------------------------------------------------------
def clean_salary(val):
    """
    Chuẩn hóa chuỗi lương thô thành (min_salary, max_salary) đơn vị Triệu VNĐ.
    Xử lý các mẫu: '15 - 25 triệu', 'Tới 40 triệu', 'Dưới 15 triệu', 'Thoả thuận'
    """
    if pd.isna(val) or "thoả thuận" in str(val).lower() or "thỏa thuận" in str(val).lower():
        return np.nan, np.nan
    
    text = str(val).lower().replace(",", ".").strip()
    
    # Tìm tất cả các số trong chuỗi (ví dụ: '15 - 25 triệu' -> [15.0, 25.0])
    nums = [float(n) for n in re.findall(r"\d+(?:\.\d+)?", text)]
    
    if not nums:
        return np.nan, np.nan
    
    if "-" in text or "đến" in text or "tới" in text and len(nums) >= 2:
        return nums[0], nums[1]
    elif "tới" in text or "dưới" in text or "lên tới" in text:
        return np.nan, nums[0]
    elif "trên" in text or "từ" in text:
        return nums[0], np.nan
    elif len(nums) == 1:
        return nums[0], nums[0]
        
    return np.nan, np.nan

# -------------------------------------------------------------
# 2. HÀM CHUẨN HÓA NĂM KINH NGHIỆM (handle_missing_experience)
# -------------------------------------------------------------
def handle_missing_experience(df):
    """
    Xử lý missing value ở cột experience và phân nhóm kinh nghiệm.
    """
    df = df.copy()
    # Xử lý 186 dòng null
    df["experience_cleaned"] = df["experience"].fillna("Không yêu cầu kinh nghiệm")
    
    def categorize_exp(val):
        val_str = str(val).lower()
        if "không yêu cầu" in val_str or "chưa có" in val_str:
            return "Không yêu cầu"
        nums = re.findall(r"\d+", val_str)
        if nums:
            years = int(nums[0])
            if years < 1:
                return "Dưới 1 năm"
            elif 1 <= years <= 2:
                return "1 - 2 năm"
            elif 3 <= years <= 5:
                return "3 - 5 năm"
            else:
                return "Trên 5 năm"
        return "Khác"
        
    df["exp_level"] = df["experience_cleaned"].apply(categorize_exp)
    return df

# -------------------------------------------------------------
# 3. HÀM TRÍCH XUẤT KỸ NĂNG BẰNG REGEX (extract_skills)
# -------------------------------------------------------------
# Bộ từ điển kỹ năng IT chuẩn hóa
SKILL_PATTERNS = {
    "Python": r"\b(python|py)\b",
    "Java": r"\bjava\b(?!\s*script)",
    "JavaScript": r"\b(javascript|js|es6)\b",
    "TypeScript": r"\b(typescript|ts)\b",
    "C#/.NET": r"\b(c#|\.net|dotnet|asp\.net)\b",
    "C++": r"\b(c\+\+)\b",
    "PHP": r"\b(php|laravel)\b",
    "Golang": r"\b(golang|go)\b",
    "React/ReactJS": r"\b(react|reactjs|react\.js)\b",
    "VueJS": r"\b(vue|vuejs)\b",
    "NodeJS": r"\b(node|nodejs|node\.js)\b",
    "Flutter": r"\b(flutter)\b",
    "Mobile (Android/iOS)": r"\b(android|ios|mobile|swift|kotlin)\b",
    "Unity/Game": r"\b(unity|unity3d|game)\b",
    "SQL/Database": r"\b(sql|mysql|postgresql|oracle|mongodb|nosql)\b",
    "Data/AI": r"\b(data|ai|machine learning|deep learning|ba|bi)\b",
    "DevOps/Cloud": r"\b(devops|docker|kubernetes|aws|azure|cloud|ci/cd)\b"
}

def extract_skills_from_title(title_text):
    """
    Bóc tách danh sách kỹ năng từ cột title dựa trên từ điển Regex.
    """
    found_skills = []
    if pd.isna(title_text):
        return found_skills
        
    text_clean = str(title_text).lower()
    for skill_name, pattern in SKILL_PATTERNS.items():
        if re.search(pattern, text_clean, re.IGNORECASE):
            found_skills.append(skill_name)
            
    return found_skills

# -------------------------------------------------------------
# 4. CHẠY THỬ NGHIỆM VÀ XUẤT FILE TRUNG GIAN
# -------------------------------------------------------------
if __name__ == "__main__":
    # Đọc dữ liệu thô
    df = pd.read_csv("topcv_jobs.csv")
    print(f"-> Đã đọc {len(df)} dòng dữ liệu.")
    
    # Chuẩn hóa lương
    salary_parsed = df["salary"].apply(clean_salary)
    df["min_salary"] = [s[0] for s in salary_parsed]
    df["max_salary"] = [s[1] for s in salary_parsed]
    
    # Chuẩn hóa kinh nghiệm
    df = handle_missing_experience(df)
    
    # Xuất file trung gian cleaned_jobs.csv
    df.to_csv("cleaned_jobs.csv", index=False, encoding="utf-8-sig")
    print("-> Đã xuất thành công: cleaned_jobs.csv")
    
    # Trích xuất kỹ năng
    df["skills"] = df["title"].apply(extract_skills_from_title)
    
    # Xuất file trung gian feature_jobs.csv
    df.to_csv("feature_jobs.csv", index=False, encoding="utf-8-sig")
    print("-> Đã xuất thành công: feature_jobs.csv")