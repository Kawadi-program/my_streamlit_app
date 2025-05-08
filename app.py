import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import os.path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# ====================
# Google カレンダー連携（7日分）
# ====================
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def get_google_calendar_events():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)

    now = datetime.utcnow().isoformat() + 'Z'
    week_ahead = (datetime.utcnow() + timedelta(days=7)).isoformat() + 'Z'

    events_result = service.events().list(
        calendarId='primary',
        timeMin=now,
        timeMax=week_ahead,
        maxResults=20,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    return events_result.get('items', [])

# ====================
# 日時・和暦・六曜・第〇〇曜日
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
        "第〇〇曜日": get_nth_weekday(now)
    }

# ====================
# ゴールドジム営業状況
# ====================
def get_gym_status():
    jst = pytz.timezone('Asia/Tokyo')
    now = datetime.now(jst)
    weekday = now.weekday()
    hour = now.hour
    minute = now.minute

    if weekday == 6:  # 日曜
        open_time = 8
        close_time = 21
    else:
        open_time = 7
        close_time = 23

    current_time = hour + minute / 60
    return "🟢 営業中" if open_time <= current_time < close_time else "🔴 閉店中"

# ====================
# LINE通知（セキュリティは環境変数で管理）
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
# Streamlit表示
# ====================
st.set_page_config(page_title="神アプリ", layout="centered")

# 日付表示
date_info = get_japan_datetime_info()
st.markdown(f"""
### 📅 本日の日付
- 西暦：{date_info['西暦']}
- 和暦：{date_info['和暦']}
- 時間：{date_info['時間']}
- 六曜：{date_info['六曜']}
- {date_info['第〇〇曜日']}
""")

# ジム営業状況
gym_status = get_gym_status()
st.markdown(f"### 🏋️ ゴールドジムさいたまスーパーアリーナの営業状況\n- {gym_status}")

# カレンダー予定表示（7日間）
st.markdown("### 📆 Googleカレンダー（今後7日間の予定）")
try:
    events = get_google_calendar_events()
    if not events:
        st.write("今後7日間に予定はありません。")
    else:
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            summary = event.get('summary', '予定タイトルなし')
            st.write(f"- {start}：{summary}")
except Exception as e:
    st.error(f"Googleカレンダー取得エラー: {e}")

# コメント送信欄（LINEに即送信）
st.header("💬 コメント欄（Botへ即通知）")
user_comment = st.text_input("Botに送りたいコメントを入力してください")
if user_comment:
    notify_line(f"📩 コメント通知：\n{user_comment}")
    st.success("Botにコメントを送信しました。")
