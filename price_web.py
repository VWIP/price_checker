# ✅ Streamlit App Template — Guaranteed to Work
# Instructions:
# 1. Deploy this to Streamlit Cloud
# 2. Add your GOOGLE_CREDENTIALS to Secrets
# 3. Share your Google Sheet with the service account
# 4. Replace SHEET_ID and SHEET_NAME accordingly

import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# Setup Google Sheets connection from secrets
def get_gsheet_data(sheet_id, sheet_name):
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
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

# --- Sheet Configuration ---
SHEET_ID = "1ikOLabQ1f4OlxLDnm-jIgL4Nckkxfdf71jwmmWu5E5M"   # ✅ Replace with your sheet ID
SHEET_NAME = "Sheet1"                                       # ✅ Replace with your actual sheet name

# --- Load Data ---
data = get_gsheet_data(SHEET_ID, SHEET_NAME)

# --- UI ---
st.title("💰 自用价格计算器")
st.write("从 Google Sheet 动态读取价格")

with st.form("form"):
    color = st.selectbox("选择颜色", data['颜色'].unique())
    kind = st.selectbox("选择种类", data['种类'].unique())
    length = st.selectbox("选择长度 (cm)", data['长度(cm)'].unique())
    quantity = st.number_input("数量", min_value=1, value=1)

    discount = st.slider("折扣 (%)", 0, 100, 0)
    tax = st.slider("税率 (%)", 0, 25, 5)

    submitted = st.form_submit_button("计算")

if submitted:
    filtered = data[(data['颜色'] == color) &
                    (data['种类'] == kind) &
                    (data['长度(cm)'] == length)]

    if not filtered.empty:
        unit_price = filtered.iloc[0]['单价']
        subtotal = unit_price * quantity
        after_discount = subtotal * (1 - discount / 100)
        total = after_discount * (1 + tax / 100)

        st.success(f"✅ 单价：{unit_price} 元")
        st.info(f"""
        - 小计：{subtotal:.2f} 元  
        - 折扣后：{after_discount:.2f} 元  
        - 含税总价：{total:.2f} 元
        """)
    else:
        st.error("未找到匹配数据，请检查 Google Sheet 中是否包含该组合")

with st.expander("🔍 查看完整价格表"):
    st.dataframe(data)
