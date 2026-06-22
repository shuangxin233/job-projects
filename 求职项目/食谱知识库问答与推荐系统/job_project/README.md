# job_project 主程序说明

## 模块定位

`job_project/app.py` 是食谱知识库问答与推荐系统的命令行入口。它负责加载本地 Markdown 食谱、判断问题类型、执行检索排序，并输出带来源的 Top-K 证据片段。

## 处理流程

```text
读取用户问题
-> 加载 data/C8/cook 下的食谱文档
-> 提取标题、类别和正文
-> route_query() 判断问题类型
-> score_doc() 计算匹配分数
-> retrieve() 召回 Top-K 食谱
-> make_answer() 输出证据和答案草稿
```

## 当前检索方式

当前版本使用轻量关键词检索和规则路由，适合在普通电脑上直接运行：

- `hybrid-basic`：普通查询和推荐问题
- `hybrid-detail`：做法、步骤、材料类问题
- `graph-lite-router`：搭配、替代、适合、原因、对比类问题

## 运行示例

```powershell
cd 求职项目\食谱知识库问答与推荐系统
python job_project\app.py --query "宫保鸡丁怎么做" --top-k 3
python job_project\app.py --query "鸡肉和蔬菜能搭配做什么" --top-k 5
```

## 输出内容

- 选择的检索策略
- 策略选择原因
- Top-K 食谱标题
- 文档类别
- 匹配分数
- 来源文件路径
- 内容预览片段

## 后续扩展

- 将关键词检索升级为 Embedding 语义检索
- 接入 ChromaDB、Qdrant 或 Milvus
- 加入 BM25 + 向量检索的混合召回
- 将 Top-K 证据交给 LLM 生成最终答案
