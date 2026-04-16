# 猫萌 · QQ 防撤回工具

基于 [NapCat](https://github.com/NapNeko/NapCatQQ) + FastAPI + SQLite 实现的 QQ 消息防撤回工具，提供本地 Web 界面查看撤回内容。

---

## 功能

- 实时捕获群聊 + 私聊消息，缓存在内存中（默认 2 分钟窗口）
- 检测到撤回事件后立即保存，推送 SSE 通知刷新页面
- 消息到达时自动下载图片 / 视频 / 语音到本地
- Web 界面（猫萌风格）
  - 左侧按群 / 好友分类，显示未读红点
  - 消息卡片未读时左侧红线标注，点击后标记已读
  - 详情弹窗渲染文字 / 图片 / 视频 / 语音，视频附下载链接
  - SSE 实时推送，标签页标题显示未读数

---

## 环境要求

- Python 3.10+
- [NapCat](https://github.com/NapNeko/NapCatQQ) 已安装并登录 QQ 账号

> NapCat 是本工具的消息来源，**必须保持运行状态**，工具才能捕获消息。

---

## 安装

**1. 克隆仓库**

```bash
git clone https://github.com/zChise/qq-recall-watcher.git
cd qq-recall-watcher
```

**2. 安装依赖**

```bash
pip install -r requirements.txt
```

---

## 配置

复制模板，创建你自己的配置文件：

```bash
cp config.example.json config.json
```

编辑 `config.json`：

```json
{
  "napcat_ws": "ws://127.0.0.1:3001",
  "token": "你的NapCat访问令牌",
  "web_port": 8080,
  "buffer_minutes": 2,
  "monitored": "all"
}
```

**字段说明：**

- `napcat_ws`：NapCat 的 WebSocket 地址，本机默认不用改
- `token`：在 NapCat 后台 → 网络配置 → WebSocket 服务 中查看
- `web_port`：本地网页端口，默认 8080
- `buffer_minutes`：消息在内存中保留多久（分钟），超过此时间的消息撤回后无法捕获
- `monitored`：`"all"` 监控所有，或指定群号 / QQ 号的数组，例如 `[123456789, 987654321]`

**如何获取 NapCat token：**

打开 NapCat WebUI → 网络配置 → 找到 WebSocket 服务那一栏 → 复制 token 填入配置文件。

---

## 启动

**必须在项目目录下执行：**

```bash
cd qq-recall-watcher
python main.py
```

看到以下输出说明启动成功：

```
[ws] connecting → ws://127.0.0.1:3001
[ws] connected
[✓] Web UI → http://127.0.0.1:8080
```

浏览器打开 `http://127.0.0.1:8080` 即可使用。

---

## 目录结构

```
qq-recall-watcher/
├── config.example.json   ← 配置模板（复制为 config.json 后填写）
├── config.json           ← 你的配置（已被 .gitignore 忽略）
├── main.py               ← 入口
├── requirements.txt
├── core/
│   ├── buffer.py         ← 内存缓冲（TTL 窗口）
│   ├── downloader.py     ← 异步媒体下载
│   ├── storage.py        ← SQLite 读写
│   └── ws_client.py      ← NapCat WebSocket 连接
├── web/
│   ├── server.py         ← FastAPI 路由 + SSE
│   └── static/           ← 前端页面
└── data/                 ← 运行时生成（已被 .gitignore 忽略）
    ├── recalled.db       ← 撤回记录数据库
    └── media/            ← 下载的媒体文件
```

---

## 常见问题

**连接失败 / `[ws] disconnected`**
- 确认 NapCat 正在运行且已登录
- 检查 `napcat_ws` 地址和端口是否正确
- 检查 `token` 是否与 NapCat 后台一致

**捕获不到撤回消息**
- 消息发出到撤回的间隔超过了 `buffer_minutes`，适当调大该值
- NapCat 版本过旧，私聊撤回事件支持存在差异

**语音无法播放**
- QQ 语音为 `.silk` 格式，浏览器不支持原生播放，页面提供下载链接

**换电脑后历史记录丢失**
- `data/` 目录含 `recalled.db` 和 `media/`，整体复制到新机器即可保留历史

---

## 免责声明

本工具仅供个人学习和研究使用。请勿用于侵犯他人隐私，使用前请确保符合当地法律法规及平台服务条款。
