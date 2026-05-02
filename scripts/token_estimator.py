#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Token Estimator - 快速Token估算工具
Fast Token Estimation Tool

Author: QClaw Community
License: MIT
"""

import re
from typing import List, Tuple


class TokenEstimator:
    """Token快速估算器"""
    
    # Token估算系数 (基于GPT/BPE tokenizer经验值)
    COEFFICIENTS = {
        "english": 4,      # 英文: ~4字符/token
        "chinese": 1.5,    # 中文: ~1.5字符/token (中文token密度更高)
        "code": 3,         # 代码: ~3字符/token
        "whitespace": 0.3, # 空白字符: ~0.3字符/token (压缩程度更高)
    }
    
    @staticmethod
    def detect_language(text: str) -> Tuple[str, float]:
        """
        检测文本主要语言
        
        Returns:
            (language, ratio): 语言类型和比例
        """
        if not text:
            return ("unknown", 0)
        
        # 中文字符检测 (CJK统一汉字范围)
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf]', text))
        total_chars = len(text)
        chinese_ratio = chinese_chars / total_chars if total_chars > 0 else 0
        
        # 代码特征检测
        code_patterns = [
            r'\bdef\s', r'\bclass\s', r'\bimport\s', r'\bfunction\s',
            r'\{', r'\}', r'\(\)', r'->', r'=>', r'===', r'!==',
            r'\bif\s*\(', r'\bfor\s*\(', r'\bwhile\s*\('
        ]
        code_matches = sum(len(re.findall(p, text)) for p in code_patterns)
        code_ratio = min(code_matches / (total_chars / 100), 1)  # 标准化
        
        if chinese_ratio > 0.3:
            return ("chinese", chinese_ratio)
        elif code_ratio > 0.2:
            return ("code", code_ratio)
        else:
            return ("english", 1 - chinese_ratio)
    
    @staticmethod
    def estimate(text: str, method: str = "auto") -> int:
        """
        估算文本token数量
        
        Args:
            text: 输入文本
            method: 估算方法 (auto/english/chinese/code)
        
        Returns:
            估算的token数量
        """
        if not text:
            return 0
        
        total_chars = len(text)
        
        if method == "auto":
            # 自动检测并估算
            lang, ratio = TokenEstimator.detect_language(text)
            
            if lang == "chinese":
                # 中文文本
                chinese_chars = len(re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf]', text))
                non_chinese = total_chars - chinese_chars
                return int(
                    chinese_chars / TokenEstimator.COEFFICIENTS["chinese"] +
                    non_chinese / TokenEstimator.COEFFICIENTS["english"]
                )
            elif lang == "code":
                # 代码文本 (更紧凑)
                return int(total_chars / TokenEstimator.COEFFICIENTS["code"])
            else:
                # 英文文本
                # 考虑空白字符压缩
                whitespace_chars = len(re.findall(r'\s+', text))
                non_whitespace = total_chars - whitespace_chars
                return int(
                    whitespace_chars / TokenEstimator.COEFFICIENTS["whitespace"] +
                    non_whitespace / TokenEstimator.COEFFICIENTS["english"]
                )
        
        elif method == "english":
            return total_chars // TokenEstimator.COEFFICIENTS["english"]
        
        elif method == "chinese":
            return int(total_chars / TokenEstimator.COEFFICIENTS["chinese"])
        
        elif method == "code":
            return total_chars // TokenEstimator.COEFFICIENTS["code"]
        
        else:
            return total_chars // 4  # 默认英文估算
    
    @staticmethod
    def estimate_batch(texts: List[str], method: str = "auto") -> int:
        """
        批量估算token
        
        Args:
            texts: 文本列表
            method: 估算方法
        
        Returns:
            总token估算数
        """
        return sum(TokenEstimator.estimate(t, method) for t in texts)
    
    @staticmethod
    def get_breakdown(text: str) -> dict:
        """
        获取文本token详细分解
        
        Returns:
            分解统计信息
        """
        if not text:
            return {"total": 0, "chinese": 0, "english": 0, "whitespace": 0, "other": 0}
        
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf]', text))
        whitespace_chars = len(re.findall(r'\s+', text))
        ascii_letters = len(re.findall(r'[a-zA-Z]', text))
        digits = len(re.findall(r'[0-9]', text))
        other_chars = len(text) - chinese_chars - whitespace_chars - ascii_letters - digits
        
        return {
            "total": TokenEstimator.estimate(text),
            "chinese_tokens": int(chinese_chars / TokenEstimator.COEFFICIENTS["chinese"]),
            "english_tokens": (ascii_letters + digits) // TokenEstimator.COEFFICIENTS["english"],
            "whitespace_tokens": int(whitespace_chars / TokenEstimator.COEFFICIENTS["whitespace"]),
            "other_tokens": other_chars // 4,
            "char_breakdown": {
                "chinese": chinese_chars,
                "whitespace": whitespace_chars,
                "ascii_letters": ascii_letters,
                "digits": digits,
                "other": other_chars
            }
        }


def main():
    """测试用例"""
    test_texts = [
        "Hello, this is a simple English sentence.",
        "这是一段中文文本，用来测试中文token估算。",
        "def hello():\n    print('Hello World')\n    return True",
        "混合文本Mix: 这里有一些中文mixed with English words.",
    ]
    
    print("Token Estimation Results / Token估算结果:")
    print("=" * 60)
    
    for text in test_texts:
        result = TokenEstimator.get_breakdown(text)
        print(f"\nText: {text[:50]}...")
        print(f"Estimated tokens: {result['total']}")
        print(f"Breakdown: {result['char_breakdown']}")


if __name__ == "__main__":
    main()