# Best Practices / 使用最佳实践

## Table of Contents / 目录

1. [When to Optimize / 何时优化](#when-to-optimize)
2. [Choosing Compression Level / 选择压缩级别](#choosing-compression-level)
3. [Configuration Tuning / 配置调优](#configuration-tuning)
4. [Common Pitfalls / 常见陷阱](#common-pitfalls)
5. [Integration Patterns / 集成模式](#integration-patterns)

---

## When to Optimize

### Should You Optimize? / 是否需要优化？

| Scenario / 场景 | Optimize? / 是否优化 |
|----------------|--------------------|
| Token usage < 50% of limit | ❌ No, unnecessary / 不需要 |
| Token usage 50-70% of limit | ⚠️ Consider if growing / 关注增长趋势 |
| Token usage 70-90% of limit | ✅ Light optimization / 轻度优化 |
| Token usage > 90% of limit | 🔴 Aggressive optimization / 激进优化 |
| Repeatedly hitting limits | 🔴 Must optimize / 必须优化 |

### Anti-patterns / 反模式

- ❌ Optimizing every request regardless of need
- ❌ Using aggressive compression when light compression suffices
- ❌ Removing recent messages instead of old ones
- ❌ Compressing system prompts (usually high-value, low-token)

---

## Choosing Compression Level

### Decision Tree / 决策树

```
Is token usage > 90%?
├── Yes → AGGRESSIVE (three-layer full compression)
└── No → Is token usage > 70%?
    ├── Yes → MODERATE (far layer + middle layer compression)
    └── No → Is token usage > 50%?
        ├── Yes → LIGHT (deduplicate + filter)
        └── No → NONE (no optimization needed)
```

### Level Comparison / 级别对比

| Level / 级别 | Savings / 节省 | Info Loss / 信息损失 | Speed / 速度 | Use Case / 场景 |
|-------------|---------------|--------------------|----|----------------|
| NONE | 0% | None | Fastest / 最快 | Short conversations / 短对话 |
| LIGHT | 5-15% | Minimal / 极少 | Fast / 快 | Minor overflow / 轻微超限 |
| MODERATE | 30-50% | Some details / 部分细节 | Medium / 中等 | Multi-turn chats / 多轮对话 |
| AGGRESSIVE | 60-80% | Significant / 较多 | Slower / 较慢 | Very long conversations / 超长对话 |

---

## Configuration Tuning

### Key Parameters / 关键参数

#### `keep_recent` (default: 10)

- **Lower values** (3-5): More aggressive, saves more tokens, may lose recent context
- **Higher values** (15-20): More conservative, preserves context, less savings
- **Recommendation**: 5-10 for task-focused chats, 10-15 for open-ended conversations

#### `model_limit` (default: 8192)

- Set to your model's actual context window minus a safety margin
- Recommended: `model_limit = actual_limit * 0.9` (reserve 10% for output)

#### `safe_threshold` (default: 0.7)

- Controls when optimization starts
- Lower (0.5): Start optimizing earlier, more cautious
- Higher (0.8): Start optimizing later, more aggressive

---

## Common Pitfalls

### 1. Over-Compression / 过度压缩

**Problem**: Stripping too much context causes the model to lose track of the conversation.

**Solution**: Always keep `keep_recent >= 5` messages intact. Use MODERATE instead of AGGRESSIVE when possible.

### 2. Ignoring Decision Points / 忽略决策点

**Problem**: Compressing away key decisions leads to the model suggesting already-rejected approaches.

**Solution**: Always extract and preserve decision points before compressing history.

### 3. Premature Optimization / 过早优化

**Problem**: Running the full pipeline on every request wastes compute.

**Solution**: Use pre-analysis to check if optimization is actually needed. Skip if risk_level is SAFE.

### 4. Not Reserving Output Budget / 未预留输出预算

**Problem**: Filling the context window to 100% leaves no room for the model's response.

**Solution**: Always set `model_limit` to 80-90% of the actual context window.

---

## Integration Patterns

### Pattern 1: Pre-Request Hook / 请求前钩子

```python
# Before every LLM API call
optimizer = TokenOptimizer(model_limit=8192)
analysis = optimizer.pre_analyze(messages, system_prompt, current_message)

if analysis.risk_level != RiskLevel.SAFE:
    result = optimizer.optimize(messages, system_prompt, current_message)
    messages = result.optimized_messages
```

### Pattern 2: Middleware / 中间件模式

```python
class TokenOptimizationMiddleware:
    def __init__(self, model_limit=8192):
        self.optimizer = TokenOptimizer(model_limit=model_limit)
    
    def process(self, request):
        analysis = self.optimizer.pre_analyze(request.messages)
        if analysis.risk_level == RiskLevel.CRITICAL:
            result = self.optimizer.optimize(request.messages)
            request.messages = result.optimized_messages
            request.metadata["token_savings"] = result.savings_percent
        return request
```

### Pattern 3: Background Compression / 后台压缩

```python
# Periodically compress history in background
# (e.g., every 10 messages)
if len(messages) % 10 == 0:
    compressor = HistoryCompressor(keep_recent=10)
    result = compressor.layered_compress(messages, CompressionLevel.MODERATE)
    messages = result.compressed_messages
```
