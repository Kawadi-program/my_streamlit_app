import streamlit as st

st.title("はじめてのStreamlitアプリ")
name = st.text_input("あなたの名前を入力してください")

if name:
    st.success(f"こんにちは、{name}さん！Streamlitへようこそ。")