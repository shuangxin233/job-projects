# 食谱知识库问答与推荐系统 - 主线说明

本目录将食谱知识库问答系统整理成一个可运行、可讲解的求职展示版本。项目主线集中在 `job_project/`，避免把大量学习材料和可选组件混在一起影响演示。

## 展示重点

- 本地 Markdown 食谱知识库
- 问题意图路由
- 标题、正文、类别综合打分
- Top-K 证据召回
- 证据来源路径输出
- 后续可扩展到向量检索和 LLM 生成

## 入口命令

```powershell
python job_project\app.py --query "宫保鸡丁怎么做" --top-k 3
```

更多流程说明见 `README.md` 和 `job_project/README.md`。
