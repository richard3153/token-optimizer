# Token Optimizer / Token 优化器

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-green.svg)](https://python.org)
[![Skill](https://img.shields.io/badge/Skill-Token%20Optimizer-orange.svg)](https://github.com)

> 🎯 **A token preprocessing pipeline that reduces input token consumption before calculating token usage.**
>
> 🎯 **Token 预处理优化流水线，在计算 token 使用前主动减少输入 token 消耗。**

---

## 🌟 Features / 特性

| Feature / 特性 | Description / 描述 |
|---------------|-------------------|
| 📊 **Fast Estimation / 快速估算** | Estimate tokens for English, Chinese, and code content / 支持英文、中文、代码的 token 快速估算 |
| 🗜️ **Layered Compression / 分层压缩** | Three-layer history compression: recent → middle → far / 三层历史压缩：近层→中间层→远层 |
| 🧠 **Smart Filtering / 智能过滤** | Keyword + semantic relevance scoring / 关键词+语义相关性评分 |
| 📋 **Decision Extraction / 决策提取** | Preserve key decisions from long conversations / 从长对话中提取保留关键决策 |
| 🔄 **Progressive Optimization / 渐进优化** | Start with low-cost strategies, escalate as needed / 从低损策略开始，按需升级 |
| ⚡ **Early Exit / 提前退出** | Stop when safe threshold reached / 达到安全阈值立即停止 |

---

## 📦 Installation / 安装

### Via SkillHub (Recommended) / 通过 SkillHub 安装（推荐）

```bash
# Install via SkillHub CLI / 通过 SkillHub CLI 安装
skillhub install token-optimizer
```

### Via OpenClaw / 通过 OpenClaw 安装

```bash
# In OpenClaw chat / 在 OpenClaw 对话中
/install token-optimizer
```

### Manual Installation / 手动安装

```bash
# Clone the repository / 克隆仓库
git clone https://github.com/qclaw-community/token-optimizer.git

# Copy to skills directory / 复制到 skills 目录
# Windows
xcopy /E /I token-optimizer %USERPROFILE%\.qclaw\skills\token-optimizer
# macOS/Linux
cp -r token-optimizer ~/.qclaw/skills/token-optimizer
```

---

## 🚀 Quick Start / 快速开始

### Python API

```python
from token_optimizer import TokenOptimizer

# Initialize with your model's token limit / 使用模型的 token 上限初始化
optimizer = TokenOptimizer(model_limit=8192)

# Analyze token usage / 分析 token 使用情况
analysis = optimizer.pre_analyze(
    messages=conversation_history,
    system_prompt="You are a helpful assistant.",
    current_message="Tell me about..."
)

# Optimize if needed / 按需优化
if analysis.risk_level != "safe":
    result = optimizer.optimize(
        messages=conversation_history,
        system_prompt="You are a helpful assistant.",
        current_message="Tell me about..."
    )
    print(f"Saved {result.savings_percent}% tokens")
    print(f"Applied strategies: {result.applied_strategies}")
```

### CLI Usage / 命令行使用

```bash
# Estimate tokens for a message file / 估算消息文件的 token 数
python scripts/token_estimator.py --text "Hello, 你好世界"

# Optimize a conversation / 优化对话
python scripts/token_optimizer.py --input messages.json --limit 8192

# Compress history / 压缩历史
python scripts/history_compressor.py --input messages.json --level moderate
```

---

## 🏗️ Architecture / 架构

### Processing Pipeline / 处理流水线

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Phase 1  │───▶│  Phase 2  │───▶│  Phase 3  │───▶│  Phase 4  │
│ Pre-Analyze│   │  Decide   │   │  Execute  │   │  Calculate │
│   预分析    │   │   决策    │   │   执行    │   │   计算     │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
     ↓               ↓               ↓               ↓
  Estimate       Risk Level     Apply Strategy    Final Result
  估算token      风险等级       应用策略          最终结果
```

### Three-Layer Compression / 三层压缩

```
┌────────────────────────────────────────┐
│  Recent Layer (近层)                    │
│  Last N messages → Keep intact         │
│  最近N条消息 → 完整保留                  │
│  Compression: 0%                        │
├────────────────────────────────────────┤
│  Middle Layer (中间层)                  │
│  Mid-age messages → AI Summary         │
│  中期消息 → AI摘要                      │
│  Compression: ~70%                      │
├────────────────────────────────────────┤
│  Far Layer (远层)                       │
│  Oldest messages → Decision Points     │
│  最早消息 → 提取关键决策点               │
│  Compression: ~95%                      │
└────────────────────────────────────────┘
```

---

## 📖 Use Cases / 使用场景

| Scenario / 场景 | Description / 描述 |
|----------------|-------------------|
| 💬 **Long Conversations / 长对话** | Multi-turn chats that exceed model context window / 超出模型上下文窗口的多轮对话 |
| 🤖 **AI Agents / AI 代理** | Autonomous agents with growing conversation history / 对话历史持续增长的自主代理 |
| 📝 **Document Processing / 文档处理** | Large documents that need to fit within token limits / 需要适配 token 限制的大文档 |
| 🔧 **API Cost Reduction / API 成本优化** | Reduce token usage to lower API costs / 减少 token 使用量以降低 API 成本 |
| 🔄 **Context Management / 上下文管理** | Smart context window management for chat applications / 聊天应用的智能上下文窗口管理 |

---

## ⚙️ Configuration / 配置

| Parameter / 参数 | Default / 默认值 | Description / 描述 |
|-----------------|-----------------|-------------------|
| `model_limit` | 8192 | Model token limit / 模型 token 上限 |
| `safe_threshold` | 0.7 | Safe usage ratio / 安全使用比例 |
| `warning_threshold` | 0.9 | Warning usage ratio / 警告使用比例 |
| `keep_recent` | 10 | Recent messages to preserve / 保留的最近消息数 |

---

## 📊 Expected Results / 预期效果

| Scenario / 场景 | Savings / 节省 | Example / 示例 |
|----------------|---------------|---------------|
| Light overflow / 轻度超限 | 20-30% | 8000 → 5600-6400 tokens |
| Medium overflow / 中度超限 | 40-60% | 12000 → 4800-7200 tokens |
| Severe overflow / 严重超限 | 60-80% | 20000 → 4000-8000 tokens |

---

## 📁 Project Structure / 项目结构

```
token-optimizer/
├── SKILL.md                          # Skill definition / Skill 定义文件
├── LICENSE                           # MIT License / MIT 许可证
├── README.md                         # This file / 本文件
├── scripts/
│   ├── token_optimizer.py            # Main optimization pipeline / 主优化流水线
│   ├── token_estimator.py            # Fast token estimation / 快速 token 估算
│   └── history_compressor.py         # History compression / 历史压缩策略
└── references/
    ├── algorithms.md                 # Algorithm details / 算法详细说明
    └── best_practices.md             # Usage best practices / 使用最佳实践
```

---

## 🤝 Contributing / 贡献

Contributions are welcome! Please feel free to submit a Pull Request.

欢迎贡献代码！请随时提交 Pull Request。

1. Fork the repository / Fork 仓库
2. Create your feature branch / 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. Commit your changes / 提交变更 (`git commit -m 'Add amazing feature'`)
4. Push to the branch / 推送到分支 (`git push origin feature/amazing-feature`)
5. Open a Pull Request / 开启 Pull Request

---

## 📄 License / 许可证

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

本项目基于 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

---

## 🏷️ Topics & Tags

`token-optimizer` `token-compression` `llm` `context-window` `conversation-management` `token-estimation` `openclaw-skill` `qclaw-skill` `skillhub` `ai-agent` `prompt-engineering` `nlp`

---

<p align="center">
  Made with ❤️ by QClaw Community
</p>
