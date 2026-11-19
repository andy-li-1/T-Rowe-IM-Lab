"""Web UI: upload or paste a call transcript, get structured tax input.

Run:  streamlit run app.py
"""

import json
import os
from dataclasses import replace
from pathlib import Path

import pandas as pd
import streamlit as st

from tax_extractor import run_text
from tax_extractor.config import PROVIDERS, load_settings

SAMPLE_PATH = Path(__file__).parent / "data" / "transcripts" / "sample_call.txt"

st.set_page_config(page_title="Transcript → Tax Input", page_icon="🧾", layout="wide")


# --------------------------------------------------------------------------- #
# Sidebar: model settings
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.header("Model")
    provider = st.selectbox(
        "Provider",
        list(PROVIDERS),
        index=list(PROVIDERS).index(os.getenv("TAX_EXTRACTOR_PROVIDER", "gemini")),
        help="gemini / groq: free hosted tiers (need a free key). ollama: runs locally, no key.",
    )
    preset = PROVIDERS[provider]
    model = st.text_input("Model", value=preset["model"])

    key_env = preset["key_env"]
    if key_env:
        env_key = os.getenv(key_env, "")
        api_key = st.text_input(
            f"API key ({key_env})",
            type="password",
            placeholder="Loaded from environment" if env_key else "Paste your key",
            help="Kept only in this browser session; never saved to disk.",
        ) or env_key
    else:
        api_key = "ollama"

    st.caption(
        "⚠️ Free hosted tiers may use inputs for training. "
        "Use synthetic transcripts, or Ollama for real client data."
    )


# --------------------------------------------------------------------------- #
# Main: transcript input
# --------------------------------------------------------------------------- #
st.title("🧾 Transcript → Tax Input")
st.write("Upload or paste a call transcript to extract a structured tax input.")

uploaded = st.file_uploader("Upload transcript (.txt)", type=["txt"])
if st.button("Load sample transcript"):
    st.session_state["transcript"] = SAMPLE_PATH.read_text()
if uploaded is not None and st.session_state.get("loaded_file_id") != uploaded.file_id:
    # Load each new upload once, so edits in the text box aren't overwritten on rerun.
    st.session_state["transcript"] = uploaded.read().decode("utf-8", errors="replace")
    st.session_state["loaded_file_id"] = uploaded.file_id

text = st.text_area("Transcript", key="transcript", height=260)
source = uploaded.name if uploaded is not None else "transcript.txt"

if st.button("Extract", type="primary", disabled=not text.strip()):
    if not api_key:
        st.error(f"Add a {provider} API key in the sidebar (or set {key_env}).")
    else:
        settings = replace(
            load_settings(), provider=provider, base_url=preset["base_url"], model=model, api_key=api_key
        )
        with st.spinner(f"Extracting with {model}…"):
            try:
                st.session_state["result"] = run_text(text, source=source, settings=settings)
            except Exception as e:  # show any provider/validation error in the UI
                st.session_state.pop("result", None)
                st.error(f"{type(e).__name__}: {e}")


# --------------------------------------------------------------------------- #
# Results
# --------------------------------------------------------------------------- #
result = st.session_state.get("result")
if result:
    data = result.data
    st.divider()
    st.subheader("Result")

    if result.warnings:
        for w in result.warnings:
            st.warning(w)
    else:
        st.success("No validation warnings.")

    tp = data.taxpayer
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tax year", tp.tax_year or "—")
    c2.metric("Filing status", (tp.filing_status.value or "—").replace("_", " "))
    c3.metric("State", tp.state_of_residence or "—")
    c4.metric("Dependents", len(data.dependents))

    def items_table(items):
        return pd.DataFrame(
            [
                {"Category": i.category, "Description": i.description,
                 "Amount": i.amount.value, "Quote": i.amount.quote}
                for i in items
            ]
        )

    tabs = st.tabs(["Income", "Deductions", "Dependents", "Follow-ups", "Raw JSON"])
    money = {"Amount": st.column_config.NumberColumn(format="$%,.0f")}
    with tabs[0]:
        if data.income:
            st.dataframe(items_table(data.income), column_config=money, hide_index=True, width="stretch")
            st.caption(f"Total: ${sum(i.amount.value or 0 for i in data.income):,.0f}")
        else:
            st.info("No income found.")
    with tabs[1]:
        if data.deductions:
            st.dataframe(items_table(data.deductions), column_config=money, hide_index=True, width="stretch")
            st.caption(f"Total: ${sum(i.amount.value or 0 for i in data.deductions):,.0f}")
        else:
            st.info("No deductions found.")
    with tabs[2]:
        if data.dependents:
            st.dataframe(pd.DataFrame([d.model_dump() for d in data.dependents]), hide_index=True, width="stretch")
        else:
            st.info("No dependents found.")
    with tabs[3]:
        for q in data.open_questions:
            st.markdown(f"- {q}")
        if data.extraction_notes:
            st.caption(f"Model notes: {data.extraction_notes}")
        if not data.open_questions and not data.extraction_notes:
            st.info("Nothing flagged.")
    with tabs[4]:
        st.json(result.to_dict())

    st.download_button(
        "Download JSON",
        data=json.dumps(result.to_dict(), indent=2),
        file_name=f"{Path(result.source).stem}.json",
        mime="application/json",
    )
