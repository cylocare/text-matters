import streamlit as st
from openai import OpenAI
import time
import os

# Authentication
USERNAME = os.environ['USERNAME']
PASSWORD = os.environ['PASSWORD']

# User login session
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False


def login():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == USERNAME and password == PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Invalid username or password")


if not st.session_state.authenticated:
    login()
    st.stop()


client = OpenAI()

# Translation languages
languages = [
    "Hindi", "Spanish", "Mandarin Chinese", "Portuguese", "Russian", "Japanese", "Korean",
    "Indonesian (Bahasa Indonesia)", "Turkish", "Thai", "Vietnamese", "French", "German",
    "Italian", "Polish", "Bengali", "Ukrainian", "Nepali (Nepal)", "Yoruba (Nigeria)", "Zulu (South Africa)"
]
prompt_template = os.environ['PROMPT_TEMPLATE']

# Streamlit UI
st.title("Translations | Cylo")
xml_input = st.text_area("Paste your XML here:")
translate_button = st.button("Translate")


if translate_button and xml_input:
    st.subheader("Translations:")
    for lang in languages:
        with st.spinner(f"Translating into {lang}..."):
            prompt = prompt_template.format(xml_data=xml_input, language=lang)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system",
                     "content": "You are a world-class translation assistant that understands how native speakers would speak and read their languages."},
                    {"role": "user", "content": prompt},
                ],
                temperature=1,
                max_tokens=12000
            )
            translated_text = response.choices[0].message.content

            st.markdown(f"### {lang}")
            st.code(translated_text, language="xml")
            time.sleep(1)
