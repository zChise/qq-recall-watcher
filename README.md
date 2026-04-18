# 猫萌 · QQ 防撤回工具

基于 [NapCat](https://github.com/NapNeko/NapCatQQ) + FastAPI + SQLite 的 QQ 消息防撤回工具，提供本地 Web 页面查看撤回内容。

---

## 功能

- 实时捕获群聊 + 私聊消息，缓存在内存中（默认 2 分钟）
- 检测到撤回事件后立即保存，页面 3 秒内自动刷新
- 消息到达时自动下载图片 / 视频 / 语音到本地
- Web 页面按群/好友分类查看，支持未读红点与详情弹窗

---

## 环境要求

- Python 3.10+
- [NapCat](https://github.com/NapNeko/NapCatQQ) 已安装并登录 QQ

> NapCat 是本工具的数据来源，必须保持运行。

---

## 安装

```bash
git clone https://github.com/zChise/qq-recall-watcher.git
cd qq-recall-watcher
pip install -r requirements.txt
```

---

## 配置

复制模板并编辑：

```bash
cp config.example.json config.json
```

`config.json` 示例：

```json
{
  "napcat_ws": "ws://127.0.0.1:3001",
  "token": "你的NapCat访问令牌",
  "web_port": 8080,
  "buffer_minutes": 2,
  "monitored": "all"
}
```

字段说明：

- `napcat_ws`：NapCat WebSocket 地址
- `token`：NapCat 后台的 WebSocket token
- `web_port`：本地网页端口（默认 `8080`）
- `buffer_minutes`：消息缓存窗口（分钟）
- `monitored`：`"all"` 或指定群号/QQ号数组，例如 `[123456789, 987654321]`

---

## 启动

在项目目录执行：

```bash
python main.py
```

看到以下日志代表启动成功：

```text
[ok] Web UI -> http://127.0.0.1:8080
[ws] connecting -> ws://127.0.0.1:3001
[ws] connected
```

浏览器访问：`http://127.0.0.1:8080`

---

## Windows 一次性跑通（推荐）

如果你在 Windows 上遇到依赖或编码问题，按下面流程可稳定启动。

1. 进入项目目录

```powershell
cd C:\Users\你的用户名\...\qq-recall-watcher
```

2. 确认你用的是 Windows Python（不是 `C:\msys64\...`）

```powershell
py -0p
```

3. 创建并激活虚拟环境

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\activate
```

4. 安装依赖

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

5. 启动

```powershell
python main.py
```

以后每次启动只需：

```powershell
cd C:\Users\你的用户名\...\qq-recall-watcher
.\.venv\Scripts\activate
python main.py
```

---

## 从零迁移到新电脑（完整步骤）

目标：新电脑安装后，保留旧电脑的历史撤回记录和媒体文件。

1. 新电脑安装 Python 3.10+ 与 NapCat，并登录 QQ
2. 克隆项目并安装依赖

```bash
git clone https://github.com/zChise/qq-recall-watcher.git
cd qq-recall-watcher
pip install -r requirements.txt
```

3. 从旧电脑复制以下内容到新电脑同名项目目录
- `data/recalled.db`
- `data/media/`
- `config.json`（可选，但推荐）

4. 在新电脑 NapCat 后台获取新的 token
- 打开 NapCat WebUI -> 网络配置 -> WebSocket 服务
- 复制 token，写入新电脑的 `config.json`

5. 确认 `config.json` 的关键项
- `napcat_ws` 通常为 `ws://127.0.0.1:3001`
- `token` 为新电脑 NapCat 的 token
- `web_port` 默认 `8080`（占用可改 `8081`）

6. 启动并验证

```bash
python main.py
```

验证点：
- 页面能打开
- 控制台出现 `[ws] connected`
- 历史记录与媒体能正常显示

注意：`config.json` 与 `data/` 被 `.gitignore` 忽略，不会随 Git 自动同步，必须手动拷贝。

---

## 常见问题（轻松版）

### 1) `No module named uvicorn`
依赖未装到当前环境。

```powershell
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
```

### 2) `No module named pip` / PEP 668 / `--break-system-packages`
通常是用了 MSYS2 Python（`C:\msys64\...`）。

解决：改用 `py -3.12` 创建 venv（见上文 Windows 流程）。

### 3) `json.decoder.JSONDecodeError: Unexpected UTF-8 BOM`
`config.json` 含 BOM，但程序按纯 `utf-8` 读取。

解决：
- 把 `config.json` 另存为 UTF-8（无 BOM）
- 或程序读取使用 `utf-8-sig`

### 4) `WinError 10048` 端口占用
`web_port` 被占用。

- 直接把 `config.json` 的 `web_port` 改为 `8081` 再启动
- 或先释放占用端口再启动

### 5) `taskkill /PID <上面查到的PID> /F` 报错
`< >` 是占位符，不能原样输入。必须换成真实数字：

```powershell
taskkill /PID 12345 /F
```

### 6) `[ws] disconnected`
- 检查 NapCat 是否在线并已登录
- 检查 `napcat_ws` 和 `token` 是否与 NapCat 后台一致
- 检查 NapCat WebSocket 服务端口是否可访问

---

## 目录结构

```text
qq-recall-watcher/
├── config.example.json
├── config.json
├── main.py
├── requirements.txt
├── core/
│   ├── buffer.py
│   ├── downloader.py
│   ├── storage.py
│   └── ws_client.py
├── web/
│   ├── server.py
│   └── static/
└── data/
    ├── recalled.db
    └── media/
```

---

## Windows 已知问题说明

原版使用 SSE（Server-Sent Events）推送撤回通知。在 Windows 上，asyncio 的 ProactorEventLoop 可能导致 SSE 长连接被重置（`ERR_CONNECTION_RESET`）。

当前方案：前端使用 3 秒轮询替代 SSE，并抑制 `WinError 64` 噪声日志，无需额外依赖。

---

## 免责声明

本工具仅供个人学习和研究使用。请勿用于侵犯他人隐私，使用前请确保符合当地法律法规及平台服务条款。