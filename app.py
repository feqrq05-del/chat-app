import os
import sqlite3
import random
import time
from datetime import datetime
from flask import Flask, request, redirect, url_for, session, render_template_string, send_from_directory
from flask_socketio import SocketIO, emit
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'higori-platform-vip-super-secret-2026'

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

socketio = SocketIO(app, cors_allowed_origins="*")

def get_db():
    conn = sqlite3.connect('higori_data.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id_code TEXT UNIQUE,
                name TEXT NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                avatar TEXT DEFAULT '',
                cover TEXT DEFAULT '',
                bio TEXT DEFAULT 'أهلاً بكم في منصة Higori Platform VIP',
                visits INTEGER DEFAULT 0,
                joined_date TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS stories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                user_name TEXT,
                user_avatar TEXT,
                content_text TEXT,
                media_path TEXT,
                privacy TEXT DEFAULT 'public',
                created_at TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER,
                sender_name TEXT,
                receiver_id INTEGER,
                group_id INTEGER DEFAULT 0,
                content TEXT,
                view_once INTEGER DEFAULT 0,
                created_at TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS friendships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_a INTEGER,
                user_b INTEGER,
                status TEXT DEFAULT 'pending',
                created_at TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                group_code TEXT UNIQUE,
                owner_id INTEGER,
                cover TEXT DEFAULT '',
                created_at TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS group_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER,
                user_id INTEGER,
                role TEXT DEFAULT 'member'
            )
        ''')
        conn.commit()

init_db()

AUTH_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Higori Platform - VIP Access</title>
    <style>
        :root {
            --bg-color: #070d12;
            --card-bg: rgba(13, 22, 31, 0.95);
            --neon-green: #00ff88;
            --neon-glow: 0 0 20px rgba(0, 255, 136, 0.45);
            --border-glow: 1px solid rgba(0, 255, 136, 0.25);
            --text-muted: #8ba2b5;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: system-ui, sans-serif; }
        body {
            background: radial-gradient(circle at top, #0f271d 0%, #070d12 75%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
            color: #ffffff;
        }
        .vip-box {
            width: 100%;
            max-width: 420px;
            background: var(--card-bg);
            border: var(--border-glow);
            border-radius: 24px;
            padding: 35px 25px;
            backdrop-filter: blur(12px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.8), var(--neon-glow);
            text-align: center;
        }
        .vip-pill {
            display: inline-block;
            background: rgba(0, 255, 136, 0.1);
            color: var(--neon-green);
            padding: 4px 16px;
            border-radius: 30px;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 2px;
            border: 1px solid var(--neon-green);
            margin-bottom: 12px;
        }
        .title { font-size: 26px; font-weight: 900; letter-spacing: 1px; margin-bottom: 5px; }
        .title span { color: var(--neon-green); text-shadow: var(--neon-glow); }
        .subtitle { font-size: 13px; color: var(--text-muted); margin-bottom: 25px; }
        .form-group { margin-bottom: 15px; text-align: right; }
        .form-group label { display: block; font-size: 12px; color: var(--text-muted); margin-bottom: 6px; }
        .inp {
            width: 100%;
            padding: 14px 16px;
            background: rgba(9, 15, 22, 0.9);
            border: 1px solid #1a2936;
            border-radius: 12px;
            color: #fff;
            font-size: 14px;
            outline: none;
        }
        .inp:focus { border-color: var(--neon-green); box-shadow: 0 0 10px rgba(0,255,136,0.3); }
        .btn-vip {
            width: 100%;
            padding: 14px;
            margin-top: 10px;
            background: linear-gradient(135deg, #00ff88, #00bd67);
            border: none;
            border-radius: 12px;
            color: #070d12;
            font-size: 15px;
            font-weight: 800;
            cursor: pointer;
            box-shadow: var(--neon-glow);
        }
        .error-badge {
            background: rgba(255, 75, 75, 0.15);
            border: 1px solid #ff4b4b;
            color: #ff6b6b;
            padding: 10px;
            border-radius: 8px;
            font-size: 12px;
            margin-bottom: 15px;
        }
        .toggle-link { margin-top: 22px; font-size: 13px; color: var(--text-muted); }
        .toggle-link a { color: var(--neon-green); text-decoration: none; font-weight: bold; }
    </style>
</head>
<body>
<div class="vip-box">
    <div class="vip-pill">VIP PLATFORM</div>
    <div class="title">Higori <span>platform</span></div>
    {% if mode == 'register' %}
        <div class="subtitle">إنشاء حساب مستخدم مميز جديد</div>
        {% if error %}<div class="error-badge">{{ error }}</div>{% endif %}
        <form method="POST">
            <div class="form-group"><label>الاسم الظاهر</label><input class="inp" name="name" placeholder="اسمك الظاهر" required></div>
            <div class="form-group"><label>اسم المستخدم (Username بالإنجليزية)</label><input class="inp" name="username" placeholder="مثال: osama_vip" required></div>
            <div class="form-group"><label>كلمة المرور</label><input class="inp" type="password" name="password" placeholder="••••••••" required></div>
            <button class="btn-vip" type="submit">إنشاء الحساب</button>
        </form>
        <div class="toggle-link">لديك حساب بالفعل؟ <a href="/login">تسجيل الدخول</a></div>
    {% else %}
        <div class="subtitle">بوابة الدخول للنظام</div>
        {% if error %}<div class="error-badge">{{ error }}</div>{% endif %}
        <form method="POST">
            <div class="form-group"><label>اسم المستخدم</label><input class="inp" name="username" placeholder="Username" required></div>
            <div class="form-group"><label>كلمة المرور</label><input class="inp" type="password" name="password" placeholder="••••••••" required></div>
            <button class="btn-vip" type="submit">دخول المنصة</button>
        </form>
        <div class="toggle-link">مستخدم جديد؟ <a href="/register">إنشاء حساب VIP</a></div>
    {% endif %}
</div>
</body>
</html>
"""

MAIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Higori platform</title>
    <script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
    <style>
        :root {
            --bg-color: #060b10;
            --card-bg: #0d1620;
            --card-inner: #13212f;
            --border-color: #192b3a;
            --neon-green: #00ff88;
            --neon-glow: 0 0 14px rgba(0, 255, 136, 0.45);
            --text-main: #ffffff;
            --text-muted: #8ba2b5;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: system-ui, -apple-system, sans-serif; }
        body {
            background-color: var(--bg-color);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: flex-start;
            padding: 12px 8px;
        }
        .phone-wrapper {
            width: 100%;
            max-width: 440px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            position: relative;
        }
        .header-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 4px 6px;
        }
        .theme-pill {
            background: #142230;
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 6px 12px;
            font-size: 14px;
            cursor: pointer;
        }
        .brand-title {
            font-size: 24px;
            font-weight: 900;
            letter-spacing: 1.5px;
            color: var(--neon-green);
            text-shadow: var(--neon-glow);
            text-align: center;
            flex: 1;
        }
        .btn-settings-top {
            width: 100%;
            background: linear-gradient(180deg, #00c76d, #008f4c);
            color: white;
            border: none;
            padding: 13px;
            border-radius: 14px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            box-shadow: var(--neon-glow);
        }
        .nav-bar {
            display: flex;
            justify-content: space-between;
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 18px;
            padding: 10px 6px;
        }
        .nav-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 5px;
            cursor: pointer;
            color: var(--text-muted);
            font-size: 11px;
            flex: 1;
            transition: 0.2s;
        }
        .nav-item.active {
            color: var(--neon-green);
            font-weight: bold;
        }
        .nav-item .icon { font-size: 20px; }
        .nav-item.active .icon { filter: drop-shadow(0 0 6px var(--neon-green)); }
        .tab-panel {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 18px;
            padding: 16px;
            min-height: 480px;
            display: none;
            flex-direction: column;
        }
        .tab-panel.active { display: flex; }
        .status-tray {
            display: flex;
            gap: 14px;
            overflow-x: auto;
            padding-bottom: 8px;
            margin-top: 10px;
        }
        .status-tray::-webkit-scrollbar { display: none; }
        .story-bubble {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 6px;
            cursor: pointer;
            min-width: 70px;
        }
        .story-ring {
            width: 66px;
            height: 66px;
            border-radius: 50%;
            border: 2px solid var(--neon-green);
            box-shadow: 0 0 8px rgba(0,255,136,0.3);
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden;
            background: #111d28;
            font-weight: bold;
            font-size: 20px;
        }
        .story-ring.dashed { border-style: dashed; }
        .story-ring img { width: 100%; height: 100%; object-fit: cover; }
        .story-label { font-size: 11px; color: var(--text-muted); max-width: 65px; text-overflow: ellipsis; overflow: hidden; white-space: nowrap; text-align: center; }
        .chat-sub-nav {
            display: flex;
            gap: 8px;
            margin-bottom: 12px;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 10px;
        }
        .sub-pill {
            background: var(--card-inner);
            border: 1px solid var(--border-color);
            color: var(--text-muted);
            padding: 6px 14px;
            border-radius: 10px;
            font-size: 12px;
            cursor: pointer;
        }
        .sub-pill.active {
            background: rgba(0, 255, 136, 0.15);
            border-color: var(--neon-green);
            color: var(--neon-green);
            font-weight: bold;
        }
        #chat-stream {
            flex: 1;
            height: 330px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 10px;
            padding: 6px 0;
        }
        .bubble-row { display: flex; width: 100%; }
        .bubble-row.mine { justify-content: flex-start; }
        .bubble-row.theirs { justify-content: flex-end; }
        .bubble-msg {
            background: #0d3826;
            border-right: 3px solid var(--neon-green);
            padding: 10px 14px;
            border-radius: 12px;
            max-width: 85%;
            word-wrap: break-word;
            font-size: 13px;
        }
        .bubble-msg.other {
            background: var(--card-inner);
            border-right: none;
            border-left: 3px solid #38607f;
        }
        .bubble-header { display: flex; justify-content: space-between; gap: 10px; font-size: 11px; color: var(--neon-green); font-weight: bold; margin-bottom: 4px; }
        .bubble-time { font-size: 10px; color: var(--text-muted); text-align: left; margin-top: 4px; }
        .chat-input-bar {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 10px;
        }
        .chat-input-bar input {
            flex: 1;
            background: var(--card-inner);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 12px 14px;
            color: #fff;
            outline: none;
            font-size: 13px;
        }
        .btn-send {
            background: var(--neon-green);
            color: #060b10;
            border: none;
            padding: 12px 18px;
            border-radius: 12px;
            font-weight: bold;
            font-size: 14px;
            cursor: pointer;
        }
        .item-card {
            background: var(--card-inner);
            border: 1px solid var(--border-color);
            border-radius: 14px;
            padding: 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 8px;
        }
        .item-avatar {
            width: 44px;
            height: 44px;
            border-radius: 50%;
            background: #192b3a;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden;
            font-weight: bold;
            font-size: 14px;
        }
        .item-avatar img { width: 100%; height: 100%; object-fit: cover; }
        .item-details { flex: 1; margin-right: 12px; }
        .item-name { font-weight: bold; font-size: 14px; display: flex; align-items: center; gap: 4px; }
        .item-sub { font-size: 11px; color: var(--text-muted); margin-top: 3px; }
        .action-btns { display: flex; gap: 6px; }
        .btn-small {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            color: #fff;
            padding: 6px 12px;
            border-radius: 8px;
            font-size: 12px;
            cursor: pointer;
            font-weight: bold;
        }
        .btn-small.green { background: var(--neon-green); color: #000; border: none; }
        .btn-small.danger { background: rgba(255, 75, 75, 0.2); border-color: #ff4b4b; color: #ff6b6b; }
        .profile-cover {
            width: 100%;
            height: 140px;
            background: #162432;
            border-radius: 14px;
            position: relative;
            margin-bottom: 45px;
            overflow: hidden;
        }
        .profile-cover img { width: 100%; height: 100%; object-fit: cover; }
        .profile-avatar-circle {
            width: 78px;
            height: 78px;
            border-radius: 50%;
            border: 3px solid var(--card-bg);
            background: #1c3042;
            position: absolute;
            bottom: -35px;
            right: 18px;
            overflow: hidden;
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 28px;
        }
        .profile-avatar-circle img { width: 100%; height: 100%; object-fit: cover; }
        .online-dot {
            width: 14px;
            height: 14px;
            background: var(--neon-green);
            border-radius: 50%;
            position: absolute;
            bottom: 2px;
            left: 2px;
            border: 2px solid var(--card-bg);
        }
        .id-badge-card {
            background: var(--card-inner);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 12px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-top: 14px;
            font-size: 12px;
        }
        .badge-row { display: flex; justify-content: space-between; align-items: center; }
        .btn-copy {
            background: #203548;
            border: none;
            color: #fff;
            padding: 3px 10px;
            border-radius: 6px;
            font-size: 11px;
            cursor: pointer;
        }
        .stats-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 14px;
        }
        .stat-card {
            background: var(--card-inner);
            border: 1px solid var(--border-color);
            padding: 12px;
            border-radius: 12px;
            text-align: center;
        }
        .stat-val { font-size: 22px; font-weight: 900; color: var(--neon-green); }
        .stat-lbl { font-size: 11px; color: var(--text-muted); margin-top: 2px; }
        .modal-overlay {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.85);
            backdrop-filter: blur(8px);
            display: none;
            justify-content: center;
            align-items: center;
            padding: 15px;
            z-index: 1000;
        }
        .modal-overlay.active { display: flex; }
        .modal-content {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            width: 100%;
            max-width: 400px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.8);
            position: relative;
        }
        .btn-close-modal {
            position: absolute;
            top: 15px;
            left: 15px;
            background: #1e3345;
            color: #fff;
            border: none;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            font-size: 16px;
            cursor: pointer;
        }
        #toast {
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            background: #0d281c;
            border: 1px solid var(--neon-green);
            color: #fff;
            padding: 8px 18px;
            border-radius: 20px;
            font-size: 12px;
            display: none;
            z-index: 2000;
            box-shadow: var(--neon-glow);
        }
    </style>
</head>
<body>

<div class="phone-wrapper">
    <div class="header-top">
        <div class="theme-pill" onclick="toggleTheme()">🌙</div>
        <div class="brand-title">Higori platform</div>
    </div>

    <button class="btn-settings-top" onclick="openModal('settings-modal')">الإعدادات</button>

    <div class="nav-bar">
        <div class="nav-item active" id="btn-status" onclick="switchTab('status')">
            <span class="icon">⛺</span><span>الحالات</span>
        </div>
        <div class="nav-item" id="btn-chats" onclick="switchTab('chats')">
            <span class="icon">💬</span><span>الدردشات</span>
        </div>
        <div class="nav-item" id="btn-groups" onclick="switchTab('groups')">
            <span class="icon">🎯</span><span>مجموعات</span>
        </div>
        <div class="nav-item" id="btn-people" onclick="switchTab('people')">
            <span class="icon">👥</span><span>أشخاص</span>
        </div>
        <div class="nav-item" id="btn-profile" onclick="switchTab('profile')">
            <span class="icon">👤</span><span>بروفايلي</span>
        </div>
    </div>

    <div class="tab-panel active" id="tab-status">
        <div style="font-weight: bold; font-size: 14px;">الحالات (24 ساعة)</div>
        <div class="status-tray">
            <div class="story-bubble" onclick="openModal('add-story-modal')">
                <div class="story-ring dashed">+</div>
                <div class="story-label">أضف</div>
            </div>
            {% for s in stories %}
                <div class="story-bubble" onclick="viewStory('{{ s.user_name }}', '{{ s.created_at }}', '{{ s.content_text }}', '{{ s.media_path }}')">
                    <div class="story-ring">
                        {% if s.media_path %}
                            <img src="/uploads/{{ s.media_path }}">
                        {% elif s.user_avatar %}
                            <img src="/uploads/{{ s.user_avatar }}">
                        {% else %}
                            {{ s.user_name[:2] }}
                        {% endif %}
                    </div>
                    <div class="story-label">{{ s.user_name }}</div>
                </div>
            {% endfor %}
        </div>
        {% if not stories %}
            <div style="text-align: center; color: var(--text-muted); margin-top: 100px; font-size: 13px;">لا توجد حالات حالياً. كن أول من ينشر حالة!</div>
        {% endif %}
    </div>

    <div class="tab-panel" id="tab-chats">
        <div class="chat-sub-nav">
            <div class="sub-pill active">الدردشة العامة</div>
            <div class="sub-pill" onclick="showToast('ميزة الرسائل المجهولة مفعلة')">الرسائل المجهولة</div>
        </div>

        <div id="chat-stream">
            {% for m in messages %}
                <div class="bubble-row {% if m.sender_id == current_user.id %}mine{% else %}theirs{% endif %}">
                    <div class="bubble-msg {% if m.sender_id != current_user.id %}other{% endif %}">
                        <div class="bubble-header">
                            <span>{{ m.sender_name }}</span>
                            {% if m.view_once %}<span style="color:#ffbb00;">عرض مرة واحدة</span>{% endif %}
                        </div>
                        <div>{{ m.content }}</div>
                        <div class="bubble-time">{{ m.created_at }} ✔</div>
                    </div>
                </div>
            {% endfor %}
        </div>

        <div style="display: flex; gap: 4px; margin-top: 6px; font-size: 10px; color: var(--text-muted); align-items: center;">
            <span>⏱ اختفاء: مغلق</span>
            <label style="margin-right: auto; display: flex; align-items: center; gap: 4px;">
                <input type="checkbox" id="chk-view-once"> عرض مرة واحدة
            </label>
        </div>

        <div class="chat-input-bar">
            <input type="text" id="chat-txt" placeholder="اكتب رسالة..." autocomplete="off">
            <button class="btn-send" onclick="sendChatMessage()">إرسال</button>
        </div>
    </div>

    <div class="tab-panel" id="tab-groups">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <div style="font-weight: bold; font-size: 15px;">مجموعاتي</div>
            <button class="btn-small green" onclick="openModal('create-group-modal')">إنشاء</button>
        </div>

        <div style="display: flex; flex-direction: column; gap: 8px;">
            {% for g in my_groups %}
                <div class="item-card">
                    <div class="item-avatar">🎯</div>
                    <div class="item-details">
                        <div class="item-name">{{ g.name }}</div>
                        <div class="item-sub">ID: {{ g.group_code }} | المالك: {{ g.owner_name }}</div>
                    </div>
                    <button class="btn-small" onclick="showToast('تم فتح روم المجموعة')">عرض</button>
                </div>
            {% endfor %}
            {% if not my_groups %}
                <div style="text-align: center; color: var(--text-muted); margin-top: 50px; font-size: 13px;">لا تنتمي إلى أي مجموعة بعد. أنشئ مجموعتك الخاصة الآن!</div>
            {% endif %}
        </div>
    </div>

    <div class="tab-panel" id="tab-people">
        <div style="font-weight: bold; font-size: 15px; margin-bottom: 10px;">اكتشف الأعضاء ({{ all_users|length }})</div>
        
        <form method="GET" action="/" style="display: flex; gap: 6px; margin-bottom: 15px;">
            <input name="q" placeholder="ابحث بالاسم أو اليوزر أو ID" value="{{ search_query }}" style="flex:1; background: var(--card-inner); border: 1px solid var(--border-color); border-radius: 10px; padding: 10px; color: #fff; font-size: 12px;">
            <button class="btn-small green" type="submit">بحث</button>
        </form>

        {% if pending_requests %}
            <div style="font-size: 12px; color: var(--neon-green); font-weight: bold; margin-bottom: 8px;">طلبات صداقة واردة:</div>
            {% for req in pending_requests %}
                <div class="item-card">
                    <div class="item-avatar">{{ req.name[:2] }}</div>
                    <div class="item-details">
                        <div class="item-name">{{ req.name }}</div>
                        <div class="item-sub">ID: {{ req.user_id_code }}</div>
                    </div>
                    <div class="action-btns">
                        <a href="/accept_friend/{{ req.id }}" class="btn-small green" style="text-decoration:none;">قبول</a>
                        <a href="/reject_friend/{{ req.id }}" class="btn-small danger" style="text-decoration:none;">رفض</a>
                    </div>
                </div>
            {% endfor %}
        {% endif %}

        <div style="display: flex; flex-direction: column; gap: 8px; margin-top: 10px;">
            {% for u in all_users %}
                {% if u.id != current_user.id %}
                    <div class="item-card">
                        <div class="item-avatar">
                            {% if u.avatar %}<img src="/uploads/{{ u.avatar }}">{% else %}{{ u.name[:2] }}{% endif %}
                        </div>
                        <div class="item-details" onclick="location.href='/user/{{ u.id }}'" style="cursor:pointer;">
                            <div class="item-name">{{ u.name }} <span style="font-size:10px; color:var(--neon-green);">VIP</span></div>
                            <div class="item-sub">@{{ u.username }} | ID: {{ u.user_id_code }}</div>
                        </div>
                        <div class="action-btns">
                            <a href="/user/{{ u.id }}" class="btn-small" style="text-decoration:none;">يوزر</a>
                            <a href="/add_friend/{{ u.id }}" class="btn-small green" style="text-decoration:none;">إضافة</a>
                        </div>
                    </div>
                {% endif %}
            {% endfor %}
        </div>
    </div>

    <div class="tab-panel" id="tab-profile">
        <div class="profile-cover">
            {% if current_user.cover %}<img src="/uploads/{{ current_user.cover }}">{% endif %}
            <button onclick="openModal('edit-profile-modal')" style="position: absolute; bottom: 8px; left: 8px; background: rgba(0,0,0,0.6); color: #fff; border: 1px solid #fff; border-radius: 6px; font-size: 11px; padding: 4px 8px; cursor: pointer;">تغيير</button>
        </div>
        <div class="profile-avatar-circle">
            {% if current_user.avatar %}<img src="/uploads/{{ current_user.avatar }}">{% else %}🥷{% endif %}
            <div class="online-dot"></div>
        </div>

        <div style="font-size: 19px; font-weight: 800; display: flex; align-items: center; gap: 6px;">
            {{ current_user.name }} <span style="color: var(--neon-green); font-size: 16px;">✔</span>
        </div>
        <div style="color: var(--neon-green); font-size: 12px; margin-top: 3px;">● متصل الآن (VIP)</div>
        <div style="color: var(--text-muted); font-size: 13px; margin-top: 6px;">{{ current_user.bio }}</div>

        <div class="id-badge-card">
            <div class="badge-row">
                <span>USERNAME: <b>@{{ current_user.username }}</b></span>
                <button class="btn-copy" onclick="copyText('@{{ current_user.username }}')">نسخ</button>
            </div>
            <div class="badge-row">
                <span>VIP ID: <b>{{ current_user.user_id_code }}</b></span>
                <button class="btn-copy" onclick="copyText('{{ current_user.user_id_code }}')">نسخ</button>
            </div>
            <div class="badge-row">
                <span>JOINED: <b>{{ current_user.joined_date }}</b></span>
            </div>
        </div>

        <div class="stats-row">
            <div class="stat-card">
                <div class="stat-val">{{ friends_count }}</div>
                <div class="stat-lbl">صديق</div>
            </div>
            <div class="stat-card">
                <div class="stat-val">{{ current_user.visits }}</div>
                <div class="stat-lbl">زيارة</div>
            </div>
        </div>

        <button class="btn-small green" style="width: 100%; margin-top: 15px; padding: 12px;" onclick="openModal('edit-profile-modal')">تعديل البروفايل والغلاف</button>
    </div>
</div>

<div class="modal-overlay" id="add-story-modal">
    <div class="modal-content">
        <button class="btn-close-modal" onclick="closeModal('add-story-modal')">✕</button>
        <div style="font-weight: bold; font-size: 16px; margin-bottom: 15px; text-align: center;">نشر حالة جديدة</div>
        <form action="/publish_story" method="POST" enctype="multipart/form-data" style="display: flex; flex-direction: column; gap: 12px;">
            <div>
                <label style="font-size: 12px; color: var(--text-muted);">من يرى الحالة؟</label>
                <select name="privacy" style="width: 100%; background: var(--card-inner); border: 1px solid var(--border-color); color: #fff; padding: 10px; border-radius: 8px;">
                    <option value="public">للجميع (عامة)</option>
                    <option value="friends">خاصة للأصدقاء</option>
                </select>
            </div>
            <div>
                <label style="font-size: 12px; color: var(--text-muted);">نص الحالة (اختياري)</label>
                <textarea name="story_text" rows="3" placeholder="اكتب حالتك هنا..." style="width: 100%; background: var(--card-inner); border: 1px solid var(--border-color); color: #fff; padding: 10px; border-radius: 8px; resize: none;"></textarea>
            </div>
            <div>
                <label style="font-size: 12px; color: var(--text-muted);">الوسائط (صورة أو فيديو)</label>
                <input type="file" name="story_file" accept="image/*,video/*" style="width: 100%; background: var(--card-inner); border: 1px solid var(--border-color); color: #fff; padding: 8px; border-radius: 8px;">
            </div>
            <button class="btn-small green" type="submit" style="padding: 12px; font-size: 14px; margin-top: 6px;">نشر الآن</button>
        </form>
    </div>
</div>

<div class="modal-overlay" id="view-story-modal">
    <div class="modal-content" style="text-align: center;">
        <button class="btn-close-modal" onclick="closeModal('view-story-modal')">✕</button>
        <div id="v-author" style="font-weight: bold; font-size: 15px; margin-bottom: 2px;"></div>
        <div id="v-time" style="font-size: 11px; color: var(--text-muted); margin-bottom: 12px;"></div>
        <div id="v-text" style="font-size: 15px; margin-bottom: 15px; line-height: 1.5;"></div>
        <div id="v-media-wrap"></div>
    </div>
</div>

<div class="modal-overlay" id="create-group-modal">
    <div class="modal-content">
        <button class="btn-close-modal" onclick="closeModal('create-group-modal')">✕</button>
        <div style="font-weight: bold; font-size: 16px; margin-bottom: 15px; text-align: center;">إنشاء مجموعة جديدة</div>
        <form action="/new_group" method="POST" style="display: flex; flex-direction: column; gap: 12px;">
            <input name="g_name" placeholder="اسم المجموعة (مثال: محترفي فري فاير)" style="width: 100%; background: var(--card-inner); border: 1px solid var(--border-color); color: #fff; padding: 12px; border-radius: 10px;" required>
            <button class="btn-small green" type="submit" style="padding: 12px;">إنشاء المجموعة</button>
        </form>
    </div>
</div>

<div class="modal-overlay" id="edit-profile-modal">
    <div class="modal-content">
        <button class="btn-close-modal" onclick="closeModal('edit-profile-modal')">✕</button>
        <div style="font-weight: bold; font-size: 16px; margin-bottom: 15px; text-align: center;">تعديل الملف الشخصي</div>
        <form action="/save_profile" method="POST" enctype="multipart/form-data" style="display: flex; flex-direction: column; gap: 10px;">
            <div>
                <label style="font-size: 12px; color: var(--text-muted);">الاسم الظاهر</label>
                <input name="name" value="{{ current_user.name }}" style="width: 100%; background: var(--card-inner); border: 1px solid var(--border-color); color: #fff; padding: 10px; border-radius: 8px;">
            </div>
            <div>
                <label style="font-size: 12px; color: var(--text-muted);">البايو (Bio)</label>
                <input name="bio" value="{{ current_user.bio }}" style="width: 100%; background: var(--card-inner); border: 1px solid var(--border-color); color: #fff; padding: 10px; border-radius: 8px;">
            </div>
            <div>
                <label style="font-size: 12px; color: var(--text-muted);">تغيير الصورة الشخصية</label>
                <input type="file" name="avatar" accept="image/*" style="width: 100%; background: var(--card-inner); border: 1px solid var(--border-color); color: #fff; padding: 6px; border-radius: 8px;">
            </div>
            <div>
                <label style="font-size: 12px; color: var(--text-muted);">تغيير صورة الغلاف</label>
                <input type="file" name="cover" accept="image/*" style="width: 100%; background: var(--card-inner); border: 1px solid var(--border-color); color: #fff; padding: 6px; border-radius: 8px;">
            </div>
            <button class="btn-small green" type="submit" style="padding: 12px; margin-top: 6px;">حفظ التغييرات</button>
        </form>
    </div>
</div>

<div class="modal-overlay" id="settings-modal">
    <div class="modal-content" style="max-height: 85vh; overflow-y: auto;">
        <button class="btn-close-modal" onclick="closeModal('settings-modal')">✕</button>
        <div style="font-weight: bold; font-size: 16px; margin-bottom: 15px; text-align: center;">الإعدادات</div>
        <div style="display: flex; flex-direction: column; gap: 8px;">
            <div class="item-card" onclick="openModal('edit-profile-modal'); closeModal('settings-modal');" style="cursor: pointer;"><span>تعديل البروفايل</span> <span>›</span></div>
            <div class="item-card" onclick="showToast('تم تعيين خلفية النيون الافتراضية')" style="cursor: pointer;"><span>خلفية الدردشة</span> <span>›</span></div>
            <div class="item-card" onclick="showToast('عدد زوارك حتى الآن: {{ current_user.visits }}')" style="cursor: pointer;"><span>من زار بروفايلي</span> <span>›</span></div>
            <div class="item-card" onclick="showToast('الخصوصية: VIP مشفر بالكامل')" style="cursor: pointer;"><span>الخصوصية</span> <span>›</span></div>
            <a href="/logout" class="btn-small danger" style="text-align: center; text-decoration: none; padding: 12px; margin-top: 15px;">تسجيل الخروج</a>
        </div>
    </div>
</div>

<div id="toast">OK تم النسخ</div>

<script>
    const socket = io();

    function switchTab(tabId) {
        document.querySelectorAll('.tab-panel').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));

        const targetTab = document.getElementById('tab-' + tabId);
        if (targetTab) targetTab.classList.add('active');

        const targetBtn = document.getElementById('btn-' + tabId);
        if (targetBtn) targetBtn.classList.add('active');
    }

    function openModal(id) { document.getElementById(id).classList.add('active'); }
    function closeModal(id) { document.getElementById(id).classList.remove('active'); }

    function copyText(val) {
        navigator.clipboard.writeText(val);
        showToast('OK تم النسخ: ' + val);
    }

    function showToast(msg) {
        const t = document.getElementById('toast');
        t.innerText = msg;
        t.style.display = 'block';
        setTimeout(() => { t.style.display = 'none'; }, 2200);
    }

    function toggleTheme() {
        showToast('وضع VIP الليلي مفعل افتراضياً');
    }

    socket.on('broadcast_msg', function(data) {
        const stream = document.getElementById('chat-stream');
        const row = document.createElement('div');
        row.className = 'bubble-row ' + (data.is_me ? 'mine' : 'theirs');
        row.innerHTML = `
            <div class="bubble-msg ${data.is_me ? '' : 'other'}">
                <div class="bubble-header"><span>${data.sender_name}</span></div>
                <div>${data.content}</div>
                <div class="bubble-time">${data.created_at} ✔</div>
            </div>
        `;
        stream.appendChild(row);
        stream.scrollTop = stream.scrollHeight;
    });

    function sendChatMessage() {
        const inp = document.getElementById('chat-txt');
        const viewOnce = document.getElementById('chk-view-once').checked;
        if (inp.value.trim() !== '') {
            socket.emit('client_msg', {
                text: inp.value.trim(),
                view_once: viewOnce ? 1 : 0
            });
            inp.value = '';
            document.getElementById('chk-view-once').checked = false;
        }
    }

    document.getElementById('chat-txt').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') sendChatMessage();
    });

    function viewStory(name, time, text, media) {
        document.getElementById('v-author').innerText = name;
        document.getElementById('v-time').innerText = time;
        document.getElementById('v-text').innerText = text || '';
        const wrap = document.getElementById('v-media-wrap');
        wrap.innerHTML = '';
        if (media) {
            wrap.innerHTML = `<img src="/uploads/${media}" style="width:100%; max-height:280px; object-fit:contain; border-radius:12px;">`;
        }
        openModal('view-story-modal');
    }

    window.onload = function() {
        const s = document.getElementById('chat-stream');
        if (s) s.scrollTop = s.scrollHeight;
    };
</script>
</body>
</html>
"""

OTHER_PROFILE_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ u.name }} - Higori</title>
    <style>
        :root {
            --bg-color: #060b10;
            --card-bg: #0d1620;
            --border-color: #192b3a;
            --neon-green: #00ff88;
            --text-muted: #8ba2b5;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: system-ui, sans-serif; }
        body { background: var(--bg-color); color: #fff; padding: 15px; display: flex; justify-content: center; }
        .wrapper { width: 100%; max-width: 440px; background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 20px; padding: 16px; }
        .cover { width: 100%; height: 140px; border-radius: 14px; background: #162432; overflow: hidden; position: relative; margin-bottom: 45px; }
        .cover img { width: 100%; height: 100%; object-fit: cover; }
        .avatar { width: 75px; height: 75px; border-radius: 50%; border: 3px solid var(--card-bg); background: #1f3549; position: absolute; bottom: -35px; right: 18px; overflow: hidden; display: flex; justify-content: center; align-items: center; font-size: 26px; }
        .avatar img { width: 100%; height: 100%; object-fit: cover; }
        .btn-back { background: #142230; color: #fff; border: 1px solid var(--border-color); padding: 8px 16px; border-radius: 10px; text-decoration: none; display: inline-block; margin-bottom: 12px; font-size: 13px; }
        .btn-add { width: 100%; background: var(--neon-green); color: #000; font-weight: bold; border: none; padding: 12px; border-radius: 12px; margin-top: 15px; cursor: pointer; text-decoration: none; display: block; text-align: center; }
    </style>
</head>
<body>
<div class="wrapper">
    <a href="/" class="btn-back">‹ رجوع للمنصة</a>
    <div class="cover">
        {% if u.cover %}<img src="/uploads/{{ u.cover }}">{% endif %}
        <div class="avatar">{% if u.avatar %}<img src="/uploads/{{ u.avatar }}">{% else %}👤{% endif %}</div>
    </div>
    <div style="font-size: 20px; font-weight: bold;">{{ u.name }} <span style="color: var(--neon-green);">✔</span></div>
    <div style="color: var(--neon-green); font-size: 12px; margin-top: 3px;">● متصل الآن (VIP)</div>
    <div style="color: var(--text-muted); font-size: 13px; margin: 10px 0;">{{ u.bio }}</div>

    <div style="background: #13212f; border: 1px solid var(--border-color); border-radius: 12px; padding: 12px; font-size: 13px; display: flex; flex-direction: column; gap: 8px;">
        <div>USERNAME: <b>@{{ u.username }}</b></div>
        <div>VIP ID: <b>{{ u.user_id_code }}</b></div>
        <div>JOINED: <b>{{ u.joined_date }}</b></div>
    </div>

    <a href="/add_friend/{{ u.id }}" class="btn-add">إرسال طلب صداقة</a>
</div>
</body>
</html>
"""

@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    search_query = request.args.get('q', '').strip()

    with get_db() as conn:
        current_user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        
        if search_query:
            all_users = conn.execute(
                "SELECT * FROM users WHERE (name LIKE ? OR username LIKE ? OR user_id_code LIKE ?) AND id != ?",
                (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%", session['user_id'])
            ).fetchall()
        else:
            all_users = conn.execute('SELECT * FROM users ORDER BY id DESC LIMIT 30').fetchall()

        stories = conn.execute('SELECT * FROM stories ORDER BY id DESC LIMIT 20').fetchall()
        messages = conn.execute('SELECT * FROM messages WHERE group_id = 0 ORDER BY id ASC LIMIT 80').fetchall()

        pending_requests = conn.execute('''
            SELECT users.* FROM friendships 
            JOIN users ON friendships.user_a = users.id 
            WHERE friendships.user_b = ? AND friendships.status = 'pending'
        ''', (session['user_id'],)).fetchall()

        friends_count = conn.execute('''
            SELECT COUNT(*) as c FROM friendships 
            WHERE (user_a = ? OR user_b = ?) AND status = 'accepted'
        ''', (session['user_id'], session['user_id'])).fetchone()['c']

        my_groups = conn.execute('''
            SELECT groups.*, users.name as owner_name FROM groups 
            JOIN users ON groups.owner_id = users.id 
            ORDER BY groups.id DESC
        ''').fetchall()

    return render_template_string(
        MAIN_TEMPLATE,
        current_user=current_user,
        all_users=all_users,
        stories=stories,
        messages=messages,
        pending_requests=pending_requests,
        friends_count=friends_count,
        my_groups=my_groups,
        search_query=search_query
    )

@app.route('/uploads/<filename>')
def serve_upload(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/user/<int:user_id>')
def view_user_profile(user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    with get_db() as conn:
        conn.execute('UPDATE users SET visits = visits + 1 WHERE id = ?', (user_id,))
        conn.commit()
        u = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)) .fetchone()
    if not u:
        return redirect(url_for('home'))
    return render_template_string(OTHER_PROFILE_TEMPLATE, u=u)

@app.route('/save_profile', methods=['POST'])
def save_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    name = request.form.get('name')
    bio = request.form.get('bio')
    avatar = request.files.get('avatar')
    cover = request.files.get('cover')

    with get_db() as conn:
        if name:
            conn.execute('UPDATE users SET name = ?, bio = ? WHERE id = ?', (name, bio, session['user_id']))
        if avatar and avatar.filename:
            fn = f"av_{session['user_id']}_{int(time.time())}_{secure_filename(avatar.filename)}"
            avatar.save(os.path.join(app.config['UPLOAD_FOLDER'], fn))
            conn.execute('UPDATE users SET avatar = ? WHERE id = ?', (fn, session['user_id']))
        if cover and cover.filename:
            cv = f"cv_{session['user_id']}_{int(time.time())}_{secure_filename(cover.filename)}"
            cover.save(os.path.join(app.config['UPLOAD_FOLDER'], cv))
            conn.execute('UPDATE users SET cover = ? WHERE id = ?', (cv, session['user_id']))
        conn.commit()
    return redirect(url_for('home'))

@app.route('/publish_story', methods=['POST'])
def publish_story():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    text = request.form.get('story_text', '').strip()
    privacy = request.form.get('privacy', 'public')
    file = request.files.get('story_file')
    media_fn = ''

    if file and file.filename:
        media_fn = f"st_{session['user_id']}_{int(time.time())}_{secure_filename(file.filename)}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], media_fn))

    if text or media_fn:
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
        with get_db() as conn:
            u = conn.execute('SELECT name, avatar FROM users WHERE id = ?', (session['user_id'],)).fetchone()
            conn.execute('''
                INSERT INTO stories (user_id, user_name, user_avatar, content_text, media_path, privacy, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (session['user_id'], u['name'], u['avatar'], text, media_fn, privacy, now_str))
            conn.commit()
    return redirect(url_for('home'))

@app.route('/add_friend/<int:target_id>')
def add_friend(target_id):
    if 'user_id' not in session or target_id == session['user_id']:
        return redirect(url_for('home'))
    now_str = datetime.now().strftime('%Y-%m-%d')
    with get_db() as conn:
        chk = conn.execute('SELECT * FROM friendships WHERE (user_a = ? AND user_b = ?) OR (user_a = ? AND user_b = ?)',
                           (session['user_id'], target_id, target_id, session['user_id'])).fetchone()
        if not chk:
            conn.execute('INSERT INTO friendships (user_a, user_b, status, created_at) VALUES (?, ?, ?, ?)',
                         (session['user_id'], target_id, 'pending', now_str))
            conn.commit()
    return redirect(url_for('home'))

@app.route('/accept_friend/<int:requester_id>')
def accept_friend(requester_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    with get_db() as conn:
        conn.execute('UPDATE friendships SET status = ? WHERE user_a = ? AND user_b = ?',
                     ('accepted', requester_id, session['user_id']))
        conn.commit()
    return redirect(url_for('home'))

@app.route('/reject_friend/<int:requester_id>')
def reject_friend(requester_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    with get_db() as conn:
        conn.execute('DELETE FROM friendships WHERE user_a = ? AND user_b = ?', (requester_id, session['user_id']))
        conn.commit()
    return redirect(url_for('home'))

@app.route('/new_group', methods=['POST'])
def new_group():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    g_name = request.form.get('g_name', '').strip()
    if g_name:
        code = str(random.randint(10000000, 99999999))
        now_str = datetime.now().strftime('%Y-%m-%d')
        with get_db() as conn:
            cur = 
