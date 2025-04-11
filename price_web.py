# 🍱 Streamlit 点餐风格前端 - 商品选择器
import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# 获取 Google Sheet 数据
def get_gsheet_data(sheet_id, sheet_name):
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    try:
        creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(sheet_id).worksheet(sheet_name)
        df = pd.DataFrame(sheet.get_all_records())
        return df
    except Exception as e:
        st.error("❌ 无法连接 Google Sheets，请检查以下内容：")
        st.markdown("""
        - 📌 Google 表格是否分享给了服务账号？
        - 📌 SHEET_ID 是否正确？
        - 📌 工作表名称是否正确？
        """)
        st.exception(e)
        st.stop()

# 配置
SHEET_ID = "1ikOLabQ1f4OlxLDnm-jIgL4Nckkxfdf71jwmmWu5E5M"
SHEET_NAME = "Sheet1"
data = get_gsheet_data(SHEET_ID, SHEET_NAME)

# 初始化 session_state
if "order" not in st.session_state:
    st.session_state.order = []

st.title("🧾 点单系统")
st.write("请选择商品：点击种类进入选项，添加后将在下方汇总。")

# 显示所有种类卡片式选择
all_kinds = data['种类'].unique()
st.write("## 菜单")
cols = st.columns(3)
for idx, kind in enumerate(all_kinds):
    with cols[idx % 3]:
        with st.expander(f"🍽️ {kind}"):
            available_colors = data[data['种类'] == kind]['颜色'].unique()
            color = st.selectbox(f"选择颜色（{kind}）", available_colors, key=f"color_{kind}")

            available_lengths = data[(data['种类'] == kind) & (data['颜色'] == color)]['长度(inch)'].unique()
            length = st.selectbox(f"选择长度（inch）（{kind}）", available_lengths, key=f"length_{kind}")

            # 数量输入统一管理
            quantity = st.number_input("数量", min_value=1, value=1, step=1, key=f"qty_{kind}_{color}_{length}")
