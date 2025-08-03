import os
from io import BytesIO

import streamlit as st
from dotenv import load_dotenv

from app.docx_utils import extract_blocks, restore_blocks
from app.llm_client import translate, estimate
from app.validator import validate

load_dotenv()

st.set_page_config(page_title="DOCX Translator", page_icon="📄")
st.title("DOCX Translator")

uploaded = st.file_uploader("Файл .docx", type=["docx"])
target   = st.selectbox(
    "Язык перевода",
    [("kk", "Қазақша"), ("ru", "Орыс")],
    format_func=lambda x: x[1],
)[0]

if uploaded:
    content = uploaded.read()
    blocks, _ = extract_blocks(BytesIO(content))
    tokens = sum(len(b["content"]) for b in blocks) // 4
    st.caption(f"≈ {tokens} токенов · ~ ${estimate(tokens):.2f}")

if st.button("Аудару") and uploaded:
    st.write("Процессинг")

    blocks, doc = extract_blocks(BytesIO(content))
    translated  = translate([b["content"] for b in blocks], target)

    issues = validate([b["content"] for b in blocks], translated)
    if issues:
        st.warning(" Проверьте placeholders:")
        st.write("\n".join(f"• {i}" for i in issues))

    restore_blocks(doc, blocks, translated)

    buf = BytesIO()
    doc.save(buf); buf.seek(0)

    st.success("Готово")
    st.download_button(
        "Скачать",
        data=buf,
        file_name=f"translated_{target}.docx",
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),
    )

    with st.expander("Показать текстовый diff"):
        from app.validator import html_diff
        st.components.v1.html(
            html_diff(
                "\n\n".join(b["content"] for b in blocks),
                "\n\n".join(translated),
            ),
            height=600,
            scrolling=True,
        )
