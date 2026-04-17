// ── State ─────────────────────────────────────────────────────────────────────
let _filter = { type: 'all', group_id: null, user_id: null };
let _msgMap  = {};   // msg_id -> message object

// ── API ───────────────────────────────────────────────────────────────────────
async function apiFetch(path) {
    try {
        const r = await fetch(path, { cache: 'no-store' });
        return r.json();
    } catch (e) {
        return [];
    }
}

// ── Load ──────────────────────────────────────────────────────────────────────
async function loadChats() {
    const chats = await apiFetch('/api/chats');
    const list  = document.getElementById('chatList');

    while (list.children.length > 1) list.removeChild(list.lastChild);

    let totalUnread = 0;
    for (const c of chats) {
        const isGroup = c.chat_type === 'group';
        const key     = isGroup ? `g_${c.group_id}` : `u_${c.user_id}`;
        // 群：优先用群名，没有就用群号
        const label   = isGroup
            ? (c.group_name || `群 ${c.group_id}`)
            : c.sender_name;
        const unread  = c.unread || 0;

        const li = document.createElement('li');
        li.className   = 'chat-item';
        li.dataset.key = key;
        li.innerHTML   = `
            <span class="chat-label" title="${escHtml(label)}">${escHtml(label)}</span>
            <span class="chat-count">${unread || ''}</span>
        `;
        if (unread > 0) li.querySelector('.chat-count').style.display = 'inline';

        const gid = c.group_id, uid = c.user_id;
        li.onclick = () => selectChat(li, c.chat_type,
            isGroup ? gid : null,
            isGroup ? null : uid);
        list.appendChild(li);
        totalUnread += unread;
    }

    const allCount    = document.getElementById('allCount');
    const globalBadge = document.getElementById('globalBadge');
    if (totalUnread > 0) {
        allCount.textContent      = totalUnread;
        allCount.style.display    = 'inline';
        globalBadge.textContent   = totalUnread;
        globalBadge.style.display = 'inline';
    } else {
        allCount.style.display    = 'none';
        globalBadge.style.display = 'none';
    }

    // 保持当前选中项高亮
    const curKey = _currentKey();
    document.querySelectorAll('.chat-item').forEach(el => {
        el.classList.toggle('selected', el.dataset.key === curKey);
    });
}

function _currentKey() {
    if (_filter.type === 'all') return 'all';
    if (_filter.group_id != null) return `g_${_filter.group_id}`;
    return `u_${_filter.user_id}`;
}

async function loadMessages() {
    const params = new URLSearchParams();
    if (_filter.group_id != null) params.set('group_id', _filter.group_id);
    else if (_filter.user_id != null) params.set('user_id', _filter.user_id);

    const msgs = await apiFetch('/api/messages?' + params);
    msgs.forEach(m => { _msgMap[m.msg_id] = m; });
    renderMessages(msgs);
}

// ── Render ────────────────────────────────────────────────────────────────────
function getPreview(content) {
    if (!Array.isArray(content)) return '[消息]';
    for (const seg of content) {
        switch (seg.type) {
            case 'text':   return (seg.data?.text || '').slice(0, 80);
            case 'image':  return '[图片]';
            case 'video':  return '[视频]';
            case 'record': return '[语音]';
            case 'at':     return `@${seg.data?.name || seg.data?.qq || '某人'}`;
        }
    }
    return '[消息]';
}

function formatTime(ts) {
    const d   = new Date(ts * 1000);
    const now = new Date();
    if (d.toDateString() === now.toDateString()) {
        return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    }
    const yesterday = new Date(now - 86400000);
    if (d.toDateString() === yesterday.toDateString()) {
        return '昨天 ' + d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    }
    return d.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' }) + ' ' +
           d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
}

function renderMessages(msgs) {
    const container = document.getElementById('msgContainer');
    if (!msgs.length) {
        container.innerHTML = '<div class="placeholder">暂无撤回消息</div>';
        return;
    }
    container.innerHTML = msgs.map(m => {
        const chatLabel = m.chat_type === 'group'
            ? (m.group_name || `群聊 ${m.group_id}`)
            : '私聊';
        const preview = getPreview(m.content);
        const dot     = m.is_read ? '' : '<div class="unread-indicator"></div>';
        return `
        <div class="msg-card ${m.is_read ? '' : 'unread'}"
             data-msgid="${m.msg_id}"
             onclick="openDetail(${m.msg_id})">
            ${dot}
            <div class="msg-card-top">
                <div>
                    <div class="msg-sender">${escHtml(m.sender_name)}</div>
                    <div class="msg-chat">${escHtml(chatLabel)}</div>
                </div>
                <div class="msg-time">${formatTime(m.recalled_at)}</div>
            </div>
            <div class="msg-preview">${escHtml(preview)}</div>
        </div>`;
    }).join('');
}

function renderContent(content) {
    if (!Array.isArray(content)) return '<span class="seg-muted">[空消息]</span>';
    return content.map(seg => {
        const d = seg.data || {};
        switch (seg.type) {
            case 'text':
                return `<span>${escHtml(d.text || '')}</span>`;
            case 'image': {
                const src = d.local_file ? `/api/media/${d.local_file}` : (d.url || '');
                return src
                    ? `<img src="${src}" loading="lazy" alt="图片" onerror="this.outerHTML='<span class=seg-muted>[图片加载失败]</span>'">`
                    : '<span class="seg-muted">[图片]</span>';
            }
            case 'video': {
                const src = d.local_file ? `/api/media/${d.local_file}` : (d.url || '');
                if (!src) return '<span class="seg-muted">[视频]</span>';
                const dlName = d.local_file || '视频.mp4';
                return `<div class="video-wrap">
                    <video src="${src}" controls preload="metadata"></video>
                    <a class="media-dl" href="${src}" download="${dlName}">↓ 下载视频文件</a>
                </div>`;
            }
            case 'record':
            case 'audio': {
                if (!d.local_file && !d.url) return '<span class="seg-muted">[语音]</span>';
                const src = d.local_file ? `/api/media/${d.local_file}` : d.url;
                const dlName = d.local_file || '语音文件';
                // 同时提供 audio 播放 + 下载链接（silk 格式浏览器播不了时可下载）
                return `<div class="audio-wrap">
                    <audio src="${src}" controls></audio>
                    <a class="media-dl" href="${src}" download="${dlName}">↓ 下载语音文件</a>
                </div>`;
            }
            case 'at':
                return `<span class="seg-at">@${escHtml(d.name || d.qq || '某人')}</span>`;
            case 'face':
                return `<span class="seg-muted">[表情]</span>`;
            case 'forward':
                return `<span class="seg-muted">[合并转发消息]</span>`;
            default:
                return `<span class="seg-muted">[${escHtml(seg.type || '未知')}]</span>`;
        }
    }).join('');
}

function escHtml(s) {
    return String(s ?? '')
        .replace(/&/g, '&amp;').replace(/</g, '&lt;')
        .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// ── Interaction ───────────────────────────────────────────────────────────────
function selectChat(el, type, group_id, user_id) {
    document.querySelectorAll('.chat-item').forEach(i => i.classList.remove('selected'));
    if (el) el.classList.add('selected');
    _filter = { type, group_id: group_id ?? null, user_id: user_id ?? null };
    sessionStorage.setItem('filter', JSON.stringify(_filter));

    // 点进具体群/好友时，全部标已读（和 QQ 一样）
    if (type !== 'all') {
        const params = new URLSearchParams();
        if (group_id != null) params.set('group_id', group_id);
        else if (user_id != null) params.set('user_id', user_id);
        fetch('/api/read-all?' + params, { method: 'POST' }).then(() => loadChats());
    }

    loadMessages();
}

async function openDetail(msgId) {
    const m = _msgMap[msgId];
    if (!m) return;

    const chatLabel = m.chat_type === 'group'
        ? ` · ${m.group_name || '群聊 ' + m.group_id}`
        : ' · 私聊';
    document.getElementById('modalSender').textContent = m.sender_name + chatLabel;
    document.getElementById('modalTime').textContent   = formatTime(m.recalled_at) + ' 撤回';
    document.getElementById('modalBody').innerHTML     = renderContent(m.content);

    const modal = document.getElementById('modal');
    const bg = document.getElementById('modalBg');
    bg.style.display = 'block';
    modal.style.display = 'flex';
    requestAnimationFrame(() => { modal.classList.add('open'); bg.classList.add('open'); });

    if (!m.is_read) {
        m.is_read = 1;
        fetch(`/api/read/${msgId}`, { method: 'POST' });

        // 平滑消除红边和红点，不整体刷新
        const card = document.querySelector(`.msg-card[data-msgid="${msgId}"]`);
        if (card) {
            const dot = card.querySelector('.unread-indicator');
            if (dot) {
                dot.style.opacity = '0';
                setTimeout(() => dot.remove(), 500);
            }
            card.classList.remove('unread');
        }
        // 只刷新侧边栏数字
        loadChats();
    }
}

function closeDetail() {
    const modal = document.getElementById('modal');
    const bg    = document.getElementById('modalBg');
    modal.classList.remove('open');
    bg.classList.remove('open');
    setTimeout(() => { modal.style.display = 'none'; bg.style.display = 'none'; }, 220);
}

document.addEventListener('keydown', e => { if (e.key === 'Escape') closeDetail(); });

// ── 轮询（替代不稳定的SSE）────────────────────────────────────────────────────
function startPolling() {
    setInterval(async () => {
        await loadChats();
        await loadMessages();
        const unread = document.getElementById('allCount').textContent;
        document.title = unread ? `(${unread}) 猫萌` : '猫萌';
    }, 3000);
}

// ── Init ──────────────────────────────────────────────────────────────────────
(async () => {
    const saved = sessionStorage.getItem('filter');
    if (saved) {
        try { _filter = JSON.parse(saved); } catch (_) {}
    }
    await loadChats();
    await loadMessages();
    startPolling();
})();
