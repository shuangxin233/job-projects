from datetime import datetime

import pandas as pd
import streamlit as st

from utils.helpers import process_user_input


def _split_response(response):
  if isinstance(response, dict):
    return response.get("answer", ""), response.get("sources", [])
  return str(response), []


def render_sources(sources):
  if not sources:
    return

  with st.expander("Sources", expanded=False):
    for source in sources:
      citation_id = source.get("citation_id", "S?")
      source_file = source.get("source_file") or "unknown"
      page = source.get("page")
      page_label = f", page {page + 1}" if isinstance(page, int) else ""
      channel = source.get("retrieval_channel") or "retrieval"
      score = source.get("rerank_score") or source.get("rrf_score")
      score_label = f" | score: {score}" if score is not None else ""
      st.markdown(f"**[{citation_id}] {source_file}{page_label}**  \n{channel}{score_label}")
      st.caption((source.get("preview") or source.get("page_content") or "")[:500])


def render_user_input(model_provider, model):
  disable_input = (
    st.session_state.get("unsubmitted_files", False)
    or not st.session_state.get(f"uploaded_files_{st.session_state.uploader_key}", [])
    or not st.session_state.get("chat_ready")
  )

  question = st.chat_input(
    "Ask a question from the uploaded knowledge files",
    disabled=disable_input
  )

  if not question:
    return

  with st.chat_message("user"):
    st.markdown(question)
  with st.chat_message("ai"):
    with st.spinner("Thinking..."):
      try:
        response = process_user_input(model_provider, model, question)
        answer, sources = _split_response(response)
        st.markdown(answer)
        render_sources(sources)
        file_names = [f.name for f in st.session_state.get("pdf_files")]
        st.session_state.chat_history.append(
          (question, answer, model_provider, model, file_names, datetime.now(), sources)
        )
      except Exception as e:
        st.error(f"Error: {str(e)}")


def render_uploaded_files_expander():
  uploaded_files = st.session_state.get(f"uploaded_files_{st.session_state.uploader_key}", [])
  if uploaded_files and not st.session_state.get("unsubmitted_files"):
    with st.expander("Uploaded Files"):
      for f in uploaded_files:
        st.markdown(f"- {f.name}")


def render_chat_history():
  for item in st.session_state.get("chat_history", []):
    q = item[0]
    answer = item[1]
    sources = item[6] if len(item) > 6 else []
    with st.chat_message("user"):
      st.markdown(q)
    with st.chat_message("ai"):
      st.markdown(answer)
      render_sources(sources)


def render_download_chat_history():
  rows = []
  for item in st.session_state.get("chat_history", []):
    question, answer, provider, model_name, files, timestamp, *rest = item
    sources = rest[0] if rest else []
    rows.append({
      "Question": question,
      "Answer": answer,
      "Model": provider,
      "Model Name": model_name,
      "Files": ", ".join(files),
      "Sources": ", ".join(source.get("source_file", "") for source in sources),
      "Timestamp": timestamp,
    })

  df = pd.DataFrame(rows)

  with st.expander("Download Chat History"):
    st.download_button(
      "Download Chat History",
      data=df.to_csv(index=False),
      file_name="chat_history.csv",
      mime="text/csv"
    )
