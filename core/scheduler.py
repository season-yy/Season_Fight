"""APScheduler 定时任务模块"""

import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from core.task_manager import auto_end_running_tasks, migrate_plans_to_today

logger = logging.getLogger(__name__)

# 全局 scheduler 实例
_scheduler: BackgroundScheduler = None


def midnight_job():
    """凌晨 00:00 触发的任务：
    1. 自动结束昨日所有 running 状态的任务
    2. 迁移今日的未来计划任务
    """
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    today = datetime.now().strftime('%Y-%m-%d')

    try:
        ended_count = auto_end_running_tasks(yesterday)
        if ended_count > 0:
            logger.info(f'[凌晨任务] 自动结束 {ended_count} 个未完成任务（{yesterday}）')
    except Exception as e:
        logger.error(f'[凌晨任务] 自动结束任务失败: {e}')

    try:
        migrated_count = migrate_plans_to_today()
        if migrated_count > 0:
            logger.info(f'[凌晨任务] 迁移 {migrated_count} 个未来计划任务到今日（{today}）')
    except Exception as e:
        logger.error(f'[凌晨任务] 迁移计划任务失败: {e}')


def start_scheduler() -> BackgroundScheduler:
    """启动定时调度器"""
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    _scheduler = BackgroundScheduler(timezone='Asia/Shanghai')
    # 每天凌晨 00:00 触发
    _scheduler.add_job(
        midnight_job,
        CronTrigger(hour=0, minute=0),
        id='midnight_job',
        name='凌晨自动结束未完成任务 + 迁移计划任务',
        replace_existing=True,
    )
    _scheduler.start()
    logger.info('[调度器] 定时任务已启动：每天 00:00 自动结束未完成任务')
    return _scheduler


def stop_scheduler():
    """停止调度器"""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info('[调度器] 定时任务已停止')
