from config.settings import GROQ_API_KEY, GOOGLE_API_KEY

from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

from core.retrieval import build_sources, format_context, hybrid_retrieve
from utils.logger import logger


def get_prompt():
  logger.debug("Creating chat prompt template.")
  return ChatPromptTemplate.from_messages([
    ("system", (
      "Answer using only the context below. Cite supporting evidence with [S1], [S2], etc. "
      "If the answer is not in the context, say you don't know and explain what source is missing."
    )),
    ("human", "Context:\n{context}\n\n\nQuestion:\n{input}")
  ])

def get_llm(model_provider: str, model: str):
  logger.debug(f"Initializing LLM for {model_provider} - {model}")
  if model_provider == "groq":
    return ChatGroq(model=model, api_key=GROQ_API_KEY)
  elif model_provider == "gemini":
    return ChatGoogleGenerativeAI(model=model, api_key=GOOGLE_API_KEY)
  else:
    logger.error(f"Unsupported LLM Provider: {model_provider}")
    raise ValueError(f"Unsupported LLM Provider: {model_provider}")

def build_llm_chain(model_provider: str, model: str, vectorstore):
  logger.debug(f"Building LLM chain for provider: {model_provider}, model: {model}")
  prompt = get_prompt()
  llm = get_llm(model_provider, model)
  retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

  return create_retrieval_chain(
    retriever,
    create_stuff_documents_chain(llm, prompt=prompt)
  )


def _message_content(response) -> str:
  return getattr(response, "content", str(response))


def answer_question(model_provider: str, model: str, vectorstore, question: str, top_k: int = 5):
  logger.debug(f"Answering with hybrid retrieval for provider: {model_provider}, model: {model}")
  docs = hybrid_retrieve(vectorstore, question, top_k=top_k)
  if not docs:
    return {
      "answer": "I don't know. No relevant document chunks were retrieved for this question.",
      "sources": []
    }

  prompt = get_prompt()
  llm = get_llm(model_provider, model)
  response = (prompt | llm).invoke({
    "context": format_context(docs),
    "input": question,
  })

  return {
    "answer": _message_content(response),
    "sources": build_sources(docs),
  }
