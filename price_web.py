import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# === 从 Google Sheets 获取数据 ===
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
        - 📌 表格是否分享给服务账号
        - 📌 SHEET_ID 是否正确
        - 📌 Sheet 名称是否一致
        """)
        st.exception(e)
        st.stop()

# === Sheet 配置 ===
SHEET_ID = "1ikOLabQ1f4OlxLDnm-jIgL4Nckkxfdf71jwmmWu5E5M"
SHEET_NAME = "Sheet1"
data = get_gsheet_data(SHEET_ID, SHEET_NAME)

# === 初始化 Session State ===
if "order" not in st.session_state:
    st.session_state.order = []

# === 页面标题 ===
st.title("🧾 点单系统")
st.write("点击种类 → 选择颜色 + 长度 → 添加至订单")

# === 菜单选择 ===
st.write("## 📋 菜单")
all_kinds = data['种类'].unique()
cols = st.columns(3)

for idx, kind in enumerate(all_kinds):
    with cols[idx % 3]:
        with st.expander(f"🍽️ {kind}"):
            available_colors = data[data['种类'] == kind]['颜色'].unique()
            color = st.selectbox(f"选择颜色", available_colors, key=f"color_{kind}")

            available_lengths = data[(data['种类'] == kind) & (data['颜色'] == color)]['长度(inch)'].unique()
            length = st.selectbox(f"选择长度（inch）", available_lengths, key=f"length_{kind}")

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
                else:
                    st.warning("⚠️ 表格中找不到该组合")

# === 折扣与税率设置：一行显示 + 可选金额 + 自定义金额 ===
st.write("## 💵 折扣与税率")
col_a, col_b, col_c = st.columns([2, 2, 2])

with col_a:
    discount_mode = st.selectbox("折扣方式", ["固定金额 ($)", "百分比 (%)"], index=0)

with col_b:
    if discount_mode == "固定金额 ($)":
        discount_option = st.selectbox("折扣金额", ["$10", "$15", "$20", "自定义金额"], index=3)
        if discount_option == "自定义金额":
            discount_value = st.number_input("输入金额", min_value=0.0, value=0.0, step=1.0)
        else:
            discount_value = float(discount_option.strip("$"))
    else:
        discount_value = st.slider("折扣百分比 (%)", 0, 100, 0)

with col_c:
    tax = st.number_input("税率 (%)", value=2.7, step=0.1)


# === 当前订单 ===
st.write("## 🧾 当前订单明细")
if st.button("🧹 清空订单"):
    st.session_state.order = []
    st.rerun()

if not st.session_state.order:
    st.info("🕙 当前没有添加任何商品")
else:
    # 表头（7列）
    header_cols = st.columns([1.2, 2, 2, 2.2, 1.5, 1.5, 1])
    headers = ["颜色", "种类", "长度", "数量", "单价", "小计", "删除"]
    for col, h in zip(header_cols, headers):
        col.markdown(f"<span style='font-size:16px; font-weight:600'>{h}</span>", unsafe_allow_html=True)

    # 每一项订单
    for i, row in enumerate(st.session_state.order):
        qty_key = f"qty_input_{i}"
        col1, col2, col3, col4, col5, col6, col7 = st.columns([1.2, 2, 2, 2.2, 1.5, 1.5, 1])

        with col1:
            st.markdown(f"<div style='line-height:2.6'>{row['颜色']}</div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div style='line-height:2.6'>{row['种类']}</div>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div style='line-height:2.6'>{row['长度 (inch)']} inch</div>", unsafe_allow_html=True)
        with col4:
            qty = st.number_input(
                label=" ",
                min_value=1,
                step=1,
                value=row["数量"],
                key=qty_key,
                label_visibility="collapsed"
            )
            st.session_state.order[i]["数量"] = qty
            st.session_state.order[i]["小计 ($)"] = qty * row["单价 ($)"]
        with col5:
            st.markdown(f"<div style='line-height:2.6'>${row['单价 ($)']:.2f}</div>", unsafe_allow_html=True)
        with col6:
            st.markdown(f"<div style='line-height:2.6'>${row['小计 ($)']:.2f}</div>", unsafe_allow_html=True)
        with col7:
            if st.button("🗑️", key=f"del_{i}"):
                st.session_state.order.pop(i)
                st.rerun()

    # === 总价计算 ===
    df_order = pd.DataFrame(st.session_state.order)
    subtotal = df_order["小计 ($)"].sum()

    if discount_mode == "固定金额 ($)":
        discount_amt = discount_value
        after_discount = max(subtotal - discount_amt, 0)
        discount_display = f"**折扣：** -${discount_amt:.2f}"
    else:
        discount_amt = subtotal * (discount_value / 100)
        after_discount = subtotal - discount_amt
        discount_display = f"**折扣：** {discount_value}% → -${discount_amt:.2f}"

    tax_amt = after_discount * (tax / 100)
    total = after_discount + tax_amt

    # === 显示金额汇总 ===
    st.markdown("---")
    st.markdown(f"**原始总价：** ${subtotal:.2f}")
    st.markdown(discount_display)
    st.markdown(f"**税率：** {tax:.1f}% → +${tax_amt:.2f}")
    st.markdown(f"### 🧮 含税总计：🟩 **${total:.2f}**")
