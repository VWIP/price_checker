
# 🍱 Streamlit 点餐系统：移动端优化版
import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# === Google Sheets 读取函数 ===
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
        st.markdown("1. 表格权限已分享  2. SHEET_ID 正确  3. 工作表名称正确")
        st.exception(e)
        st.stop()

# === 配置 ===
SHEET_ID = "1ikOLabQ1f4OlxLDnm-jIgL4Nckkxfdf71jwmmWu5E5M"
SHEET_NAME = "Sheet1"
data = get_gsheet_data(SHEET_ID, SHEET_NAME)

if "order" not in st.session_state:
    st.session_state.order = []
if "selected_discount" not in st.session_state:
    st.session_state.selected_discount = None

# === 页面标题 ===
st.title("🧾 点单系统")

st.markdown("### 🍽️ 菜单")
kinds = data['种类'].unique()
cols = st.columns(len(kinds))
for i, kind in enumerate(kinds):
    with cols[i]:
        with st.expander(f"🍱 {kind}", expanded=False):
            color = st.selectbox("选择颜色", data[data['种类'] == kind]['颜色'].unique(), key=f"color_{kind}")
            length = st.selectbox("选择长度（inch）", data[(data['种类'] == kind) & (data['颜色'] == color)]['长度(inch)'].unique(), key=f"len_{kind}")
            if st.button(f"添加 {kind}", key=f"add_{kind}_{color}_{length}"):
                match = data[(data['种类'] == kind) & (data['颜色'] == color) & (data['长度(inch)'] == length)]
                if not match.empty:
                    price = match.iloc[0]['单价']
                    st.session_state.order.append({
                        "颜色": color,
                        "种类": kind,
                        "长度 (inch)": length,
                        "数量": 1,
                        "单价 ($)": price,
                        "小计 ($)": price
                    })

# === 当前订单明细 ===
st.markdown("### 🧾 当前订单明细")
if st.button("🧹 清空订单"):
    st.session_state.order = []
    st.rerun()

if not st.session_state.order:
    st.info("🕗 当前无订单")
else:
    header = st.columns([1.2, 1.8, 1.6, 2.2, 1.2, 1.2, 0.6])
    labels = ["颜色", "种类", "长度", "数量", "单价", "小计", "删除"]
    for col, label in zip(header, labels):
        col.markdown(f"<div style='font-weight:bold;font-size:15px'>{label}</div>", unsafe_allow_html=True)

    for i, row in enumerate(st.session_state.order):
        col1, col2, col3, col4, col5, col6, col7 = st.columns([1.2, 1.8, 1.6, 2.2, 1.2, 1.2, 0.6])
        with col1:
            st.markdown(f"<div style='line-height:2.2'>{row['颜色']}</div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div style='line-height:2.2'>{row['种类']}</div>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div style='line-height:2.2'>{row['长度 (inch)']} inch</div>", unsafe_allow_html=True)
        with col4:
            qty = st.number_input(" ", min_value=1, step=1, value=row["数量"], key=f"qty_{i}", label_visibility="collapsed")
            st.session_state.order[i]["数量"] = qty
            st.session_state.order[i]["小计 ($)"] = qty * row["单价 ($)"]
        with col5:
            st.markdown(f"<div style='line-height:2.2'>${row['单价 ($)']:.2f}</div>", unsafe_allow_html=True)
        with col6:
            st.markdown(f"<div style='line-height:2.2'>${row['小计 ($)']:.2f}</div>", unsafe_allow_html=True)
        with col7:
            if st.button("🗑️", key=f"del_{i}"):
                st.session_state.order.pop(i)
                st.rerun()

# === 折扣与税率 ===
st.markdown("### 💵 折扣与税率")
col1, col2, col3, col4 = st.columns([1.5, 3.2, 2.5, 2])

with col1:
    st.markdown("**折扣方式**")
    mode = st.selectbox(" ", ["固定金额 ($)", "百分比 (%)"], label_visibility="collapsed")

with col2:
    st.markdown("**折扣金额**")
    b1, b2, b3, b4 = st.columns(4)
    if b1.button("$10"):
        st.session_state.selected_discount = 10
    if b2.button("$15"):
        st.session_state.selected_discount = 15
    if b3.button("$20"):
        st.session_state.selected_discount = 20
    if b4.button("❌ 无折扣"):
        st.session_state.selected_discount = 0

with col3:
    st.markdown("**税率 (%)**")
    tax = st.number_input(" ", value=2.7, step=0.1, label_visibility="collapsed")

# === 价格计算 ===
df_order = pd.DataFrame(st.session_state.order)
subtotal = df_order["小计 ($)"].sum()
discount = st.session_state.selected_discount or 0
if mode == "固定金额 ($)":
    discount_amt = discount
else:
    discount_amt = subtotal * (discount / 100)
after_discount = max(subtotal - discount_amt, 0)
tax_amt = after_discount * (tax / 100)
total = after_discount + tax_amt

# === 汇总显示 ===
st.markdown("---")
st.markdown(f"**原始总价：** ${subtotal:.2f}")
st.markdown(f"**折扣：** -${discount_amt:.2f}")
st.markdown(f"**税率：** {tax:.2f}% → +${tax_amt:.2f}")
st.markdown(f"### 🧮 含税总计：🟩 **${total:.2f}**")