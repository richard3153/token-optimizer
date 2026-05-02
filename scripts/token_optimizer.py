#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Token Optimizer - Token预处理优化流水线
Token Preprocessing Optimization Pipeline

Author: QClaw Community
License: MIT
"""

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Tuple
import argparse


class RiskLevel(Enum):
    """风险等级"""
    SAFE = "safe"        # < 70% limit
    WARNING = "warning"  # 70-90% limit
    CRITICAL = "critical"  # > 90% limit


@dataclass
class TokenBreakdown:
    """Token分布"""
    system_prompt: int = 0
    conversation_history: int = 0
    current_message: int = 0
    attachments: int = 0
    
    @property
    def total(self) -> int:
        return self.system_prompt + self.conversation_history + self.current_message + self.attachments


@dataclass
class PreAnalysisResult:
    """预分析结果"""
    total_tokens: int
    breakdown: TokenBreakdown
    risk_level: RiskLevel
    limit: int


@dataclass
class OptimizationResult:
    """优化结果"""
    original_tokens: int
    optimized_tokens: int
    saved_tokens: int
    savings_percent: float
    applied_strategies: List[str]
    warnings: List[str]
    ready: bool


class TokenEstimator:
    """Token估算器"""
    
    # Token估算系数
    CHARS_PER_TOKEN_EN = 4      # 英文: 4字符/token
    CHARS_PER_TOKEN_ZH = 1.5    # 中文: 1.5字符/token
    CHARS_PER_TOKEN_CODE = 3    # 代码: 3字符/token
    
    @staticmethod
    def estimate(text: str, content_type: str = "mixed") -> int:
        """
        估算文本的token数量
        
        Args:
            text: 输入文本
            content_type: 内容类型 (english/chinese/code/mixed)
        
        Returns:
            估算的token数量
        """
        if not text:
            return 0
        
        # 检测中文字符比例
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        total_chars = len(text)
        chinese_ratio = chinese_chars / total_chars if total_chars > 0 else 0
        
        # 检测代码特征
        code_patterns = ['def ', 'class ', 'import ', 'function ', '{', '}', '()', '->', '=>']
        code_score = sum(1 for p in code_patterns if p in text) / len(code_patterns)
        
        # 根据内容类型选择估算方式
        if content_type == "english":
            return total_chars // TokenEstimator.CHARS_PER_TOKEN_EN
        elif content_type == "chinese":
            return int(total_chars / TokenEstimator.CHARS_PER_TOKEN_ZH)
        elif content_type == "code":
            return total_chars // TokenEstimator.CHARS_PER_TOKEN_CODE
        else:
            # 混合内容：加权平均
            en_chars = total_chars - chinese_chars
            zh_tokens = int(chinese_chars / TokenEstimator.CHARS_PER_TOKEN_ZH)
            en_tokens = en_chars // TokenEstimator.CHARS_PER_TOKEN_EN
            
            # 代码修正
            if code_score > 0.3:
                return int((zh_tokens + en_tokens) * 0.9)  # 代码通常更紧凑
            
            return zh_tokens + en_tokens


class TokenOptimizer:
    """Token优化器主类"""
    
    def __init__(
        self,
        model_limit: int = 8192,
        safe_threshold: float = 0.7,
        warning_threshold: float = 0.9,
        keep_recent: int = 10
    ):
        """
        初始化Token优化器
        
        Args:
            model_limit: 模型token上限
            safe_threshold: 安全阈值 (默认0.7)
            warning_threshold: 警告阈值 (默认0.9)
            keep_recent: 保留最近N条消息 (默认10)
        """
        self.model_limit = model_limit
        self.safe_threshold = safe_threshold
        self.warning_threshold = warning_threshold
        self.keep_recent = keep_recent
        self.estimator = TokenEstimator()
    
    def pre_analyze(
        self,
        messages: List[Dict],
        system_prompt: str = "",
        current_message: str = "",
        attachments: List[str] = None
    ) -> PreAnalysisResult:
        """
        阶段1: 预分析
        
        Args:
            messages: 对话历史消息列表
            system_prompt: 系统提示词
            current_message: 当前消息
            attachments: 附件列表
        
        Returns:
            预分析结果
        """
        # 计算各部分token
        breakdown = TokenBreakdown(
            system_prompt=self.estimator.estimate(system_prompt),
            conversation_history=sum(
                self.estimator.estimate(m.get("content", "")) for m in messages
            ),
            current_message=self.estimator.estimate(current_message),
            attachments=sum(
                self.estimator.estimate(a) for a in (attachments or [])
            )
        )
        
        total = breakdown.total
        
        # 确定风险等级
        ratio = total / self.model_limit
        if ratio < self.safe_threshold:
            risk_level = RiskLevel.SAFE
        elif ratio < self.warning_threshold:
            risk_level = RiskLevel.WARNING
        else:
            risk_level = RiskLevel.CRITICAL
        
        return PreAnalysisResult(
            total_tokens=total,
            breakdown=breakdown,
            risk_level=risk_level,
            limit=self.model_limit
        )
    
    def decide_strategies(self, analysis: PreAnalysisResult) -> List[str]:
        """
        阶段2: 决策优化策略
        
        Args:
            analysis: 预分析结果
        
        Returns:
            要应用的策略列表
        """
        if analysis.risk_level == RiskLevel.SAFE:
            return []
        
        strategies = []
        
        if analysis.risk_level == RiskLevel.WARNING:
            # 轻度优化
            strategies = ["deduplicate", "filter_irrelevant"]
        else:
            # 激进优化
            strategies = [
                "truncate_history",
                "summarize_history",
                "filter_irrelevant",
                "deduplicate"
            ]
        
        return strategies
    
    def apply_strategy(
        self,
        strategy: str,
        messages: List[Dict],
        current_message: str = ""
    ) -> Tuple[List[Dict], int]:
        """
        阶段3: 应用单个优化策略
        
        Args:
            strategy: 策略名称
            messages: 消息列表
            current_message: 当前消息 (用于相关性计算)
        
        Returns:
            (优化后的消息列表, 节省的token数)
        """
        original_tokens = sum(
            self.estimator.estimate(m.get("content", "")) for m in messages
        )
        
        if strategy == "truncate_history":
            # 截断历史：只保留最近N条
            optimized = messages[-self.keep_recent:] if len(messages) > self.keep_recent else messages
        
        elif strategy == "deduplicate":
            # 去重：移除重复内容
            seen = set()
            optimized = []
            for msg in messages:
                content = msg.get("content", "")
                if content not in seen:
                    seen.add(content)
                    optimized.append(msg)
        
        elif strategy == "filter_irrelevant":
            # 过滤无关：简化实现，保留最近消息
            # 完整实现需要语义相似度计算
            optimized = messages[-max(self.keep_recent, len(messages) // 2):]
        
        elif strategy == "summarize_history":
            # 摘要压缩：标记需要摘要的消息
            # 完整实现需要AI生成摘要
            optimized = messages  # 占位，实际需要调用AI
        
        else:
            optimized = messages
        
        optimized_tokens = sum(
            self.estimator.estimate(m.get("content", "")) for m in optimized
        )
        
        return optimized, original_tokens - optimized_tokens
    
    def optimize(
        self,
        messages: List[Dict],
        system_prompt: str = "",
        current_message: str = "",
        attachments: List[str] = None
    ) -> OptimizationResult:
        """
        完整优化流程
        
        Args:
            messages: 对话历史消息列表
            system_prompt: 系统提示词
            current_message: 当前消息
            attachments: 附件列表
        
        Returns:
            优化结果
        """
        # 阶段1: 预分析
        analysis = self.pre_analyze(
            messages, system_prompt, current_message, attachments
        )
        
        # 阶段2: 决策
        strategies = self.decide_strategies(analysis)
        
        if not strategies:
            # 无需优化
            return OptimizationResult(
                original_tokens=analysis.total_tokens,
                optimized_tokens=analysis.total_tokens,
                saved_tokens=0,
                savings_percent=0.0,
                applied_strategies=[],
                warnings=[],
                ready=True
            )
        
        # 阶段3: 执行优化
        optimized_messages = messages
        total_saved = 0
        applied = []
        warnings = []
        
        for strategy in strategies:
            optimized_messages, saved = self.apply_strategy(
                strategy, optimized_messages, current_message
            )
            total_saved += saved
            
            if saved > 0:
                applied.append(strategy)
            
            # 检查是否已达到安全阈值
            current_tokens = analysis.total_tokens - total_saved
            if current_tokens < self.model_limit * self.safe_threshold:
                break  # 提前退出
        
        # 阶段4: 最终计算
        optimized_tokens = analysis.total_tokens - total_saved
        savings_percent = (total_saved / analysis.total_tokens * 100) if analysis.total_tokens > 0 else 0
        
        return OptimizationResult(
            original_tokens=analysis.total_tokens,
            optimized_tokens=optimized_tokens,
            saved_tokens=total_saved,
            savings_percent=round(savings_percent, 2),
            applied_strategies=applied,
            warnings=warnings,
            ready=optimized_tokens < self.model_limit
        )


def main():
    """CLI入口"""
    parser = argparse.ArgumentParser(
        description="Token Optimizer - Token预处理优化工具"
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="输入消息文件 (JSON格式)"
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=8192,
        help="模型token上限 (默认: 8192)"
    )
    parser.add_argument(
        "--output", "-o",
        help="输出文件路径"
    )
    
    args = parser.parse_args()
    
    # 加载消息
    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    messages = data.get("messages", [])
    system_prompt = data.get("system_prompt", "")
    current_message = data.get("current_message", "")
    
    # 执行优化
    optimizer = TokenOptimizer(model_limit=args.limit)
    result = optimizer.optimize(messages, system_prompt, current_message)
    
    # 输出结果
    output = {
        "original_tokens": result.original_tokens,
        "optimized_tokens": result.optimized_tokens,
        "saved_tokens": result.saved_tokens,
        "savings_percent": result.savings_percent,
        "applied_strategies": result.applied_strategies,
        "warnings": result.warnings,
        "ready": result.ready
    }
    
    print(json.dumps(output, indent=2, ensure_ascii=False))
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
