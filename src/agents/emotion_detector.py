"""
情感检测模块 - 识别用户输入中的情绪状态
"""
from enum import Enum
from typing import Optional
from dataclasses import dataclass


class EmotionTag(Enum):
    """情绪标签"""
    POSITIVE = "positive"       # 积极/自信
    NEUTRAL = "neutral"         # 中性/专注
    CONFUSED = "confused"      # 困惑/不确定
    FRUSTRATED = "frustrated"   # 挫败/沮丧
    RESISTANT = "resistant"     # 抵触/抗拒
    UNKNOWN = "unknown"         # 未知


@dataclass
class EmotionResult:
    """情绪检测结果"""
    tag: EmotionTag
    confidence: float  # 0.0 - 1.0
    suggested_response: str  # 建议的回复策略


# 负面情绪关键词（中文）
NEGATIVE_KEYWORDS = {
    EmotionTag.RESISTANT: [
        "不想学", "不要", "太麻烦了", "不可能", "浪费时间",
        "没意义", "不喜欢", "抵触", "抗拒", "排斥"
    ],
    EmotionTag.FRUSTRATED: [
        "太难了", "看不懂", "不会", "听不懂", "卡住了",
        "崩溃", "挫折", "失败", "搞不定", "太复杂"
    ],
    EmotionTag.CONFUSED: [
        "什么是", "怎么", "为什么", "不太明白", "不清楚",
        "疑问", "困惑", "迷糊", "搞不清", "区别"
    ]
}

# 正面情绪关键词
POSITIVE_KEYWORDS = [
    "懂了", "明白了", "好的", "没问题", "可以", "理解",
    "谢谢", "好的", "清楚", "了解"
]


class EmotionDetector:
    """情感检测器"""

    def __init__(self):
        self.negative_keywords = NEGATIVE_KEYWORDS
        self.positive_keywords = POSITIVE_KEYWORDS

    def detect(self, user_input: str) -> EmotionResult:
        """
        检测用户输入中的情绪

        Args:
            user_input: 用户输入文本

        Returns:
            EmotionResult: 包含情绪标签、置信度和建议回复
        """
        text = user_input.lower().strip()

        # 1. 检查正面情绪
        for keyword in self.positive_keywords:
            if keyword in text:
                return EmotionResult(
                    tag=EmotionTag.POSITIVE,
                    confidence=0.8,
                    suggested_response="鼓励继续，确认下一步"
                )

        # 2. 检查各类负面情绪
        for emotion, keywords in self.negative_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    confidence = 0.6 + (len(keyword) / 20)  # 关键词越长置信度越高
                    confidence = min(confidence, 0.95)

                    response_map = {
                        EmotionTag.RESISTANT: "先共情，理解顾虑，再引导尝试",
                        EmotionTag.FRUSTRATED: "降低难度，提供更多示例，鼓励小步前进",
                        EmotionTag.CONFUSED: "用更简单的方式解释，提供具体例子"
                    }

                    return EmotionResult(
                        tag=emotion,
                        confidence=min(confidence, 0.95),
                        suggested_response=response_map.get(emotion, "提供支持和帮助")
                    )

        # 3. 检查是否为空或太短
        if not text or len(text) < 2:
            return EmotionResult(
                tag=EmotionTag.NEUTRAL,
                confidence=0.5,
                suggested_response="继续当前话题"
            )

        # 4. 默认为中性
        return EmotionResult(
            tag=EmotionTag.NEUTRAL,
            confidence=0.6,
            suggested_response="继续当前话题"
        )

    def detect_with_llm(self, user_input: str, llm_client) -> EmotionResult:
        """
        使用 LLM 进行更深入的情绪检测（可选增强）

        Args:
            user_input: 用户输入文本
            llm_client: LLM 客户端实例

        Returns:
            EmotionResult: 更准确的情绪检测结果
        """
        prompt = f"""用户输入："{user_input}"

请分析这段文字的情绪状态，只返回一个 JSON 对象：
{{"tag": "positive/neutral/confused/frustrated/resistant", "confidence": 0.0-1.0, "reason": "原因"}}

只返回 JSON，不要其他内容。"""

        try:
            response = llm_client.generate(
                system_prompt="你是一个情绪分析助手。",
                user_message=prompt
            )

            import json
            result = json.loads(response)
            tag_map = {
                "positive": EmotionTag.POSITIVE,
                "neutral": EmotionTag.NEUTRAL,
                "confused": EmotionTag.CONFUSED,
                "frustrated": EmotionTag.FRUSTRATED,
                "resistant": EmotionTag.RESISTANT,
            }

            return EmotionResult(
                tag=tag_map.get(result.get("tag", "neutral"), EmotionTag.NEUTRAL),
                confidence=result.get("confidence", 0.5),
                suggested_response="基于 LLM 分析的回复建议"
            )
        except Exception:
            # 如果 LLM 检测失败，回退到规则检测
            return self.detect(user_input)