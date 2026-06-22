# RAG Evaluation Report

This report is a template. Start the FastAPI server, upload a representative
knowledge base, copy `evaluation_questions.example.json` to
`evaluation_questions.json`, and replace the sample file names with real
source files.

Run:

```bash
python evaluation/evaluate_rag.py --provider groq --model llama-3.1-8b-instant --questions evaluation_questions.json
```

Metrics:

- Source hit rate: whether retrieved sources include the expected document.
- Citation marker rate: whether the generated answer includes citation markers such as `[S1]`.
- Manual review: check whether the answer is faithful to the retrieved chunks.
