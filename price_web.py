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
            length = st.selectbox(f"选择长度（inch）（{kind}）", available_lengths, key=f"length_{kind}")

            quantity = st.number_input(f"数量（{kind}）", min_value=1, value=1, step=1, key=f"qty_{kind}")

            if st.button(f"添加 {kind}", key=f"add_{kind}"):
                match = data[(data['种类'] == kind) & (data['颜色'] == color) & (data['长度(cm)'] == length)]
                if not match.empty:
                    price = match.iloc[0]['单价']
                    st.session_state.order.append({
                        "种类": kind,
                        "颜色": color,
                        "长度 (inch)": length,
                        "数量": quantity,
                        "单价 ($)": price,
                        "小计 ($)": price * quantity
                    })
                else:
                    st.warning("找不到该组合对应的单价")

# 折扣和税率
discount = st.slider("折扣 (%)", 0, 100, 0)
tax = st.number_input("税率 (%)", min_value=0.0, step=0.1, value=2.7)

# 显示订单
st.write("## 🧾 当前订单")
if len(st.session_state.order) == 0:
    st.info("当前没有添加任何商品")
else:
    df_order = pd.DataFrame(st.session_state.order)
    total = df_order["小计 ($)"].sum()
    discount_amount = total * (discount / 100)
    discounted = total - discount_amount
    tax_amount = discounted * (tax / 100)
    taxed = discounted + tax_amount

    # 显示订单数据表（带删除按钮）
    for i in range(len(df_order)):
        col1, col2 = st.columns([9, 1])
        with col1:
            st.write(df_order.iloc[i:i+1].style.format({"单价 ($)": "$ {:.2f}", "小计 ($)": "$ {:.2f}"}))
        with col2:
            if st.button("🗑️", key=f"del_{i}"):
                st.session_state.order.pop(i)
                st.rerun()

    # 添加折扣/税率显示 + 总计
    st.markdown("---")
    st.markdown(f"**原始总价：** $ {total:.2f}")
    st.markdown(f"**折扣：** {discount}% ➡️ 减少 $ {discount_amount:.2f}")
    st.markdown(f"**税率：** {tax}% ➡️ 增加 $ {tax_amount:.2f}")
    st.markdown(f"### 🧮 总计（含税）：🟩 **$ {taxed:.2f}**")
