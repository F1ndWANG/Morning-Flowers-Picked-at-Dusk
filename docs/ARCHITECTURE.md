# 项目架构

这个项目目前是“无构建静态前端 + FastAPI 后端”的结构，重点是把广告创意生成、效果预估、多目标排序、图片 Prompt 和真实 API 接入位都拆成独立模块。

## 目录说明

```text
E:\AIGCSAR
├─ backend
│  ├─ .env.example
│  ├─ app
│  │  ├─ api
│  │  ├─ core
│  │  ├─ models
│  │  └─ services
│  └─ data
├─ docs
├─ index.html
├─ scripts
└─ src
```

## 前端模块

- `src/app`
  - `controller.js`：前端编排层，负责串联表单、后端 API、本地 pipeline 和页面渲染。
  - `apiClient.js`：后端接口调用层。
- `src/core`
  - `generator.js`：本地 mock 创意生成。
  - `scoring.js`：CTR/CVR/eCPM 特征打分。
  - `strategies.js`：多目标 rerank 与 ablation。
  - `compliance.js`：合规和风险规则。
  - `prompt.js`：文本与图片 Prompt 生成。
  - `report.js`：面试报告生成。
  - `pipeline.js`：本地完整链路。
- `src/ui`
  - `summary.js`、`lab.js`、`creativePool.js`、`governance.js`、`integration.js` 分别负责结果、实验、创意池、质量门控和 API 接入位展示。

## 后端模块

- `backend/app/core/settings.py`
  - 统一读取文本大模型和文生图接口配置。
- `backend/app/services/llm_service.py`
  - 文本大模型接入位。
  - 在 `mock` 模式下回退到模板生成。
  - 在 `api` 模式下调用 OpenAI-compatible `/chat/completions` 接口。
- `backend/app/services/image_generation_service.py`
  - 文生图接入位。
  - 在 `mock` 模式下只生成图片 Prompt。
  - 在 `api` 模式下调用 OpenAI-compatible `/images/generations` 接口。
- `backend/app/services/pipeline_service.py`
  - 串联 baseline、文本生成、预测、rerank、图片 Prompt / 图片生成、报告输出。
- `backend/app/api/routes.py`
  - 暴露 `/catalog`、`/samples`、`/integrations`、`/pipeline/run`、`/experiments/history`。

## 当前 API 设计

- 文本大模型接入位：
  - `AIGCSAR_LLM_API_KEY`
  - `AIGCSAR_LLM_MODEL`
  - `AIGCSAR_LLM_API_BASE`
- 文生图接入位：
  - `AIGCSAR_IMAGE_API_KEY`
  - `AIGCSAR_IMAGE_MODEL`
  - `AIGCSAR_IMAGE_API_BASE`
  - `AIGCSAR_IMAGE_SIZE`

## 运行链路

1. 前端加载 `catalog / samples / integrations`。
2. 用户填写商品信息，并选择 `mock` 或 `api` 模式。
3. 后端生成文本创意、预测效果、做多目标 rerank。
4. 后端生成图片 Prompt；若图片 API 已配置，则返回真实生成图片。
5. 前端展示指标、创意池、API 状态、实验结果与报告。
