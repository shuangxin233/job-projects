# All-in-RAG Job Project Mainline

Use `job_project/` as the interview-facing entry instead of presenting this
whole repository as one project.

Why:

- The full repo is a learning/tutorial library.
- The job project should be a focused, runnable application.
- The selected mainline extracts the useful ideas from C8 and C9 while avoiding
  unnecessary Neo4j/Milvus setup for the first demo.

Entry:

```bash
python job_project\app.py --query "宫保鸡丁怎么做"
```

See `job_project/README.md` for the demo flow and simplified stack.
