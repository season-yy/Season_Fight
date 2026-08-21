"""统计分析模块 - jieba 关键词分析 + 聚合统计"""

import json
import glob
from collections import Counter
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Any

import jieba

from config import TASKS_DIR, PLANS_DIR, STOPWORDS, HISTORY_DAYS


# ============== 关键词分析 ==============

def analyze_unfinished_keywords(days: int = HISTORY_DAYS, top_n: int = 10) -> List[Tuple[str, int]]:
    """
    分析最近 N 天未完成任务的关键词 Top N
    返回: [(关键词, 出现次数), ...]
    """
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    all_words = []

    for json_file in glob.glob(str(TASKS_DIR / '*.json')):
        date_str = json_file.split('\\')[-1].replace('.json', '')
        if date_str < cutoff_date:
            continue
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                day_data = json.load(f)
        except Exception:
            continue

        for task in day_data.get('tasks', []):
            if task['status'] == 'uncompleted':
                # 同时分析任务名和分类
                text = f"{task['name']} {task.get('category', '')}"
                words = jieba.lcut(text)
                filtered = [
                    w for w in words
                    if len(w) > 1
                    and w not in STOPWORDS
                    and not w.isdigit()
                    and not w.isspace()
                ]
                all_words.extend(filtered)

    return Counter(all_words).most_common(top_n)


# ============== 分类统计 ==============

def analyze_category_distribution(days: int = HISTORY_DAYS) -> List[Dict[str, Any]]:
    """
    分析最近 N 天任务分类分布（所有任务，包括完成的）
    返回: [{name: 分类名, count: 任务数, total_seconds: 总时长}, ...]
    """
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    cat_counter = Counter()
    cat_seconds = {}

    for json_file in glob.glob(str(TASKS_DIR / '*.json')):
        date_str = json_file.split('\\')[-1].replace('.json', '')
        if date_str < cutoff_date:
            continue
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                day_data = json.load(f)
        except Exception:
            continue

        for task in day_data.get('tasks', []):
            cat = task.get('category', '其他')
            cat_counter[cat] += 1
            cat_seconds[cat] = cat_seconds.get(cat, 0) + task.get('duration_seconds', 0)

    return [
        {'name': cat, 'count': count, 'total_seconds': cat_seconds[cat]}
        for cat, count in cat_counter.most_common()
    ]


# ============== 月度趋势 ==============

def get_monthly_trend(year: int, month: int) -> Dict[str, Any]:
    """
    获取某月每日的完成率趋势
    返回: {days: [{date, total, completed, completion_rate}, ...]}
    """
    from calendar import monthrange
    days_in_month = monthrange(year, month)[1]
    days_data = []

    for day in range(1, days_in_month + 1):
        date_str = f'{year}-{month:02d}-{day:02d}'
        json_file = TASKS_DIR / f'{date_str}.json'
        if not json_file.exists():
            continue
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                day_data = json.load(f)
        except Exception:
            continue

        stats = day_data.get('stats', {})
        days_data.append({
            'date': date_str,
            'total': stats.get('total', 0),
            'completed': stats.get('completed', 0),
            'completion_rate': stats.get('completion_rate', 0),
        })

    return {'year': year, 'month': month, 'days': days_data}


# ============== 日历数据 ==============

def get_calendar_data(year: int, month: int) -> Dict[str, Any]:
    """
    获取某月日历数据（每日完成率）
    返回: {days: {date: {total, completed, completion_rate, modified, status}, ...}}
    """
    from calendar import monthrange
    days_in_month = monthrange(year, month)[1]
    days = {}

    for day in range(1, days_in_month + 1):
        date_str = f'{year}-{month:02d}-{day:02d}'
        json_file = TASKS_DIR / f'{date_str}.json'
        if not json_file.exists():
            continue
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                day_data = json.load(f)
        except Exception:
            continue

        stats = day_data.get('stats', {})
        rate = stats.get('completion_rate', 0)
        # 状态分类：excellent/good/poor/failed
        if rate >= 0.8:
            status = 'excellent'
        elif rate >= 0.5:
            status = 'good'
        elif rate > 0:
            status = 'poor'
        else:
            status = 'failed'

        days[date_str] = {
            'total': stats.get('total', 0),
            'completed': stats.get('completed', 0),
            'completion_rate': rate,
            'modified': stats.get('modified', 0),
            'status': status,
        }

    return {'year': year, 'month': month, 'days': days}


# ============== 今日概览 ==============

def get_today_overview() -> Dict[str, Any]:
    """获取今日概览数据"""
    today = datetime.now().strftime('%Y-%m-%d')
    json_file = TASKS_DIR / f'{today}.json'
    if not json_file.exists():
        return {
            'date': today,
            'stats': {'total': 0, 'completed': 0, 'uncompleted': 0,
                      'pending': 0, 'modified': 0, 'completion_rate': 0,
                      'total_seconds': 0},
            'tasks': [],
            'current_task': None,
        }
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        data = {'tasks': []}

    # 找出当前正在运行的任务
    current = None
    for t in data.get('tasks', []):
        if t['status'] == 'running':
            current = t
            break

    return {
        'date': today,
        'stats': data.get('stats', {}),
        'tasks': data.get('tasks', []),
        'current_task': current,
    }


# ============== 每日饼状图数据 ==============

def get_daily_pie_data(date: str) -> Dict[str, Any]:
    """
    获取某日各任务计时占比数据
    返回: {date, items: [{name, seconds, category}, ...]}
    """
    json_file = TASKS_DIR / f'{date}.json'
    if not json_file.exists():
        return {'date': date, 'items': []}

    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            day_data = json.load(f)
    except Exception:
        return {'date': date, 'items': []}

    items = [
        {
            'name': t['name'],
            'seconds': t.get('duration_seconds', 0),
            'category': t.get('category', '其他'),
            'status': t.get('status'),
        }
        for t in day_data.get('tasks', [])
        if t.get('duration_seconds', 0) > 0
    ]

    # 按秒数降序
    items.sort(key=lambda x: x['seconds'], reverse=True)
    return {'date': date, 'items': items}
