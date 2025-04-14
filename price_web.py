import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# ========== 💡 自定义样式：防止手机端竖排 ==========
st.markdown("""
<style>
/* 强制横向布局（订单表格） */
@media screen and (max-width: 768px) {
  section.main > div { max-width: 100% !important; }

  [data-testid="stHorizontalBlock"] {
    overflow-x: auto;
    white-space: nowrap;
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
  }
  [data-testid="stHorizontalBlock"] > div {
    min-width: 120px !important;
    margin-right: 6px;
  }

  .stMarkdown, .stNumberInput {
    white-space: nowrap !important;
  }
}
/* 折扣按钮间距修复 */
button[kind="secondary"] {
  padding: 0.25rem 0.75rem !important;
  font-size: 15px !important;
  margin-right: 8px !important;
  white-space: nowrap;
}
button[kind="secondary"]:last-of-type {
  margin-right: 20px !important;
}
</style>
""", unsafe_allow_html=True)

# ========== 获取 Google Sheet 数据 ==========
def get_gsheet_data(sheet_id, sheet_name):
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    try:
        creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(sheet_id).worksheet(sheet_name)
        return pd.DataFrame(sheet.get_all_records())
    except Exception as e:
        st.error("❌ 无法连接 Google Sheets")
        st.exception(e)
        st.stop()

# ========== 配置 ==========
SHEET_ID = "1ikOLabQ1f4OlxLDnm-jIgL4Nckkxfdf71jwmmWu5E5M"
SHEET_NAME = "Sheet1"
data = get_gsheet_data(SHEET_ID, SHEET_NAME)

if "order" not in st.session_state:
    st.session_state.order = []
if "selected_discount" not in st.session_state:
    st.session_state.selected_discount = None

# ========== 页面标题 ==========
st.title("🧾 点单系统")
st.write("点击种类 → 选择颜色 + 长度 → 添加至订单")

# ========== 菜单选择 ==========
st.write("## 📋 菜单")
all_kinds = data['种类'].unique()
cols = st.columns(3)

for idx, kind in enumerate(all_kinds):
    with cols[idx % 3]:
        with st.expander(f"🍽️ {kind}"):
            color = st.selectbox("选择颜色", data[data['种类'] == kind]['颜色'].unique(), key=f"color_{kind}")
            length = st.selectbox("选择长度 (inch)", data[(data['种类'] == kind) & (data['颜色'] == color)]['长度(inch)'].unique(), key=f"length_{kind}")
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
                    st.warning("⚠️ 表格中未找到该组合")

# ========== 当前订单 ==========
st.write("## 🧾 当前订单明细")
if st.button("🧹 清空订单"):
    st.session_state.order = []
    st.rerun()

if not st.session_state.order:
    st.info("🕙 当前没有添加任何商品")
else:
    header_cols = st.columns([1.2, 2, 2, 2.2, 1.5, 1.5, 1])
    for col, h in zip(header_cols, ["颜色", "种类", "长度", "数量", "单价", "小计", "删除"]):
        col.markdown(f"<span style='font-size:16px; font-weight:600'>{h}</span>", unsafe_allow_html=True)
    for i, row in enumerate(st.session_state.order):
        col1, col2, col3, col4, col5, col6, col7 = st.columns([1.2, 2, 2, 2.2, 1.5, 1.5, 1])
        with col1: st.markdown(f"<div style='line-height:2.6'>{row['颜色']}</div>", unsafe_allow_html=True)
        with col2: st.markdown(f"<div style='line-height:2.6'>{row['种类']}</div>", unsafe_allow_html=True)
        with col3: st.markdown(f"<div style='line-height:2.6'>{row['长度 (inch)']} inch</div>", unsafe_allow_html=True)
        with col4:
            qty = st.number_input(" ", value=row["数量"], min_value=1, step=1, key=f"qty_{i}", label_visibility="collapsed")
            st.session_state.order[i]["数量"] = qty
            st.session_state.order[i]["小计 ($)"] = qty * row["单价 ($)"]
        with col5: st.markdown(f"<div style='line-height:2.6'>$ {row['单价 ($)']:.2f}</div>", unsafe_allow_html=True)
        with col6: st.markdown(f"<div style='line-height:2.6'>$ {row['小计 ($)']:.2f}</div>", unsafe_allow_html=True)
        with col7:
            if st.button("🗑️", key=f"del_{i}"):
                st.session_state.order.pop(i)
                st.rerun()

# ========== 折扣与税率 ==========
st.markdown("## 💵 折扣与税率")
col1, col2, col3 = st.columns([2, 6, 2.5])

with col1:
    st.markdown("**折扣方式**")
    discount_mode = st.selectbox(" ", ["固定金额 ($)", "百分比 (%)"], index=0, label_visibility="collapsed")

with col2:
    st.markdown("**折扣金额**")
    b1, b2, b3, b4 = st.columns(4)
    with b1:
        if st.button("$10"): st.session_state.selected_discount = "$10"
    with b2:
        if st.button("$15"): st.session_state.selected_discount = "$15"
    with b3:
        if st.button("$20"): st.session_state.selected_discount = "$20"
    with b4:
        if st.button("❌ 无折扣"): st.session_state.selected_discount = None

with col3:
    st.markdown("**税率 (%)**")
    tax = st.number_input(" ", value=2.7, step=0.1, label_visibility="collapsed")

# ========== 总价计算 ==========
df_order = pd.DataFrame(st.session_state.order) if st.session_state.order else pd.DataFrame(columns=["小计 ($)"])
subtotal = df_order["小计 ($)"].sum()

if discount_mode == "固定金额 ($)":
    discount_amt = float(st.session_state.selected_discount.strip("$")) if st.session_state.selected_discount else 0.0
    after_discount = max(subtotal - discount_amt, 0)
    discount_display = f"**折扣：** -$ {discount_amt:.2f}"
else:
    discount_value = float(st.session_state.selected_discount.strip("$")) if st.session_state.selected_discount else 0.0
    discount_amt = subtotal * (discount_value / 100)
    after_discount = subtotal - discount_amt
    discount_display = f"**折扣：** {discount_value}% → -$ {discount_amt:.2f}"

tax_amt = after_discount * (tax / 100)
total = after_discount + tax_amt

# ========== 显示金额汇总 ==========
st.markdown("---")
st.markdown(f"**原始总价：** $ {subtotal:.2f}")
st.markdown(discount_display)
st.markdown(f"**税率：** {tax:.1f}% → +$ {tax_amt:.2f}")
st.markdown(f"### 🧮 含税总计：🟩 **$ {total:.2f}**")
