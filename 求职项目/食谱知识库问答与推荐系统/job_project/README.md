# Job Project Mainline

This directory turns the large `all-in-rag` learning repository into one
interview-friendly project line.

## Positioning

Project name:

**Recipe Knowledge Base QA and Recommendation System**

The original repository contains many chapters and optional stacks. For job
presentation, this mainline keeps only the parts that are easy to run and easy
to explain:

- C8 recipe corpus and modular RAG idea.
- C8 hybrid retrieval idea: semantic/keyword evidence retrieval.
- C9 query routing idea: simple questions use normal retrieval; relationship
  or reasoning questions use an expanded "graph-lite" route.

## Simplified Stack

Default stack:

- Python CLI
- Local Markdown recipe corpus
- Lightweight keyword retrieval
- Rule-based query router
- Evidence snippets with source paths

Deferred optional stack:

- Full LLM generation
- Neo4j graph modeling
- Milvus vector database
- Full Graph RAG

This keeps the project runnable on a normal laptop and avoids turning the
interview demo into an infrastructure demo.

## Run

```bash
cd C:\Users\shuangxin\Desktop\RAG项目\项目2\all-in-rag
python job_project\app.py --query "宫保鸡丁怎么做"
python job_project\app.py --query "鸡肉和蔬菜能搭配做什么"
```

The output shows:

- selected route
- route reason
- top evidence snippets
- source file paths

## Next Step

When this lightweight version is stable, connect the retrieved evidence to an
LLM and require the generated answer to cite `[S1]`, `[S2]`, etc.
