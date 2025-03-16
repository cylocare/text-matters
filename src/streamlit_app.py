import streamlit as st
import requests
import json
import base64
import os
import time
from openai import OpenAI

# GitHub Config
GITHUB_REPO = "cylocare/text-matters"
GITHUB_FILE_PATH = "dictionary_of_translations.json"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}"
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]

# Authentication
USERNAME = os.environ["USERNAME"]
PASSWORD = os.environ["PASSWORD"]

# OpenAI Client
client = OpenAI()

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

# Languages
languages = [
    "Hindi", "Spanish", "Mandarin Chinese", "Portuguese", "Russian", "Japanese", "Korean",
    "Indonesian (Bahasa Indonesia)", "Turkish", "Thai", "Vietnamese", "French", "German",
    "Italian", "Polish", "Bengali", "Ukrainian", "Nepali (Nepal)", "Yoruba (Nigeria)", "Zulu (South Africa)"
]
prompt_template = os.environ["PROMPT_TEMPLATE"]


def fetch_translation_dict():
    """Fetch the translation dictionary from GitHub."""
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(GITHUB_API_URL, headers=headers)
    if response.status_code == 200:
        content = json.loads(response.text)
        return json.loads(base64.b64decode(content["content"]).decode()), content["sha"]
    st.error("Failed to fetch translations from GitHub")
    return {}, None


def update_translation_dict(updated_dict, sha):
    """Commit updated translation dictionary to GitHub."""
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    encoded_content = base64.b64encode(json.dumps(updated_dict, indent=2).encode()).decode()
    commit_message = "Updated translations"

    payload = {
        "message": commit_message,
        "content": encoded_content,
        "sha": sha
    }

    response = requests.put(GITHUB_API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        st.success("Translation dictionary updated on GitHub")
    else:
        st.error(f"Failed to update GitHub: {response.text}")


def get_translations_from_dict(xml_lines, language, translation_dict):
    """Check dictionary for existing translations and return missing lines."""
    existing_translations = {}
    missing_lines = {}

    if language in translation_dict:
        lang_dict = translation_dict[language]
        for key, text in xml_lines.items():
            if key in lang_dict:
                existing_translations[key] = lang_dict[key]
            else:
                missing_lines[key] = text
    else:
        missing_lines = xml_lines  # If language not found, all are missing
    return existing_translations, missing_lines


def translate_missing_lines(missing_lines, language):
    """Send missing lines to OpenAI for translation."""
    if not missing_lines:
        return {}

    xml_data = "\n".join([f'<string name="{k}">{v}</string>' for k, v in missing_lines.items()])
    prompt = prompt_template.format(xml_data=xml_data, language=language)

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

    # Parse response into dictionary format
    new_translations = {}
    for line in translated_text.split("\n"):
        if '<string name="' in line:
            parts = line.split('">')
            key = parts[0].split('"')[1]
            value = parts[1].split("</string>")[0]
            new_translations[key] = value.strip()

    return new_translations


# Streamlit UI
st.title("Translations | Cylo")
xml_input = st.text_area("Paste your XML here:")
translate_button = st.button("Translate")

if translate_button and xml_input:
    st.subheader("Translations:")
    translation_dict, sha = fetch_translation_dict()

    # Parse XML input
    xml_lines = {}
    for line in xml_input.split("\n"):
        if '<string name="' in line:
            parts = line.split('">')
            key = parts[0].split('"')[1]
            value = parts[1].split("</string>")[0]
            xml_lines[key] = value.strip()

    updated_translations = {}  # Store only new translations to display

    for lang in languages:
        with st.spinner(f"Translating into {lang}..."):
            existing, missing = get_translations_from_dict(xml_lines, lang, translation_dict)
            new_translations = translate_missing_lines(missing, lang)

            # Merge translations into dict for saving
            translation_dict.setdefault(lang, {}).update(new_translations)

            # Store only the translations related to the current request for display
            updated_translations[lang] = {**existing, **new_translations}

            # **Render translation immediately**
            if updated_translations[lang]:
                with st.expander(f"📖 {lang}"):
                    st.code("\n".join([f'<string name="{k}">{v}</string>' for k, v in updated_translations[lang].items()]),
                            language="xml")

                    time.sleep(0.5)  # Smooth out UI updates

    # Update GitHub with new translations
    update_translation_dict(translation_dict, sha)
