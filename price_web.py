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

            available_lengths = data[(data['种类'] == kind) & (data['颜色'] == color)]['长度(cm)'].unique()
            length = st.selectbox(f"选择长度（{kind}）", available_lengths, key=f"length_{kind}")

            quantity = st.number_input(f"数量（{kind}）", min_value=1, value=1, step=1, key=f"qty_{kind}")

            if st.button(f"添加 {kind}", key=f"add_{kind}"):
                match = data[(data['种类'] == kind) & (data['颜色'] == color) & (data['长度(cm)'] == length)]
                if not match.empty:
                    price = match.iloc[0]['单价']
                    st.session_state.order.append({
                        "种类": kind,
                        "颜色": color,
                        "长度(cm)": length,
                        "数量": quantity,
                        "单价": price,
                        "小计": price * quantity
                    })
                else:
                    st.warning("找不到该组合对应的单价")

# 显示订单
st.write("## 🧾 当前订单")
if len(st.session_state.order) == 0:
    st.info("当前没有添加任何商品")
else:
    df_order = pd.DataFrame(st.session_state.order)
    total = df_order["小计"].sum()
    st.dataframe(df_order)
    st.success(f"当前总价：￥{total:.2f}")

    # 删除项
    for i, item in enumerate(st.session_state.order):
        if st.button(f"删除第 {i+1} 项", key=f"del_{i}"):
            st.session_state.order.pop(i)
            st.experimental_rerun()

# 折扣和税率
st.write("## 💸 调整折扣和税率")
discount = st.slider("折扣 (%)", 0, 100, 0)
tax = st.slider("税率 (%)", 0, 25, 5)

if len(st.session_state.order) > 0:
    discounted = total * (1 - discount / 100)
    taxed = discounted * (1 + tax / 100)
    st.info(f"折扣后：￥{discounted:.2f}，含税后总价：￥{taxed:.2f}")