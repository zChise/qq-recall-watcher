 猫萌 · QQ 防撤回工具（轮椅无脑手把手版）最简单好用的 QQ 消息防撤回工具
基于 NapCat + FastAPI + SQLite，本地网页查看撤回内容，图片视频语音自动保存。核心功能实时捕获群聊和私聊消息
有人撤回 → 立刻保存，网页 3 秒自动刷新
图片、视频、语音自动下载到本地
网页按群/好友分类显示，支持未读红点和详情弹窗

准备工作（必须先做好）NapCat 已安装并成功登录你的 QQ（保持 NapCat 一直运行）
Python 3.12（推荐）已安装（Windows 官方版）

第一步：获取项目打开命令提示符（按 Win + R，输入 cmd 回车），依次执行以下命令：cmd
指令长

git clone https://github.com/zChise/qq-recall-watcher.git
cd qq-recall-watcher

或者直接从 GitHub 下载压缩包解压也行，解压后的文件夹名叫 qq-recall-watcher。第二步：创建虚拟环境（只做一次）在命令提示符中继续输入下面命令（必须在项目文件夹里）：cmd
指令长

py -3.12 -m venv .venv

第三步：安装依赖继续在命令提示符中输入：cmd
指令长

.\.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

第四步：配置 config.json（最重要的一步）在项目文件夹里找到 config.example.json
复制一份，并把复制的文件重命名为 config.json
用记事本或 VS Code 打开 config.json，把内容全部替换成下面这段（直接复制粘贴）：

json

{
  "napcat_ws": "ws://127.0.0.1:3001",
  "token": "在这里粘贴你的NapCat Token",
  "web_port": 8080,
  "buffer_minutes": 2,
  "monitored": "all"
}

只修改这一行：把 "token": "在这里粘贴你的NapCat Token",
改成你的真实 Token，例如：json

"token": "abc123def456ghi789",

完整示例（仅供参考，token 要换成你自己的）：json

{
  "napcat_ws": "ws://127.0.0.1:3001",
  "token": "你的真实Token粘贴在这里",
  "web_port": 8080,
  "buffer_minutes": 2,
  "monitored": "all"
}

如何获取 Token？打开 NapCat WebUI（通常是浏览器访问 http://127.0.0.1:6099）
左侧菜单找到 网络配置 → WebSocket 服务
找到 Token 一栏，复制里面的内容

第五步：创建一键启动文件（强烈推荐）在项目文件夹里新建一个文本文件，命名为 一键启动.bat，内容如下：bat
蝙蝠

@echo off
chcp 65001 >nul
echo.
echo ========================================
echo     猫萌 QQ 防撤回工具 - 启动中...
echo ========================================
echo.
call .venv\Scripts\activate
python main.py
pause

保存后，以后每次启动只需双击这个 一键启动.bat 即可。第六步：启动工具双击 一键启动.bat，看到以下内容就代表成功：

[ok] Web UI -> http://127.0.0.1:8080
[ws] connecting -> ws://127.0.0.1:3001
[ws] connected

然后用浏览器打开：http://127.0.0.1:8080从旧电脑迁移到新电脑（完整保留历史记录）新电脑安装 Python 和 NapCat，并登录同一个 QQ。
把整个 qq-recall-watcher 文件夹复制到新电脑（或重新 clone）。
从旧电脑复制以下内容覆盖到新电脑相同位置：data/recalled.db 文件
data/media/ 文件夹
config.json 文件

更新 Token（必须做！）：在新电脑 NapCat WebUI 里重新获取 Token
把新 Token 填入 config.json

双击 一键启动.bat 启动
浏览器打开网页，检查历史记录和媒体是否正常显示

常见问题解决No module named pip / PEP 668
没有名为 pip / PEP 668 的模块
→ 你用了 MSYS2 Python。解决办法：用 py -3.12 -m venv .venv 创建虚拟环境。
No module named uvicorn
没有名为 Uvicorn 的模块
→ 没有激活环境。先双击 一键启动.bat，或在 cmd 中先执行 .\.venv\Scripts\activate
config.json 报 JSON 错误
→ 用记事本另存为 UTF-8（无 BOM），或用 VS Code 保存。
网页打不开 / 端口占用
→ 把 config.json 中的 "web_port": 8080 改成 8081，然后重启。
[ws] disconnected
[WS] 已断线
→ 检查 NapCat 是否正在运行、是否已登录 QQ、Token 是否正确。

项目重要目录config.json —— 配置文件（必须手动配置）
data/recalled.db —— 所有撤回记录
data/media/ —— 自动下载的图片、视频、语音
一键启动.bat —— 以后启动用的

注意：data/ 文件夹和 config.json 不会被 git 自动同步，换电脑时必须手动复制。免责声明
本工具仅供个人学习和研究使用。请勿用于侵犯他人隐私，使用前请确保符合当地法律法规及 QQ 服务条款。

