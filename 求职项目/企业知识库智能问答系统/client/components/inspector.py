import streamlit as st

from state.session import is_chat_ready
from utils.helpers import get_documents_count, get_similar_chunks


def render_inspect_query(model_provider):
  st.caption("Inspect hybrid retrieval results")
  try:
    doc_count = get_documents_count(model_provider)
    st.success(f"{doc_count} chunks stored in VectorStore.")
  except Exception as e:
    st.error("Could not fetch document count.")
    st.code(str(e))

  query = st.chat_input(
    "Test a query against the hybrid retriever",
    disabled=not is_chat_ready()
  )

  if not query:
    return

  with st.chat_message("user"):
    st.markdown(query)
  with st.chat_message("ai"):
    with st.spinner("Searching..."):
      try:
        results = get_similar_chunks(model_provider, query)
        if results:
          st.markdown("### Top Matching Chunks")
          for i, doc in enumerate(results):
            metadata = doc.get("metadata", {})
            source = doc.get("source_file") or metadata.get("source") or "unknown"
            channel = doc.get("retrieval_channel") or "retrieval"
            score = doc.get("rerank_score") or doc.get("rrf_score")
            score_label = f" | score: {score}" if score is not None else ""
            content = doc.get("page_content", str(doc))[:600]
            st.markdown(f"**Result {i + 1}: {source}**  \n{channel}{score_label}")
            st.caption(content)
        else:
          st.info("No matching chunks found.")
      except Exception as e:
        st.error("Error querying VectorStore")
        st.code(str(e))
