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

            if st.button(f"添加 {kind}", key=f"add_{kind}_{color}_{length}"):
                match = data[(data['种类'] == kind) & (data['颜色'] == color) & (data['长度(inch)'] == length)]
                if not match.empty:
                    price = match.iloc[0]['单价']
                    st.session_state.order.append({
                        "种类": kind,
                        "颜色": color,
                        "长度 (inch)": length,
                        "数量": 1,
                        "单价 ($)": price,
                        "小计 ($)": price
                    })
                else:
                    st.warning("找不到该组合对应的单价")

# 折扣和税率
discount = st.slider("折扣 (%)", 0, 100, 0)
tax = st.number_input("税率 (%)", min_value=0.0, step=0.1, value=2.7)

# 当前订单
st.write("## 🧾 当前订单")
if st.button("🧹 清空订单"):
    st.session_state.order = []
    st.rerun()

if len(st.session_state.order) == 0:
    st.info("当前没有添加任何商品")
else:
    st.markdown("### 当前订单明细")

# 表头
header_cols = st.columns([1.2, 2, 2, 2, 2.8, 1])
header_labels = ["颜色", "种类", "长度", "数量", "单价 + 小计", "删除"]
for col, label in zip(header_cols, header_labels):
    col.markdown(f"**{label}**")

# 每一行订单项
for i, item in enumerate(st.session_state.order):
    row = item
    qty_key = f"qty_input_{i}"
    col1, col2, col3, col4, col5, col6 = st.columns([1.2, 2, 2, 2, 2.8, 1])

    with col1:
        st.markdown(f"{row['颜色']}")
    with col2:
        st.markdown(f"{row['种类']}")
    with col3:
        st.markdown(f"{row['长度 (inch)']} inch")
    with col4:
        updated_qty = st.number_input(
            label=" ",
            min_value=1,
            value=row["数量"],
            step=1,
            key=qty_key,
            label_visibility="visible"  # ✅ 修复 +/- 不显示的问题
        )
        st.session_state.order[i]["数量"] = updated_qty
        st.session_state.order[i]["小计 ($)"] = updated_qty * row["单价 ($)"]
    with col5:
        st.markdown(f"${row['单价 ($)']:.2f} ｜ ${st.session_state.order[i]['小计 ($)']:.2f}")
    with col6:
        if st.button("🗑️", key=f"del_{i}"):
            st.session_state.order.pop(i)
            st.rerun()


    # 汇总统计
    df_order = pd.DataFrame(st.session_state.order)
    total = df_order["小计 ($)"].sum()
    discount_amount = total * (discount / 100)
    discounted = total - discount_amount
    tax_amount = discounted * (tax / 100)
    taxed = discounted + tax_amount

    st.markdown("---")
    st.markdown(f"**原始总价：** $ {total:.2f}")
    st.markdown(f"**折扣：** {discount}% ➡️ 减少 $ {discount_amount:.2f}")
    st.markdown(f"**税率：** {tax}% ➡️ 增加 $ {tax_amount:.2f}")
    st.markdown(f"### 🧮 总计（含税）：🟩 **$ {taxed:.2f}**")
