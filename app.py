import streamlit as st
import requests
from datetime import datetime
import pytz
import os
import jpholiday

# ====================
# 日本時間・和暦・六曜・第〇〇曜日
# ====================
def get_japan_datetime_info():
    jst = pytz.timezone('Asia/Tokyo')
    now = datetime.now(jst)

    def to_wareki(dt):
        year = dt.year
        if year >= 2019:
            era = "令和"
            era_year = year - 2018
        elif year >= 1989:
            era = "平成"
            era_year = year - 1988
        elif year >= 1926:
            era = "昭和"
            era_year = year - 1925
        else:
            era = "不明"
            era_year = 0
        return f"{era}{era_year}年{dt.month}月{dt.day}日"

    def get_rokuyo(dt):
        base = datetime(1900, 1, 1, tzinfo=jst)
        days = (dt - base).days
        rokuyo_cycle = ["先勝", "友引", "先負", "仏滅", "大安", "赤口"]
        return rokuyo_cycle[days % 6]

    def get_nth_weekday(dt):
        day = dt.day
        nth = (day - 1) // 7 + 1
        weekday = ["月", "火", "水", "木", "金", "土", "日"][dt.weekday()]
        return f"第{nth}{weekday}曜日"

    return {
        "西暦": now.strftime("%Y年%m月%d日"),
        "和暦": to_wareki(now),
        "時間": now.strftime("%H:%M"),
        "六曜": get_rokuyo(now),
        "第〇〇曜日": get_nth_weekday(now),
        "datetime": now
    }

# ====================
# ゴールドジム営業状況
# ====================
def get_gym_status():
    jst = pytz.timezone('Asia/Tokyo')
    now = datetime.now(jst)
    weekday = now.weekday()  # 月曜=0, 日曜=6
    hour = now.hour
    minute = now.minute

    # 定休日判定：第3月曜日（祝日の場合は営業）
    if weekday == 0:  # 月曜日
        day = now.day
        nth = (day - 1) // 7 + 1
        if nth == 3 and not jpholiday.is_holiday(now.date()):
            return "🔴 閉店中（第3月曜日のため定休日）"

    # 営業時間設定
    if weekday == 6:  # 日曜日
        open_time = 8
        close_time = 21
    else:  # 月～土
        open_time = 7
        close_time = 23

    # 営業中判定
    current_time = hour + minute / 60
    if open_time <= current_time < close_time:
        return "🟢 営業中"
    else:
        return "🔴 閉店中"

# ====================
# LINE通知（Secretsから取得）
# ====================
LINE_TOKEN = os.getenv("LINE_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

def notify_line(message):
    if not LINE_TOKEN or not LINE_USER_ID:
        return
    url = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_TOKEN}'
    }
    data = {
        'to': LINE_USER_ID,
        'messages': [{'type': 'text', 'text': message}]
    }
    requests.post(url, headers=headers, json=data)

# ====================
# Streamlit 表示
# ====================
st.set_page_config(page_title="神アプリ", layout="centered")

# 日付情報表示
date_info = get_japan_datetime_info()
st.markdown(f"""
### 📅 本日の日付
- 西暦：{date_info['西暦']}
- 和暦：{date_info['和暦']}
- 時間：{date_info['時間']}
- 六曜：{date_info['六曜']}
- {date_info['第〇〇曜日']}
""")

# ジム営業状況表示
gym_status = get_gym_status()
st.markdown(f"### 🏋️ ゴールドジムさいたまスーパーアリーナの営業状況\n- {gym_status}")

# コメント欄 → LINE通知
st.header("💬 コメント欄（Botへ即通知）")
user_comment = st.text_input("Botに送りたいコメントを入力してください")
if user_comment:
    notify_line(f"📩 コメント通知：\n{user_comment}")
    st.success("Botにコメントを送信しました。")
