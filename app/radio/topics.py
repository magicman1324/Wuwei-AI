"""电台节目话题池。日期决定当天选哪一个，无需随机以保证可复现。"""
from __future__ import annotations

from datetime import date


HEALTH_TOPICS: list[str] = [
    "夏天科学饮水的小学问",
    "高血压老人的日常注意事项",
    "饭后散步的好处与误区",
    "如何识别中风的早期预警",
    "老年人骨质疏松的防护",
    "睡眠不好的几个改善办法",
    "适合老年人的居家小运动",
    "三高人群的饮食原则",
    "预防跌倒的家庭小改造",
    "感冒和流感的区别",
    "老人用药安全提醒",
    "老花眼的日常护理",
    "天气转凉时心血管的保养",
    "饭桌上的盐糖油怎么把控",
    "夜里腿抽筋怎么办",
]


# 怀旧分两个子类：老生活记忆 + 戏曲赏析
NOSTALGIA_TOPICS: list[tuple[str, str]] = [
    # (subtopic, title)
    ("old_life", "蜂窝煤的记忆"),
    ("old_life", "凭票买粮的年代"),
    ("old_life", "永久牌自行车与铃铛声"),
    ("old_life", "老式收音机里的评书"),
    ("old_life", "六十年代的露天电影"),
    ("old_life", "走街串巷的剃头匠"),
    ("old_life", "煤油灯下的夜晚"),
    ("old_life", "供销社的玻璃糖罐"),
    ("opera", "京剧《贵妃醉酒》——梅兰芳的雍容"),
    ("opera", "京剧《空城计》——诸葛亮的从容"),
    ("opera", "越剧《梁山伯与祝英台》"),
    ("opera", "豫剧《花木兰》——常香玉的英气"),
    ("opera", "评剧《花为媒》——新凤霞的灵动"),
    ("opera", "黄梅戏《天仙配》——严凤英的婉转"),
    ("opera", "川剧变脸的奥妙"),
    ("opera", "昆曲《牡丹亭·游园惊梦》"),
]


def pick_health_topic(d: date) -> str:
    return HEALTH_TOPICS[d.toordinal() % len(HEALTH_TOPICS)]


def pick_nostalgia_topic(d: date) -> tuple[str, str]:
    """返回 (subtopic, title)。日期错位选取，避免 health/nostalgia 总踩同一节奏。"""
    idx = (d.toordinal() + 7) % len(NOSTALGIA_TOPICS)
    return NOSTALGIA_TOPICS[idx]
