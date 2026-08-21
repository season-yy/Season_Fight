"""任务管理器 - JSON 文件 CRUD + 文件锁"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

from config import TASKS_DIR, PLANS_DIR, ARCHIVE_DIR


# ============== 文件 I/O 工具 ==============

def _ensure_file(path: Path) -> None:
    """确保 JSON 文件存在，不存在则创建空结构"""
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({'date': path.stem, 'stats': {}, 'tasks': []}, f,
                      ensure_ascii=False, indent=2)


def _read_json(path: Path) -> Dict[str, Any]:
    """读取 JSON 文件"""
    _ensure_file(path)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _write_json(path: Path, data: Dict[str, Any]) -> None:
    """写入 JSON 文件（原子写：先写临时文件再 rename）"""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix('.tmp')
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    # 原子替换，避免写入中途崩溃导致文件损坏
    os.replace(tmp_path, path)


# ============== 任务对象工厂 ==============

def make_task(name: str, category: str, planned_date: str = None,
              is_planned: bool = False) -> Dict[str, Any]:
    """创建新任务对象"""
    if planned_date is None:
        planned_date = datetime.now().strftime('%Y-%m-%d')
    return {
        'id': str(uuid.uuid4()),
        'name': name.strip(),
        'category': category.strip() or '其他',
        'status': 'pending',
        'created_at': datetime.now().isoformat(timespec='seconds'),
        'planned_date': planned_date,
        'is_planned': is_planned,
        'started_at': None,
        'ended_at': None,
        'duration_seconds': 0,
        'auto_ended': False,
        'is_modified': False,
        'notes': '',
        'history': [],
    }


# ============== 每日数据加载/保存 ==============

def load_day(date: str) -> Dict[str, Any]:
    """加载某日任务数据"""
    path = TASKS_DIR / f'{date}.json'
    return _read_json(path)


def save_day(date: str, data: Dict[str, Any]) -> None:
    """保存某日任务数据"""
    path = TASKS_DIR / f'{date}.json'
    # 更新统计
    data['date'] = date
    data['stats'] = _calc_stats(data.get('tasks', []))
    _write_json(path, data)


def load_plan(date: str) -> Dict[str, Any]:
    """
    加载某日的未来计划任务
    注意：如果文件不存在，返回空结构但不会主动创建文件
    """
    path = PLANS_DIR / f'{date}.json'
    if not path.exists():
        return {'date': date, 'stats': {'total': 0}, 'tasks': []}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_plan(date: str, data: Dict[str, Any]) -> None:
    """保存某日的未来计划任务"""
    path = PLANS_DIR / f'{date}.json'
    data['date'] = date
    data['stats'] = {'total': len(data.get('tasks', []))}
    _write_json(path, data)


# ============== 任务查找 ==============

def find_task(task_id: str, search_days: int = 60) -> Optional[Tuple[Dict[str, Any], str]]:
    """
    在最近 N 天（含今日）和未来 30 天计划中查找任务
    返回: (task对象, 日期字符串) 或 None
    """
    from datetime import timedelta
    today = datetime.now().date()

    # 先查今日及最近历史
    for offset in range(0, search_days):
        date = (today - timedelta(days=offset)).strftime('%Y-%m-%d')
        try:
            day_data = load_day(date)
            for task in day_data.get('tasks', []):
                if task['id'] == task_id:
                    return task, date
        except Exception:
            continue

    # 再查未来计划
    for offset in range(1, 31):
        date = (today + timedelta(days=offset)).strftime('%Y-%m-%d')
        try:
            plan_data = load_plan(date)
            for task in plan_data.get('tasks', []):
                if task['id'] == task_id:
                    return task, date
        except Exception:
            continue

    return None


# ============== 任务操作 ==============

def create_task(name: str, category: str, date: str = None,
                planned_date: str = None) -> Dict[str, Any]:
    """
    创建任务
    - 如果 planned_date > 今天 → 存到 plans/
    - 否则 → 存到 tasks/<date>.json
    """
    today = datetime.now().strftime('%Y-%m-%d')
    if date is None:
        date = today

    # 判断是计划任务还是今日任务
    if planned_date and planned_date > today:
        task = make_task(name, category, planned_date, is_planned=True)
        plan_data = load_plan(planned_date)
        plan_data.setdefault('tasks', []).append(task)
        save_plan(planned_date, plan_data)
    else:
        task = make_task(name, category, date, is_planned=False)
        day_data = load_day(date)
        day_data.setdefault('tasks', []).append(task)
        save_day(date, day_data)
    return task


def start_task(task_id: str) -> Optional[Dict[str, Any]]:
    """开始任务计时（支持 pending/running/paused 三种状态恢复计时）"""
    result = find_task(task_id)
    if not result:
        return None
    task, date = result
    # 允许 pending、running、paused 三种状态开始/恢复计时
    if task['status'] not in ('pending', 'running', 'paused'):
        return task

    task['status'] = 'running'
    task['started_at'] = datetime.now().isoformat(timespec='seconds')
    # 累加之前暂停的时长
    if 'paused_at' in task and task['paused_at']:
        task['duration_seconds'] += _elapsed_since(task['paused_at'])
        task['paused_at'] = None
    _save_task_back(task, date)
    return task


def pause_task(task_id: str) -> Optional[Dict[str, Any]]:
    """暂停任务"""
    result = find_task(task_id)
    if not result:
        return None
    task, date = result
    if task['status'] != 'running':
        return task

    task['paused_at'] = datetime.now().isoformat(timespec='seconds')
    task['duration_seconds'] += _elapsed_since(task['started_at'])
    task['started_at'] = None
    task['status'] = 'paused'
    _save_task_back(task, date)
    return task


def complete_task(task_id: str) -> Optional[Dict[str, Any]]:
    """完成任务（点击 ✔）"""
    result = find_task(task_id)
    if not result:
        return None
    task, date = result

    # 计算最终时长
    if task['status'] == 'running' and task['started_at']:
        task['duration_seconds'] += _elapsed_since(task['started_at'])
    elif task.get('paused_at'):
        task['duration_seconds'] += _elapsed_since(task['paused_at'])

    task['status'] = 'completed'
    task['ended_at'] = datetime.now().isoformat(timespec='seconds')
    task['started_at'] = None
    task['paused_at'] = None
    _save_task_back(task, date)
    return task


def update_task(task_id: str, changes: Dict[str, Any], reason: str) -> Optional[Dict[str, Any]]:
    """
    更新任务（编辑），必须提供 reason
    changes 可包含: name, category
    """
    if not reason or len(reason.strip()) < 2:
        raise ValueError('请填写修改理由（至少 2 个字）')

    result = find_task(task_id)
    if not result:
        return None
    task, date = result

    before = {'name': task['name'], 'category': task['category']}
    if 'name' in changes and changes['name']:
        task['name'] = changes['name'].strip()
    if 'category' in changes and changes['category']:
        task['category'] = changes['category'].strip()
    after = {'name': task['name'], 'category': task['category']}

    task['is_modified'] = True
    task['history'].append({
        'action': 'edit',
        'timestamp': datetime.now().isoformat(timespec='seconds'),
        'reason': reason.strip(),
        'before': before,
        'after': after,
    })
    _save_task_back(task, date)
    return task


def delete_task(task_id: str, reason: str) -> bool:
    """删除任务（归档到 archive/），必须提供 reason"""
    if not reason or len(reason.strip()) < 2:
        raise ValueError('请填写删除理由（至少 2 个字）')

    result = find_task(task_id)
    if not result:
        return False
    task, date = result

    # 归档
    archive_file = ARCHIVE_DIR / f'{date}.json'
    archive_file.parent.mkdir(parents=True, exist_ok=True)
    archive_data = _read_json(archive_file) if archive_file.exists() else {'tasks': []}
    task['deleted_at'] = datetime.now().isoformat(timespec='seconds')
    task['delete_reason'] = reason.strip()
    archive_data['tasks'].append(task)
    _write_json(archive_file, archive_data)

    # 从原文件中删除
    day_data = load_day(date)
    day_data['tasks'] = [t for t in day_data.get('tasks', []) if t['id'] != task_id]
    save_day(date, day_data)
    return True


# ============== 内部工具 ==============

def _elapsed_since(iso_time: str) -> int:
    """计算从 ISO 时间到现在的秒数"""
    try:
        start = datetime.fromisoformat(iso_time)
        return int((datetime.now() - start).total_seconds())
    except Exception:
        return 0


def _save_task_back(task: Dict[str, Any], date: str) -> None:
    """保存任务回对应日期的 JSON"""
    day_data = load_day(date)
    for i, t in enumerate(day_data.get('tasks', [])):
        if t['id'] == task['id']:
            day_data['tasks'][i] = task
            break
    save_day(date, day_data)


def _calc_stats(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """计算每日统计"""
    total = len(tasks)
    completed = sum(1 for t in tasks if t['status'] == 'completed')
    uncompleted = sum(1 for t in tasks if t['status'] == 'uncompleted')
    pending = sum(1 for t in tasks if t['status'] in ('pending', 'running', 'paused'))
    modified = sum(1 for t in tasks if t.get('is_modified'))
    total_seconds = sum(t.get('duration_seconds', 0) for t in tasks)
    return {
        'total': total,
        'completed': completed,
        'uncompleted': uncompleted,
        'pending': pending,
        'modified': modified,
        'completion_rate': round(completed / total, 3) if total > 0 else 0,
        'total_seconds': total_seconds,
    }


def auto_end_running_tasks(date: str) -> int:
    """
    自动结束某日所有 running/paused 状态的任务（凌晨0点调用）
    - running：停止并累计时长
    - paused：清理暂停时间戳，避免暂停时段被计入
    返回受影响的任务数
    """
    day_data = load_day(date)
    count = 0
    for task in day_data.get('tasks', []):
        if task['status'] == 'running':
            # 累计从启动到现在的时长
            if task['started_at']:
                task['duration_seconds'] += _elapsed_since(task['started_at'])
            task['status'] = 'uncompleted'
            task['auto_ended'] = True
            task['ended_at'] = f"{date}T23:59:59"
            task['started_at'] = None
            count += 1
        elif task['status'] == 'paused':
            # paused 任务过了一夜同样算未完成
            # paused_at 不计入 duration（暂停期间不计时）
            task['status'] = 'uncompleted'
            task['auto_ended'] = True
            task['ended_at'] = f"{date}T23:59:59"
            task['paused_at'] = None
            count += 1
    if count > 0:
        save_day(date, day_data)
    return count


def migrate_plans_to_today() -> int:
    """将今日对应的未来计划任务迁移到今日任务列表"""
    from datetime import datetime as _dt
    today = _dt.now().strftime('%Y-%m-%d')
    plan_file = PLANS_DIR / f'{today}.json'
    if not plan_file.exists():
        return 0

    plan_data = load_plan(today)
    if not plan_data.get('tasks'):
        return 0

    day_data = load_day(today)
    migrated = 0
    for plan in plan_data['tasks']:
        plan['is_planned'] = False
        plan['status'] = 'pending'
        plan['planned_date'] = today
        day_data.setdefault('tasks', []).append(plan)
        migrated += 1

    save_day(today, day_data)
    # 清空已迁移的计划文件
    plan_file.unlink()
    return migrated
