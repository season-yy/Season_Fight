"""Season_Fight 配置文件 - 端口、路径、Jieba 配置"""

import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent

# 数据存储目录
DATA_DIR = BASE_DIR / 'data'
TASKS_DIR = DATA_DIR / 'tasks'        # 每日实际任务 JSON
PLANS_DIR = DATA_DIR / 'plans'        # 未来计划任务 JSON
ARCHIVE_DIR = DATA_DIR / 'archive'    # 已删除任务归档
KEYWORDS_CACHE = DATA_DIR / 'keywords_cache.json'

# 网络配置
HOST = '0.0.0.0'   # 绑定所有网卡，允许手机端访问
PORT = 1224        # 用户指定的端口（非默认 5000）
DEBUG = False      # 生产模式，节省内存

# 业务配置
MAX_PLAN_DAYS = 30  # 未来任务最大可提前规划的天数
HISTORY_DAYS = 30   # 关键词统计默认分析最近天数

# 常用任务分类预设（用户可自由输入）
SUGGESTED_CATEGORIES = [
    'AI学习',
    '深度学习',
    '课题学习',
    '英语',
    '数学',
    '编程',
    '阅读',
    '写作',
    '其他',
]

# 关键词停用词（jieba 分词后过滤）
STOPWORDS = {
    '的', '了', '和', '是', '在', '我', '你', '他', '她', '它',
    '一', '个', '上', '下', '不', '就', '都', '也', '要', '把',
    '被', '让', '从', '到', '为', '以', '对', '有', '这', '那',
    '什么', '怎么', '为什么', '吗', '吧', '啊', '哦', '嗯',
    '做', '学', '看', '听', '写', '想', '说', '给', '去',
}

# 确保数据目录存在
for _d in [TASKS_DIR, PLANS_DIR, ARCHIVE_DIR]:
    _d.mkdir(parents=True, exist_ok=True)
