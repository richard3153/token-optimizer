# Token Optimization Algorithms / Token优化算法详解

## Table of Contents / 目录

1. [Token Estimation / Token估算](#token-estimation)
2. [Layered History Compression / 分层历史压缩](#layered-history-compression)
3. [Smart Message Filtering / 智能消息过滤](#smart-message-filtering)
4. [Structured Extraction / 结构化提取](#structured-extraction)

---

## Token Estimation

### BPE-based Estimation / 基于BPE的估算

Modern LLMs use Byte Pair Encoding (BPE) tokenizers. The estimation formula is derived from statistical analysis of common tokenizers (GPT-4, Claude, etc.):

| Language / 语言 | Chars/Token | Rationale / 依据 |
|----------------|-------------|-----------------|
| English | ~4.0 | BPE merges common English subwords efficiently |
| Chinese | ~1.5 | CJK characters often become individual tokens |
| Code | ~3.0 | Code has mixed patterns: keywords compress well, symbols less so |

### Formula / 公式

```
tokens = (chinese_chars / 1.5) + (english_chars / 4.0) + (whitespace_chars / 0.3)
```

Whitespace compresses heavily in BPE — spaces, newlines, and indentation merge with adjacent tokens.

### Accuracy / 精度

This estimation targets **±15% accuracy** for typical content. For exact counts, use tiktoken (OpenAI) or the model's native tokenizer.

---

## Layered History Compression

### Three-Layer Architecture / 三层架构

```
┌────────────────────────────────────────────┐
│  Far Layer (远层)                           │
│  Oldest messages → Extract decision points │
│  Compression: ~95%                          │
├────────────────────────────────────────────┤
│  Middle Layer (中间层)                      │
│  Mid-age messages → AI-generated summary   │
│  Compression: ~70%                          │
├────────────────────────────────────────────┤
│  Recent Layer (近层)                        │
│  Recent N messages → Keep intact           │
│  Compression: 0%                            │
└────────────────────────────────────────────┘
```

### Decision Point Extraction / 决策点提取

Algorithm uses regex pattern matching for decision-indicating language:

```python
decision_keywords = [
    # Chinese
    r"决定", r"选择", r"确认", r"同意", r"使用",
    r"最终方案", r"结论",
    # English
    r"decided?", r"chose?", r"confirmed?", r"agreed?",
    r"use\s+\w+", r"switch\s+to", r"adopted?",
    r"conclusion"
]
```

### Layer Boundary Calculation / 层边界计算

```
total = len(messages)
recent_start = max(0, total - keep_recent)    # Default keep_recent=10
middle_start = recent_start // 2              # Middle starts at midpoint

far_layer = messages[:middle_start]
middle_layer = messages[middle_start:recent_start]
recent_layer = messages[recent_start:]
```

---

## Smart Message Filtering

### Relevance Scoring / 相关性评分

Each message gets a relevance score based on:

1. **Keyword overlap** (40% weight): Shared keywords between message and current query
2. **Recency bonus** (30% weight): Newer messages score higher
3. **Length penalty** (10% weight): Very short messages ("ok", "yes") score lower
4. **Role weight** (20% weight): User messages slightly preferred over system messages

### Formula / 公式

```
score(msg) = 0.4 * keyword_overlap(msg, query)
           + 0.3 * recency_bonus(msg.position, total_messages)
           + 0.2 * role_weight(msg.role)
           + 0.1 * length_score(msg.content)
```

### Filtering Threshold / 过滤阈值

Messages with `score < 0.3` are candidates for removal, but:
- Always keep the last 5 messages regardless of score
- Never remove messages containing decision keywords

---

## Structured Extraction

### Extraction Schema / 提取模式

```typescript
interface StructuredExtraction {
  entities: string[];      // Named entities (tools, technologies, people)
  decisions: string[];     // Decisions made (with rationale)
  constraints: string[];   // Requirements and constraints
  currentGoal: string;     // Current objective
}
```

### Extraction Process / 提取流程

1. **Entity Recognition**: Identify technology names, tool references, proper nouns
2. **Decision Detection**: Find sentences with decision indicators
3. **Constraint Extraction**: Identify "must", "should", "need to", "不能", "必须" patterns
4. **Goal Summarization**: Condense the current objective into one sentence

### Example / 示例

**Input / 输入**:
> "我们之前讨论过用PostgreSQL，因为用户数据量可能很大，但后来考虑到运维成本，决定用SQLite，不过要加个缓存层"

**Output / 输出**:
```json
{
  "entities": ["PostgreSQL", "SQLite", "缓存层"],
  "decisions": ["选择SQLite替代PostgreSQL（原因：运维成本）"],
  "constraints": ["需要缓存层", "用户数据量大"],
  "currentGoal": ""
}
```

---

## Performance Characteristics / 性能特征

| Operation / 操作 | Time Complexity / 时间复杂度 | Space / 空间 |
|-----------------|---------------------------|-------------|
| Token estimation | O(n) | O(1) |
| Deduplication | O(n) | O(n) |
| Decision extraction | O(n × k) | O(d) |
| Layered compression | O(n) | O(n) |
| Full optimization pipeline | O(n) | O(n) |

Where: n = total messages, k = keyword patterns, d = decision points found.
