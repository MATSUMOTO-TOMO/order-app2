import streamlit as st
import json
import os
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.utils import formatdate

# 保存ファイル
USER_INFO_FILE = "user_info.json"
ORDER_FILE = "orders.json"
ADMIN_INFO_FILE = "admin_info.json"
PRODUCT_CSV = "product_list.csv"

# パスワード設定
ADMIN_PASSWORD = "T-MATSUMOTO-6111"

def load_json(fn, default):
    return json.load(open(fn, encoding="utf-8")) if os.path.exists(fn) else default

def save_json(fn, data):
    with open(fn, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def send_email(to_addrs, subject, body):
    smtp_host = "smtp.gmail.com"
    smtp_port = 587
    smtp_user = "your_email@gmail.com"
    smtp_pass = "your_app_password"  # 注意：セキュリティにご配慮ください

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = ", ".join(to_addrs)
    msg["Date"] = formatdate(localtime=True)
    try:
        smtp = smtplib.SMTP(smtp_host, smtp_port)
        smtp.starttls()
        smtp.login(smtp_user, smtp_pass)
        smtp.sendmail(smtp_user, to_addrs, msg.as_string())
        smtp.quit()
        return True
    except Exception as e:
        st.error(f"メール送信エラー: {e}")
        return False

if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "edit_index" not in st.session_state:
    st.session_state.edit_index = None
if "show_summary" not in st.session_state:
    st.session_state.show_summary = False

st.set_page_config(page_title="村田金箔：受注アプリ")
st.title("村田金箔：受注アプリ")

with st.sidebar:
    st.header("管理者ログイン")
    pwd = st.text_input("パスワードを入力", type="password")
    if st.button("ログイン"):
        if pwd == ADMIN_PASSWORD:
            st.session_state.admin_logged_in = True
            st.success("管理者ログイン成功")
            st.rerun()
        else:
            st.error("パスワードが違います")
    if st.session_state.admin_logged_in:
        if st.button("ログアウト"):
            st.session_state.admin_logged_in = False
            st.rerun()

if st.session_state.admin_logged_in:
    st.subheader("管理者設定画面")
    admin_info = load_json(ADMIN_INFO_FILE, {"emails": [""] * 5, "enabled": [False] * 5})
    emails = admin_info["emails"]
    enabled = admin_info["enabled"]
    for i in range(5):
        emails[i] = st.text_input(f"送信先アドレス {i+1}", emails[i])
        enabled[i] = st.checkbox(f"送信する (アドレス{i+1})", value=enabled[i])
    if st.button("設定を保存"):
        save_json(ADMIN_INFO_FILE, {"emails": emails, "enabled": enabled})
        st.success("管理者設定を保存しました")
    st.stop()

user = load_json(USER_INFO_FILE, {"company": "", "client": "", "contact": ""})
remember = st.checkbox("⑴ 依頼者情報を次回も表示する", value=any(user.values()))
company = st.text_input("依頼者企業名", value=user["company"])
client = st.text_input("依頼者名", value=user["client"])
contact = st.text_input("連絡先（電話/メール）", value=user["contact"])

import datetime
due_date = st.date_input("希望納期（日付を選択）", value=datetime.date.today())
df = pd.read_csv(PRODUCT_CSV, encoding="cp932") if os.path.exists(PRODUCT_CSV) else pd.DataFrame(columns=["タイプ","カラー","サイズ"])
types = df["タイプ"].dropna().unique().tolist()
colors = df["カラー"].dropna().unique().tolist()
sizes = df["サイズ"].dropna().unique().tolist()
ptype = st.selectbox("商品タイプ", types)
pcolor = st.selectbox("商品カラー", colors)
psize = st.selectbox("サイズ", sizes)
qty = st.number_input("数量", min_value=1, step=1)

orders = load_json(ORDER_FILE, [])
if st.button("追加"):
    orders.append({"type":ptype,"color":pcolor,"size":psize,"quantity":qty})
    save_json(ORDER_FILE, orders)
    st.rerun()

st.subheader("注文一覧")
for i, o in enumerate(orders):
    st.write(f"#{i+1} {o['type']} / {o['color']} / {o['size']} / {o['quantity']}個")
    c1, c2 = st.columns(2)
    if c1.button(f"修正 {i+1}"):
        st.session_state.edit_index = i
        st.rerun()
    if c2.button(f"削除 {i+1}"):
        orders.pop(i)
        save_json(ORDER_FILE, orders)
        st.rerun()

if st.session_state.edit_index is not None:
    idx = st.session_state.edit_index
    o = orders[idx]
    st.subheader(f"修正 #{idx+1}")
    new_type = st.selectbox("商品タイプ", types, index=types.index(o["type"]))
    new_color = st.selectbox("商品カラー", colors, index=colors.index(o["color"]))
    new_size = st.selectbox("サイズ", sizes, index=sizes.index(o["size"]))
    new_qty = st.number_input("数量", min_value=1, step=1, value=o["quantity"])
    if st.button("保存"):
        orders[idx] = {"type":new_type,"color":new_color,"size":new_size,"quantity":new_qty}
        save_json(ORDER_FILE, orders)
        st.session_state.edit_index = None
        st.rerun()
    if st.button("キャンセル"):
        st.session_state.edit_index = None
        st.rerun()

if st.button("決定"):
    if remember:
        save_json(USER_INFO_FILE, {"company":company,"client":client,"contact":contact})
    else:
        if os.path.exists(USER_INFO_FILE):
            os.remove(USER_INFO_FILE)
    st.session_state.show_summary = True

if st.session_state.show_summary:
    st.subheader("注文確認")
    st.write(f"依頼者企業: {company}")
    st.write(f"依頼者名: {client}")
    st.write(f"連絡先: {contact}")
    st.write(f"納期: {due_date}")
    st.write("--- 注文リスト ---")
    for i, o in enumerate(orders):
        st.write(f"#{i+1} {o['type']} / {o['color']} / {o['size']} / {o['quantity']}個")
    if st.button("注文を発信する"):
        admin_info = load_json(ADMIN_INFO_FILE, {"emails":[""]*5,"enabled":[False]*5})
        to_addrs = [e for e, en in zip(admin_info["emails"], admin_info["enabled"]) if en and e.strip()]
        if not to_addrs:
            st.error("送信先が設定されていません。管理者設定をご確認ください。")
        else:
            body = f"依頼者: {company} / {client} / {contact}\n納期: {due_date}\n\n商品リスト:\n"
            body += "\n".join([f"{i+1}. {o['type']} {o['color']} {o['size']} {o['quantity']}個" for i, o in enumerate(orders)])
            if send_email(to_addrs, "新規注文", body):
                st.success("注文を送信しました！ありがとうございます")
                if os.path.exists(ORDER_FILE): os.remove(ORDER_FILE)
                st.session_state.clear()
                st.rerun()
