#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
History Compressor - 对话历史压缩策略
Conversation History Compression Strategies

Author: QClaw Community
License: MIT
"""

import re
import json
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum


class CompressionLevel(Enum):
    """压缩级别"""
    NONE = "none"           # 不压缩
    LIGHT = "light"         # 轻度：去重 + 过滤
    MODERATE = "moderate"   # 中度：摘要压缩中间层
    AGGRESSIVE = "aggressive"  # 激进：三层全压缩


@dataclass
class CompressionResult:
    """压缩结果"""
    original_messages: List[Dict]
    compressed_messages: List[Dict]
    original_tokens: int
    compressed_tokens: int
    level: CompressionLevel
    summary_sections: List[str]  # 摘要段落（如有）
    decision_points: List[str]   # 关键决策点（如有）


class HistoryCompressor:
    """对话历史压缩器"""
    
    def __init__(
        self,
        keep_recent: int = 10,
        summary_max_paragraphs: int = 3,
        max_decision_points: int = 5,
        token_estimator=None
    ):
        """
        初始化历史压缩器
        
        Args:
            keep_recent: 保留最近N条完整消息
            summary_max_paragraphs: 摘要最大段落数
            max_decision_points: 最大关键决策点数
            token_estimator: token估算器实例
        """
        self.keep_recent = keep_recent
        self.summary_max_paragraphs = summary_max_paragraphs
        self.max_decision_points = max_decision_points
        self.token_estimator = token_estimator
    
    def _estimate_tokens(self, text: str) -> int:
        """估算token数量"""
        if self.token_estimator:
            return self.token_estimator.estimate(text)
        # 简易估算回退
        if not text:
            return 0
        chinese = len(re.findall(r'[\u4e00-\u9fff]', text))
        other = len(text) - chinese
        return int(chinese / 1.5 + other / 4)
    
    def deduplicate(self, messages: List[Dict]) -> List[Dict]:
        """
        去重：移除完全重复的消息
        
        Args:
            messages: 消息列表
        
        Returns:
            去重后的消息列表
        """
        seen = set()
        result = []
        for msg in messages:
            content = msg.get("content", "")
            # 使用角色+内容作为去重key
            key = f"{msg.get('role', '')}:{content}"
            if key not in seen:
                seen.add(key)
                result.append(msg)
        return result
    
    def filter_short_messages(
        self,
        messages: List[Dict],
        min_tokens: int = 5
    ) -> List[Dict]:
        """
        过滤过短的消息（如"好的"、"是的"等）
        
        Args:
            messages: 消息列表
            min_tokens: 最小token阈值
        
        Returns:
            过滤后的消息列表
        """
        return [
            msg for msg in messages
            if self._estimate_tokens(msg.get("content", "")) >= min_tokens
        ]
    
    def extract_decision_points(self, messages: List[Dict]) -> List[str]:
        """
        从消息中提取关键决策点
        
        识别包含决策性语言的消息，如"决定"、"选择"、"确认"等
        
        Args:
            messages: 消息列表
        
        Returns:
            关键决策点列表
        """
        decision_keywords = [
            r"决定", r"选择", r"确认", r"同意", r"使用",
            r"decided?", r"chose?", r"confirmed?", r"agreed?",
            r"use\s+\w+", r"switch\s+to", r"adopted?",
            r"最终方案", r"结论", r"conclusion"
        ]
        
        decisions = []
        for msg in messages:
            content = msg.get("content", "")
            if any(re.search(kw, content, re.IGNORECASE) for kw in decision_keywords):
                # 截取决策相关的句子
                sentences = re.split(r'[。！？.!?\n]', content)
                for s in sentences:
                    s = s.strip()
                    if s and any(re.search(kw, s, re.IGNORECASE) for kw in decision_keywords):
                        decisions.append(s)
        
        return decisions[:self.max_decision_points]
    
    def layered_compress(
        self,
        messages: List[Dict],
        level: CompressionLevel = CompressionLevel.MODERATE
    ) -> CompressionResult:
        """
        分层压缩对话历史
        
        三层结构：
        - 远层 (Far): 最早的消息 → 提取关键决策点
        - 中间层 (Middle): 中期消息 → 生成摘要
        - 近层 (Recent): 最近消息 → 完整保留
        
        Args:
            messages: 消息列表
            level: 压缩级别
        
        Returns:
            压缩结果
        """
        if not messages or level == CompressionLevel.NONE:
            return CompressionResult(
                original_messages=messages,
                compressed_messages=messages,
                original_tokens=sum(self._estimate_tokens(m.get("content", "")) for m in messages),
                compressed_tokens=sum(self._estimate_tokens(m.get("content", "")) for m in messages),
                level=level,
                summary_sections=[],
                decision_points=[]
            )
        
        original_tokens = sum(self._estimate_tokens(m.get("content", "")) for m in messages)
        compressed_messages = []
        summary_sections = []
        decision_points = []
        
        total = len(messages)
        recent_start = max(0, total - self.keep_recent)
        
        if level == CompressionLevel.LIGHT:
            # 轻度：去重 + 过滤
            compressed_messages = self.deduplicate(messages)
            compressed_messages = self.filter_short_messages(compressed_messages)
        
        elif level == CompressionLevel.MODERATE:
            # 中度：远层提取决策 + 近层完整保留
            far_messages = messages[:recent_start // 2] if recent_start > 0 else []
            middle_messages = messages[recent_start // 2:recent_start] if recent_start > 0 else []
            recent_messages = messages[recent_start:]
            
            # 远层 → 提取决策点
            if far_messages:
                decision_points = self.extract_decision_points(far_messages)
                if decision_points:
                    # 将决策点作为系统消息插入
                    decision_text = "[Key Decisions / 关键决策]:\n" + "\n".join(
                        f"- {d}" for d in decision_points
                    )
                    compressed_messages.append({
                        "role": "system",
                        "content": decision_text
                    })
            
            # 中间层 → 标记为待摘要（实际摘要需要AI生成）
            if middle_messages:
                # 简化处理：保留assistant的关键回复，过滤简短确认
                for msg in middle_messages:
                    tokens = self._estimate_tokens(msg.get("content", ""))
                    if tokens > 20:  # 保留有实质内容的消息
                        compressed_messages.append(msg)
            
            # 近层 → 完整保留
            compressed_messages.extend(recent_messages)
        
        elif level == CompressionLevel.AGGRESSIVE:
            # 激进：三层全压缩
            far_messages = messages[:recent_start // 2] if recent_start > 0 else []
            middle_messages = messages[recent_start // 2:recent_start] if recent_start > 0 else []
            recent_messages = messages[recent_start:]
            
            # 远层 → 只保留决策点
            if far_messages:
                decision_points = self.extract_decision_points(far_messages)
                if decision_points:
                    decision_text = "[Key Decisions / 关键决策]:\n" + "\n".join(
                        f"- {d}" for d in decision_points
                    )
                    compressed_messages.append({
                        "role": "system",
                        "content": decision_text
                    })
            
            # 中间层 → 只保留决策点（更激进）
            if middle_messages:
                mid_decisions = self.extract_decision_points(middle_messages)
                if mid_decisions:
                    for d in mid_decisions:
                        if d not in decision_points:
                            decision_points.append(d)
            
            # 近层 → 去重 + 过滤
            recent_deduped = self.deduplicate(recent_messages)
            recent_filtered = self.filter_short_messages(recent_deduped, min_tokens=3)
            compressed_messages.extend(recent_filtered)
        
        compressed_tokens = sum(
            self._estimate_tokens(m.get("content", "")) for m in compressed_messages
        )
        
        return CompressionResult(
            original_messages=messages,
            compressed_messages=compressed_messages,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            level=level,
            summary_sections=summary_sections,
            decision_points=decision_points
        )


def main():
    """CLI入口和测试"""
    test_messages = [
        {"role": "user", "content": "你好，我想做一个项目"},
        {"role": "assistant", "content": "好的，请告诉我更多细节"},
        {"role": "user", "content": "好的"},  # 短消息
        {"role": "user", "content": "我决定使用PostgreSQL作为数据库，因为用户数据量可能很大，需要复杂查询支持"},
        {"role": "assistant", "content": "明白，PostgreSQL是个好选择"},
        {"role": "user", "content": "但后来考虑到运维成本，我们选择用SQLite，不过要加个缓存层"},
        {"role": "assistant", "content": "收到，SQLite加缓存层的方案也合理"},
        {"role": "user", "content": "是的"},  # 短消息
        {"role": "user", "content": "前端决定用React，配合TypeScript"},
        {"role": "assistant", "content": "好的，React+TypeScript是主流选择"},
        {"role": "user", "content": "请帮我设计数据库schema"},
        {"role": "assistant", "content": "好的，根据你的需求，我建议以下schema设计..."},
    ]
    
    compressor = HistoryCompressor(keep_recent=4)
    
    print("=== Layered Compression Test / 分层压缩测试 ===\n")
    
    for level in CompressionLevel:
        result = compressor.layered_compress(test_messages, level)
        savings = (1 - result.compressed_tokens / result.original_tokens) * 100 if result.original_tokens > 0 else 0
        print(f"Level: {level.value}")
        print(f"  Messages: {len(result.original_messages)} → {len(result.compressed_messages)}")
        print(f"  Tokens: {result.original_tokens} → {result.compressed_tokens} (节省 {savings:.1f}%)")
        if result.decision_points:
            print(f"  Decision points: {result.decision_points}")
        print()


if __name__ == "__main__":
    main()
