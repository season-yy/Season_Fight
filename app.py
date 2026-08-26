"""Season_Fight 学习监督应用 - Flask 主入口"""

import logging
from datetime import datetime, timedelta
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_from_directory

from config import (
    HOST, PORT, DEBUG, MAX_PLAN_DAYS, SUGGESTED_CATEGORIES, BASE_DIR,
)
from core.task_manager import (
    load_day, load_day_with_due_plans, save_day, load_plan, save_plan,
    create_task, start_task, pause_task, complete_task,
    update_task, delete_task, auto_end_running_tasks,
    migrate_plans_to_today,
)
from core.statistics import (
    analyze_unfinished_keywords, analyze_category_distribution,
    get_monthly_trend, get_calendar_data, get_today_overview,
    get_daily_pie_data,
)
from core.scheduler import start_scheduler, stop_scheduler

# ============== 日志配置 ==============
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger('season_fight')


# ============== Flask 应用 ==============
app = Flask(__name__, static_folder=str(BASE_DIR / 'static'),
            template_folder=str(BASE_DIR / 'templates'))


# ============== 页面路由 ==============

@app.route('/')
def index():
    """主页"""
    return render_template('index.html',
                           categories=SUGGESTED_CATEGORIES,
                           max_plan_days=MAX_PLAN_DAYS,
                           port=PORT)


# ============== 任务 CRUD ==============

@app.route('/api/tasks', methods=['GET'])
def api_get_tasks():
    """获取某日任务列表"""
    date = request.args.get('date') or datetime.now().strftime('%Y-%m-%d')
    data = load_day_with_due_plans(date)
    return jsonify(data)


@app.route('/api/tasks', methods=['POST'])
def api_create_task():
    """创建任务（今日或未来计划）"""
    payload = request.json or {}
    name = (payload.get('name') or '').strip()
    category = (payload.get('category') or '其他').strip()
    planned_date = payload.get('planned_date')

    if not name:
        return jsonify({'error': '请填写任务名'}), 400

    # 校验 planned_date
    if planned_date:
        try:
            target = datetime.strptime(planned_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': '日期格式错误，应为 YYYY-MM-DD'}), 400
        today = datetime.now().date()
        if (target - today).days < 0:
            return jsonify({'error': '不能规划过去的日期'}), 400
        if (target - today).days > MAX_PLAN_DAYS:
            return jsonify({'error': f'最多只能提前规划 {MAX_PLAN_DAYS} 天'}), 400

    task = create_task(name, category, planned_date=planned_date)
    return jsonify({'success': True, 'task': task})


@app.route('/api/tasks/<task_id>', methods=['PATCH'])
def api_update_task(task_id):
    """更新任务（必须提供 reason）"""
    payload = request.json or {}
    reason = (payload.get('reason') or '').strip()
    try:
        task = update_task(task_id, payload, reason)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    if not task:
        return jsonify({'error': '任务不存在'}), 404
    return jsonify({'success': True, 'task': task})


@app.route('/api/tasks/<task_id>', methods=['DELETE'])
def api_delete_task(task_id):
    """删除任务（必须提供 reason）"""
    reason = (request.args.get('reason') or '').strip()
    try:
        ok = delete_task(task_id, reason)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    if not ok:
        return jsonify({'error': '任务不存在'}), 404
    return jsonify({'success': True})


# ============== 计时器控制 ==============

@app.route('/api/timer/start/<task_id>', methods=['POST'])
def api_timer_start(task_id):
    task = start_task(task_id)
    if not task:
        return jsonify({'error': '任务不存在'}), 404
    return jsonify({'success': True, 'task': task})


@app.route('/api/timer/pause/<task_id>', methods=['POST'])
def api_timer_pause(task_id):
    task = pause_task(task_id)
    if not task:
        return jsonify({'error': '任务不存在'}), 404
    return jsonify({'success': True, 'task': task})


@app.route('/api/timer/complete/<task_id>', methods=['POST'])
def api_timer_complete(task_id):
    task = complete_task(task_id)
    if not task:
        return jsonify({'error': '任务不存在'}), 404
    return jsonify({'success': True, 'task': task})


# ============== 未来计划任务 ==============

@app.route('/api/plans', methods=['GET'])
def api_get_plans():
    """获取某日的未来计划任务"""
    date = request.args.get('date')
    if not date:
        return jsonify({'error': '请提供日期'}), 400
    return jsonify(load_plan(date))


@app.route('/api/plans', methods=['POST'])
def api_create_plan():
    """创建未来计划任务"""
    payload = request.json or {}
    name = (payload.get('name') or '').strip()
    category = (payload.get('category') or '其他').strip()
    planned_date = payload.get('planned_date')

    if not name or not planned_date:
        return jsonify({'error': '请填写任务名和计划日期'}), 400

    try:
        target = datetime.strptime(planned_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': '日期格式错误'}), 400

    today = datetime.now().date()
    if (target - today).days < 0:
        return jsonify({'error': '不能规划过去的日期'}), 400
    if (target - today).days > MAX_PLAN_DAYS:
        return jsonify({'error': f'最多只能提前规划 {MAX_PLAN_DAYS} 天'}), 400

    task = create_task(name, category, planned_date=planned_date)
    return jsonify({'success': True, 'task': task})


@app.route('/api/plans/range', methods=['GET'])
def api_get_plans_range():
    """获取未来 N 天的所有计划任务（用于日历视图）"""
    today = datetime.now().date()
    plans = []
    for offset in range(1, MAX_PLAN_DAYS + 1):
        date = (today + timedelta(days=offset)).strftime('%Y-%m-%d')
        data = load_plan(date)
        if data.get('tasks'):
            plans.append({'date': date, 'tasks': data['tasks']})
    return jsonify({'plans': plans})


# ============== 统计 ==============

@app.route('/api/stats/today', methods=['GET'])
def api_stats_today():
    return jsonify(get_today_overview())


@app.route('/api/stats/month', methods=['GET'])
def api_stats_month():
    year = int(request.args.get('year', datetime.now().year))
    month = int(request.args.get('month', datetime.now().month))
    return jsonify(get_monthly_trend(year, month))


@app.route('/api/stats/keywords', methods=['GET'])
def api_stats_keywords():
    days = int(request.args.get('days', 30))
    top_n = int(request.args.get('top_n', 10))
    keywords = analyze_unfinished_keywords(days, top_n)
    return jsonify({'days': days, 'keywords': keywords})


@app.route('/api/stats/categories', methods=['GET'])
def api_stats_categories():
    days = int(request.args.get('days', 30))
    return jsonify({'days': days, 'categories': analyze_category_distribution(days)})


@app.route('/api/stats/pie/<date>', methods=['GET'])
def api_stats_pie(date):
    """某日各任务计时占比（用于饼状图）"""
    return jsonify(get_daily_pie_data(date))


# ============== 日历 ==============

@app.route('/api/calendar', methods=['GET'])
def api_calendar():
    year = int(request.args.get('year', datetime.now().year))
    month = int(request.args.get('month', datetime.now().month))
    return jsonify(get_calendar_data(year, month))


@app.route('/api/day/<date>', methods=['GET'])
def api_day(date):
    """获取某日详情"""
    data = load_day(date)
    data['pie'] = get_daily_pie_data(date)
    return jsonify(data)


# ============== 健康检查 & 调试 ==============

@app.route('/api/health', methods=['GET'])
def api_health():
    return jsonify({
        'status': 'ok',
        'app': 'Season_Fight',
        'time': datetime.now().isoformat(timespec='seconds'),
        'port': PORT,
    })


@app.route('/api/server/info', methods=['GET'])
def api_server_info():
    """返回服务器信息（手机访问时显示电脑端 IP）"""
    import socket
    try:
        # 获取本机 IP（局域网）
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
    except Exception:
        local_ip = '127.0.0.1'
    return jsonify({
        'local_ip': local_ip,
        'port': PORT,
        'max_plan_days': MAX_PLAN_DAYS,
        'suggested_categories': SUGGESTED_CATEGORIES,
    })


@app.route('/api/dev/trigger_midnight', methods=['POST'])
def api_dev_trigger_midnight():
    """开发模式：手动触发凌晨任务（用于测试跨日逻辑）"""
    if not DEBUG:
        return jsonify({'error': '仅 debug 模式可用'}), 403

    from core.scheduler import midnight_job
    midnight_job()
    return jsonify({'success': True, 'message': '已触发凌晨任务'})


@app.route('/api/dev/advance_day', methods=['POST'])
def api_dev_advance_day():
    """开发模式：手动迁移今日计划任务（用于测试跨日迁移）"""
    if not DEBUG:
        return jsonify({'error': '仅 debug 模式可用'}), 403
    count = migrate_plans_to_today()
    return jsonify({'success': True, 'migrated': count})


# ============== 错误处理 ==============

@app.errorhandler(404)
def not_found(_e):
    if request.path.startswith('/api/'):
        return jsonify({'error': '接口不存在'}), 404
    return render_template('index.html'), 200


@app.errorhandler(500)
def server_error(e):
    logger.error(f'[服务器错误] {e}')
    return jsonify({'error': '服务器内部错误'}), 500


# ============== 启动 ==============

if __name__ == '__main__':
    logger.info('=' * 60)
    logger.info('  Season_Fight 学习监督应用 启动中...')
    logger.info('=' * 60)
    logger.info(f'  端口: {PORT}')
    logger.info(f'  数据目录: {BASE_DIR / "data"}')
    logger.info('=' * 60)

    # 补偿应用未在凌晨运行、电脑休眠等情况导致的计划任务漏迁移。
    migrated_count = migrate_plans_to_today()
    if migrated_count > 0:
        logger.info(f'  已迁移 {migrated_count} 个今日计划任务')

    # 启动定时任务
    start_scheduler()

    # 启动 Flask
    try:
        app.run(host=HOST, port=PORT, debug=DEBUG, use_reloader=False, threaded=True)
    except KeyboardInterrupt:
        logger.info('收到退出信号，正在关闭...')
    finally:
        stop_scheduler()
