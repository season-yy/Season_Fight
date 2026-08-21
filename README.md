# Season Fight

![Season Fight 封面](static/season-fight-cover.png)

<p align="center">
  <strong>把每天想完成的事，变成看得见的进度。</strong><br>
  一个轻量、离线优先的个人学习监督工具。
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/Flask-3.0-black?logo=flask" alt="Flask 3.0">
  <img src="https://img.shields.io/badge/License-Personal%20use-7B61FF" alt="Personal use">
</p>

Season Fight 是一个运行在本机浏览器里的学习记录小工具。它不追求复杂的项目管理，而是想把「今天做什么、花了多久、有没有完成」这几件事变得足够直接。

> 适合拿来记录学习、刷题、写作、健身或任何需要每天推进一点点的事情。

## 它能做什么

- **安排任务**：创建当天任务，也可以提前规划未来 30 天。
- **专注计时**：为单个任务开始、暂停和结束计时。
- **完成提醒**：跨日仍未完成或未停止的任务会被标记，减少“忘了收尾”。
- **修改留痕**：编辑或删除任务必须填写理由，方便回顾变化。
- **数据复盘**：按日期查看完成情况、计时占比、分类分布和月度趋势。
- **关键词分析**：用中文分词找出容易拖延或未完成的任务类型。
- **局域网访问**：电脑启动后，同一 Wi‑Fi 下可用手机浏览器查看。

## 快速开始

### Windows：一键启动

直接双击 [start.bat](start.bat)。第一次运行会自动创建 `venv` 并安装依赖。

### 手动启动

```powershell
# 1. 创建并启用虚拟环境
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动服务
python app.py
```

打开 `http://localhost:1224` 即可使用。

想在手机上访问时，确保手机和电脑连接同一个 Wi‑Fi，然后打开启动窗口显示的本机 IP 地址，例如：`http://192.168.1.10:1224`。

## 使用方式

1. 输入任务名称和分类，点击“添加任务”。
2. 开始任务时点“开始”，结束时暂停或标记完成。
3. 在统计页看看时间花在哪里；在日历页回顾每天的完成情况。
4. 如果计划有变，编辑或删除时写下原因，给未来的自己留个解释。

## 我的小做法

这不是一个“逼自己努力”的工具，更像一个不会评判你的学习账本：

- 每天只先写下最重要的 1～3 件事，避免任务列表变成压力来源。
- 计时只用来观察投入，不用拿它和别人比较。
- 没完成也保留记录。看见模式，才知道下次该怎么调整。
- 周末花几分钟看一次统计：哪些事总被拖延、哪些分类真正占据了时间。

## 数据与隐私

应用数据保存在本机 `data/` 目录。该目录已被 Git 忽略，仓库**不会上传**你的任务名称、学习时长、修改记录或其他个人数据。

如果你需要备份自己的记录，请自行复制整个 `data/` 目录到安全的位置；恢复时再放回项目根目录即可。

## 项目结构

```text
Season_Fight/
├── app.py                 # Flask 入口与 API
├── config.py              # 端口、目录、统计等配置
├── core/
│   ├── task_manager.py    # 任务、计时与本地 JSON 存储
│   ├── statistics.py      # 统计与关键词分析
│   └── scheduler.py       # 跨日任务处理
├── static/                # 前端样式、脚本与项目封面
├── templates/             # 页面模板
├── data/                  # 本地个人数据（不提交）
├── requirements.txt       # Python 依赖
└── start.bat              # Windows 一键启动
```

## 配置

可在 [config.py](config.py) 修改：

- `PORT`：服务端口，默认 `1224`
- `MAX_PLAN_DAYS`：允许提前规划的天数，默认 `30`
- `HISTORY_DAYS`：统计默认回顾天数，默认 `30`
- `SUGGESTED_CATEGORIES`：任务分类建议

## 技术栈

- 后端：Flask + APScheduler
- 前端：原生 HTML / CSS / JavaScript
- 数据：本地 JSON 文件
- 中文分析：jieba

## 许可

这个项目目前仅供个人学习和使用。欢迎拿去改成更适合自己的样子。
