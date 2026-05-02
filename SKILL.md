---
name: token-optimizer
description: |
  Token预处理优化技能，在计算token使用前主动减少输入token消耗。适用于：
  (1) 对话历史过长需要压缩
  (2) 上下文接近模型token限制
  (3) 需要保留关键信息同时减少token
  (4) 多轮对话场景的智能上下文管理
  Trigger: 用户提到"token优化"、"压缩历史"、"减少上下文"、"token超限"、"上下文管理"等关键词。
---

# Token Optimizer / Token 优化器

## Overview / 概述

**EN**: A token preprocessing pipeline that reduces input token consumption before calculating token usage. Uses layered compression strategies to preserve critical context while minimizing token cost.

**中文**: Token预处理流水线，在计算token使用前主动减少输入token消耗。采用分层压缩策略，在保留关键上下文的同时最小化token开销。

---

## Core Workflow / 核心流程

```
原始输入 → [阶段1: 预分析] → [阶段2: 优化决策] → [阶段3: 执行优化] → [阶段4: 最终计算]
                ↓                    ↓                    ↓                    ↓
           估算原始token        判断是否超限          应用优化策略          最终有效token
```

---

## Phase 1: Pre-Analysis / 阶段1: 预分析

**EN**: Quick token estimation to identify overflow risk.

**中文**: 快速估算token，识别超限风险。

### Token Estimation Formula / Token估算公式

| Language / 语言 | Formula / 公式 |
|----------------|----------------|
| English / 英文 | ~4 chars = 1 token |
| Chinese / 中文 | ~1.5 chars = 1 token |
| Code / 代码 | ~3 chars = 1 token |

### Risk Levels / 风险等级

| Level / 等级 | Threshold / 阈值 | Action / 动作 |
|-------------|-----------------|---------------|
| Safe / 安全 | < 70% limit | No optimization / 无需优化 |
| Warning / 警告 | 70-90% limit | Light compression / 轻度压缩 |
| Critical / 严重 | > 90% limit | Aggressive optimization / 激进优化 |

---

## Phase 2: Optimization Decision / 阶段2: 优化决策

### Strategy Priority / 策略优先级

| Priority / 优先级 | Strategy / 策略 | Savings / 节省 | Cost / 代价 |
|------------------|----------------|---------------|------------|
| P0 | Truncate long history / 截断超长历史 | 30-50% | Lose early context / 丢失早期上下文 |
| P1 | Summarize history / 摘要压缩历史 | 20-40% | Lose details / 细节丢失 |
| P2 | Filter irrelevant / 过滤无关消息 | 10-20% | May miss info / 可能遗漏信息 |
| P3 | Deduplicate / 去重合并 | 5-10% | Minimal / 几乎无 |

---

## Phase 3: Execute Optimization / 阶段3: 执行优化

### Strategy 1: Layered History Compression / 策略1: 分层历史压缩

**EN**: Divide conversation history into three layers with different compression levels.

**中文**: 将对话历史分为三层，采用不同压缩级别。

```
原始历史 (100 messages, ~8000 tokens)
    ↓
[Recent Layer] 最近10条完整保留 (~1000 tokens)
[Middle Layer] 11-50条 → AI摘要为3段 (~500 tokens)
[Far Layer] 51-100条 → 提取5个关键决策 (~200 tokens)
    ↓
优化后 (~1700 tokens, 节省78%)
```

### Strategy 2: Smart Message Filtering / 策略2: 智能消息过滤

Use semantic similarity to filter relevant messages:
使用语义相似度过滤相关消息：

```python
# 1. Extract keywords from current query / 从当前查询提取关键词
keywords = extract_keywords(current_query)

# 2. Calculate semantic similarity / 计算语义相似度
scores = [semantic_similarity(msg, current_query) for msg in messages]

# 3. Keep high-score + recent messages / 保留高分+最近消息
filtered = [msg for i, msg in enumerate(messages) 
            if scores[i] > 0.3 or i > len(messages) - 5]
```

### Strategy 3: Structured Extraction / 策略3: 结构化提取

**EN**: Extract structured information from verbose descriptions.

**中文**: 从冗长描述中提取结构化信息。

```typescript
interface StructuredExtraction {
  entities: string[];      // 提及的实体
  decisions: string[];     // 做出的决策
  constraints: string[];   // 约束条件
  currentGoal: string;     // 当前目标
}
```

**Example / 示例**:

```
原文: "我们之前讨论过用PostgreSQL，因为用户数据量可能很大，
       但后来考虑到运维成本，决定用SQLite，不过要加个缓存层..."

↓ 提取后

decisions: ["选择SQLite替代PostgreSQL(原因:运维成本)"]
constraints: ["需要缓存层", "用户数据量大"]
```

---

## Phase 4: Final Calculation / 阶段4: 最终计算

**Output / 输出**:

| Field / 字段 | Description / 描述 |
|-------------|-------------------|
| originalTokens | Original token count / 原始token数 |
| optimizedTokens | Optimized token count / 优化后token数 |
| savedTokens | Tokens saved / 节省的token |
| savingsPercent | Savings percentage / 节省百分比 |
| appliedStrategies | Strategies applied / 应用的策略 |

---

## Usage / 使用方法

### Quick Start / 快速开始

```python
from scripts.token_optimizer import TokenOptimizer

optimizer = TokenOptimizer(model_limit=8192)
result = optimizer.optimize(
    messages=conversation_history,
    current_message=user_input
)

print(f"Saved {result.savings_percent}% tokens")
print(f"Applied: {result.applied_strategies}")
```

### CLI Usage / 命令行使用

```bash
python scripts/token_optimizer.py --input messages.json --limit 8192
```

---

## Design Principles / 设计原则

1. **Progressive Optimization / 渐进式优化**: Start with low-cost strategies, escalate as needed
2. **Preserve Key Info / 保留关键信息**: Recent messages, user decisions, constraints first
3. **Traceable / 可追溯**: Log each optimization step for debugging
4. **Configurable / 可配置**: Adjust strategy weights per scenario
5. **Early Exit / 提前退出**: Stop when safe threshold reached

---

## Expected Results / 预期效果

| Scenario / 场景 | Savings / 节省 |
|----------------|---------------|
| Light overflow / 轻度超限 | 20-30% |
| Medium overflow / 中度超限 | 40-60% |
| Severe overflow / 严重超限 | 60-80% |

---

## Resources / 资源

### scripts/
- `token_optimizer.py` - Main optimization pipeline / 主优化流水线
- `token_estimator.py` - Fast token estimation / 快速token估算
- `history_compressor.py` - History compression strategies / 历史压缩策略

### references/
- `algorithms.md` - Detailed algorithm explanations / 详细算法说明
- `best_practices.md` - Usage best practices / 使用最佳实践
