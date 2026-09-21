import os
import sqlite3
import random
import time
from flask import Flask, request, redirect, url_for, session, render_template_string, send_from_directory
from flask_socketio import SocketIO, emit
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'higori-platform-vip-ultra-2026'
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

socketio = SocketIO(app, cors_allowed_origins="*")

def get_db():
    conn = sqlite3.connect('chat_app.db')
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
                bio TEXT DEFAULT 'VIP Member at Higori Platform',
                visits INTEGER DEFAULT 0
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_name TEXT,
                sender_username TEXT,
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS stories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT,
                media_path TEXT,
                created_at REAL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_name TEXT,
                group_code TEXT,
                created_by TEXT
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
            --bg-color: #04080c;
            --card-bg: rgba(11, 20, 29, 0.9);
            --neon-green: #00ff88;
            --neon-glow: 0 0 25px rgba(0, 255, 136, 0.5);
            --border-glow: 1px solid rgba(0, 255, 136, 0.25);
            --text-muted: #8ba2b5;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: system-ui, sans-serif; }
        body {
            background: radial-gradient(circle at top, #0c2017 0%, #04080c 80%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
            color: #ffffff;
        }
        .vip-card {
            width: 100%;
            max-width: 400px;
            background: var(--card-bg);
            border: var(--border-glow);
            border-radius: 24px;
            padding: 35px 25px;
            backdrop-filter: blur(12px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.8), var(--neon-glow);
            text-align: center;
        }
        .vip-badge {
            display: inline-block;
            background: rgba(0, 255, 136, 0.1);
            color: var(--neon-green);
            padding: 4px 14px;
            border-radius: 30px;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 2px;
            border: 1px solid var(--neon-green);
            margin-bottom: 12px;
        }
        .title { font-size: 26px; font-weight: 900; margin-bottom: 6px; }
        .title span { color: var(--neon-green); text-shadow: var(--neon-glow); }
        .subtitle { font-size: 13px; color: var(--text-muted); margin-bottom: 25px; }
        .form-group { margin-bottom: 15px; text-align: right; }
        .form-group label { display: block; font-size: 12px; color: var(--text-muted); margin-bottom: 5px; }
        .input-box {
            width: 100%;
            padding: 13px 15px;
            background: rgba(7, 13, 19, 0.95);
            border: 1px solid #1a2936;
            border-radius: 12px;
            color: #fff;
            font-size: 14px;
            outline: none;
        }
        .input-box:focus { border-color: var(--neon-green); box-shadow: 0 0 10px rgba(0,255,136,0.3); }
        .btn-vip {
            width: 100%;
            padding: 14px;
            margin-top: 12px;
            background: linear-gradient(135deg, #00ff88, #00a859);
            border: none;
            border-radius: 12px;
            color: #04080c;
            font-size: 15px;
            font-weight: 800;
            cursor: pointer;
            box-shadow: var(--neon-glow);
        }
        .toggle-link { margin-top: 20px; font-size: 13px; color: var(--text-muted); }
        .toggle-link a { color: var(--neon-green); text-decoration: none; font-weight: bold; }
        .error-msg { background: rgba(255, 75, 75, 0.15); border: 1px solid #ff4b4b; color: #ff6b6b; padding: 10px; border-radius: 8px; font-size: 12px; margin-bottom: 15px; }
    </style>
</head>
<body>
<div class="vip-card">
    <div class="vip-badge">VIP PLATFORM</div>
    <div class="title">Higori <span>platform</span></div>
    {% if mode == 'register' %}
        <div class="subtitle">إنشاء حساب مستخدم جديد ومميّز</div>
        {% if error %}<div class="error-msg">{{ error }}</div>{% endif %}
        <form method="POST">
            <div class="form-group"><label>الاسم الظاهر</label><input class="input-box" name="name" placeholder="اسمك" required></div>
            <div class="form-group"><label>اسم المستخدم (Username)</label><input class="input-box" name="username" placeholder="user_vip" required></div>
            <div class="form-group"><label>كلمة المرور</label><input class="input-box" type="password" name="password" placeholder="••••••••" required></div>
            <button class="btn-vip" type="submit">إنشاء الحساب</button>
        </form>
        <div class="toggle-link">لديك حساب؟ <a href="/login">تسجيل الدخول</a></div>
    {% else %}
        <div class="subtitle">بوابة الدخول للمنصة</div>
        {% if error %}<div class="error-msg">{{ error }}</div>{% endif %}
        <form method="POST">
            <div class="form-group"><label>اسم المستخدم</label><input class="input-box" name="username" placeholder="Username" required></div>
            <div class="form-group"><label>كلمة المرور</label><input class="input-box" type="password" name="password" placeholder="••••••••" required></div>
            <button class="btn-vip" type="submit">تسجيل الدخول</button>
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
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Higori platform</title>
    <script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
    <style>
        :root {
            --bg-dark: #070d12;
            --card-bg: #0f1922;
            --border-color: #1a2936;
            --neon-green: #00ff88;
            --neon-glow: 0 0 12px rgba(0, 255, 136, 0.45);
            --text-gray: #8ba2b5;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: system-ui, sans-serif; }
        body {
            background-color: var(--bg-dark);
            color: #ffffff;
            padding: 15px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .container { width: 100%; max-width: 440px; display: flex; flex-direction: column; gap: 12px; }
        .app-title { text-align: center; font-size: 24px; font-weight: 900; letter-spacing: 2px; color: var(--neon-green); text-shadow: var(--neon-glow); margin-top: 5px; }
        .btn-settings-top {
            background: linear-gradient(180deg, #00bd67, #007a43);
            color: white; border: none; padding: 12px; border-radius: 12px; font-weight: bold; font-size: 15px; cursor: pointer; box-shadow: var(--neon-glow);
        }
        .nav-bar {
            display: flex; justify-content: space-between; background-color: var(--card-bg); border: 1px solid var(--border-color); border-radius: 16px; padding: 10px 8px;
        }
        .nav-item {
            display: flex; flex-direction: column; align-items: center; gap: 4px; cursor: pointer; color: var(--text-gray); font-size: 12px; flex: 1; transition: 0.2s;
        }
        .nav-item.active { color: var(--neon-green); font-weight: bold; }
        .nav-item .icon { font-size: 20px; }
        .tab-content {
            background-color: var(--card-bg); border: 1px solid var(--border-color); border-radius: 16px; padding: 16px; min-height: 460px; display: none; flex-direction: column;
        }
        .tab-content.active { display: flex; }
        
        /* Stories */
        .status-tray { display: flex; gap: 15px; overflow-x: auto; padding-bottom: 10px; }
        .status-item { display: flex; flex-direction: column; align-items: center; gap: 6px; cursor: pointer; }
        .status-avatar-circle {
            width: 65px; height: 65px; border-radius: 50%; border: 2px solid var(--neon-green); display: flex; justify-content: center; align-items: center; overflow: hidden; background: #14222d;
        }
        .status-avatar-circle img { width: 100%; height: 100%; object-fit: cover; }
        
        /* Chat */
        #chat-messages { flex: 1; height: 340px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; margin-bottom: 10px; }
        .msg-bubble { background-color: #122822; border-right: 3px solid var(--neon-green); padding: 8px 12px; border-radius: 8px; max-width: 85%; word-wrap: break-word; font-size: 13px; }
        .msg-bubble .sender { font-size: 11px; color: var(--neon-green); font-weight: bold; margin-bottom: 3px; }
        .chat-inputs { display: flex; gap: 8px; }
        .chat-inputs input { flex: 1; padding: 12px; background: #14222d; border: 1px solid var(--border-color); border-radius: 10px; color: white; outline: none; }
        .chat-inputs button { background: var(--neon-green); color: black; border: none; padding: 12px 18px; border-radius: 10px; font-weight: bold; cursor: pointer; }

        /* Profile */
        .profile-cover {
            width: 100%; height: 120px; background: #152430; border-radius: 12px; position: relative; margin-bottom: 45px; overflow: hidden;
        }
        .profile-cover img { width: 100%; height: 100%; object-fit: cover; }
        .profile-pic {
            width: 75px; height: 75px; border-radius: 50%; border: 3px solid var(--card-bg); background: #1b2e3d; position: absolute; bottom: -35px; right: 20px; overflow: hidden; display: flex; align-items: center; justify-content: center; font-size: 30px;
        }
        .profile-pic img { width: 100%; height: 100%; object-fit: cover; }
        .upload-badge { position: absolute; bottom: 0; background: rgba(0,0,0,0.6); width: 100%; text-align: center; font-size: 10px; color: #fff; cursor: pointer; }
        .user-id-card { background: #14222d; border: 1px solid var(--border-color); border-radius: 10px; padding: 12px; margin-top: 12px; font-size: 13px; display: flex; flex-direction: column; gap: 8px; }
        
        .btn-action { background: #14222d; border: 1px solid var(--border-color); color: white; padding: 10px; border-radius: 8px; cursor: pointer; width: 100%; margin-top: 8px; font-weight: bold; }
        .btn-danger { background: rgba(255, 75, 75, 0.15); border: 1px solid #ff4b4b; color: #ff6b6b; text-decoration: none; text-align: center; }
    </style>
</head>
<body>

<div class="container">
    <div class="app-title">Higori platform</div>
    <button class="btn-settings-top" onclick="switchTab('settings')">الإعدادات والتعديل</button>

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
            <span class="icon">👥</span><span>الأعضاء</span>
        </div>
        <div class="nav-item" id="btn-profile" onclick="switchTab('profile')">
            <span class="icon">👤</span><span>بروفايلي</span>
        </div>
    </div>

    <!-- Status Tab -->
    <div class="tab-content active" id="tab-status">
        <div style="font-weight: bold; margin-bottom: 12px;">الحالات اليومية</div>
        <div class="status-tray">
            <label class="status-item">
                <form id="story-form" action="/upload_story" method="POST" enctype="multipart/form-data">
                    <input type="file" name="story_file" accept="image/*" style="display:none" onchange="document.getElementById('story-form').submit()">
                    <div class="status-avatar-circle" style="border-style: dashed; font-size: 26px;">+</div>
                </form>
                <span style="font-size: 11px; color: var(--text-gray);">إضافة حالة</span>
            </label>
            {% for s in stories %}
                <div class="status-item" onclick="viewImage('{{ s.media_path }}')">
                    <div class="status-avatar-circle"><img src="/uploads/{{ s.media_path }}"></div>
                    <span style="font-size: 11px; color: var(--text-gray);">{{ s.user_name }}</span>
                </div>
            {% endfor %}
        </div>
        {% if not stories %}
            <div style="text-align: center; color: var(--text-gray); margin-top: 80px; font-size: 14px;">لا توجد حالات حالياً، كن أول من ينشر!</div>
        {% endif %}
    </div>

    <!-- Chat Tab -->
    <div class="tab-content" id="tab-chats">
        <div style="font-weight: bold; color: var(--neon-green); margin-bottom: 8px;">غرفة الدردشة العامة VIP</div>
        <div id="chat-messages">
            {% for msg in messages %}
                <div class="msg-bubble">
                    <div class="sender">{{ msg.sender_name }} (@{{ msg.sender_username }})</div>
                    <div>{{ msg.content }}</div>
                </div>
            {% endfor %}
        </div>
        <div class="chat-inputs">
            <input type="text" id="msg-input" placeholder="اكتب رسالة..." autocomplete="off">
            <button onclick="sendMsg()">إرسال</button>
        </div>
    </div>

    <!-- Groups Tab -->
    <div class="tab-content" id="tab-groups">
        <div style="font-weight: bold; margin-bottom: 12px;">المجموعات المتاحة</div>
        <form action="/create_group" method="POST" style="display: flex; gap: 6px; margin-bottom: 15px;">
            <input name="group_name" placeholder="اسم المجموعة الجديدة..." style="flex:1; padding: 10px; background: #14222d; border: 1px solid var(--border-color); border-radius: 8px; color: #fff;" required>
            <button style="background: var(--neon-green); border: none; padding: 10px 14px; border-radius: 8px; font-weight: bold; cursor: pointer;">إنشاء</button>
        </form>
        <div style="display: flex; flex-direction: column; gap: 8px;">
            {% for g in groups %}
                <div style="background: #14222d; padding: 12px; border-radius: 10px; border: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-weight: bold;">{{ g.group_name }}</div>
                        <div style="font-size: 11px; color: var(--text-gray);">الرمز: {{ g.group_code }} | المالك: {{ g.created_by }}</div>
                    </div>
                    <button style="background: #1e3345; border:none; color:#fff; padding: 6px 12px; border-radius: 6px;">دخول</button>
                </div>
            {% endfor %}
        </div>
    </div>

    <!-- People Tab -->
    <div class="tab-content" id="tab-people">
        <div style="font-weight: bold; margin-bottom: 12px;">أعضاء المنصة المسجلين ({{ all_users|length }})</div>
        <div style="display: flex; flex-direction: column; gap: 8px;">
            {% for u in all_users %}
                <div style="background: #14222d; border: 1px solid var(--border-color); padding: 10px 14px; border-radius: 10px; display: flex; align-items: center; justify-content: space-between;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <div style="width: 40px; height: 40px; border-radius: 50%; overflow: hidden; background: #1b2e3d; display: flex; justify-content: center; align-items: center;">
                            {% if u.avatar %}<img src="/uploads/{{ u.avatar }}" style="width:100%; height:100%; object-fit: cover;">{% else %}👤{% endif %}
                        </div>
                        <div>
                            <div style="font-weight: bold; font-size: 13px;">{{ u.name }}</div>
                            <div style="font-size: 11px; color: var(--text-gray);">@{{ u.username }} | ID: {{ u.user_id_code }}</div>
                        </div>
                    </div>
                    <span style="color: var(--neon-green); font-size: 12px;">VIP</span>
                </div>
            {% endfor %}
        </div>
    </div>

    <!-- Profile Tab -->
    <div class="tab-content" id="tab-profile">
        <div class="profile-cover">
            {% if user.cover %}<img src="/uploads/{{ user.cover }}">{% endif %}
        </div>
        <div class="profile-pic">
            {% if user.avatar %}<img src="/uploads/{{ user.avatar }}">{% else %}🥷{% endif %}
        </div>
        
        <div style="font-size: 19px; font-weight: 800; margin-top: 5px;">{{ user.name }} <span style="color: var(--neon-green);">✔</span></div>
        <div style="color: var(--neon-green); font-size: 12px; margin-top: 2px;">● حساب نشط أونلاين (VIP)</div>
        <div style="font-size: 13px; color: var(--text-gray); margin-top: 6px;">{{ user.bio }}</div>

        <div class="user-id-card">
            <div style="display: flex; justify-content: space-between;"><span>USERNAME:</span> <b>@{{ user.username }}</b></div>
            <div style="display: flex; justify-content: space-between;"><span>VIP ID:</span> <b>{{ user.user_id_code }}</b></div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 12px;">
            <div style="background: #14222d; padding: 12px; border-radius: 10px; text-align: center; border: 1px solid var(--border-color);">
                <div style="font-size: 20px; font-weight: bold; color: var(--neon-green);">{{ all_users|length }}</div>
                <div style="font-size: 11px; color: var(--text-gray);">أعضاء VIP</div>
            </div>
            <div style="background: #14222d; padding: 12px; border-radius: 10px; text-align: center; border: 1px solid var(--border-color);">
                <div style="font-size: 20px; font-weight: bold; color: var(--neon-green);">{{ messages|length }}</div>
                <div style="font-size: 11px; color: var(--text-gray);">رسالة مرسلة</div>
            </div>
        </div>
    </div>

    <!-- Settings Tab -->
    <div class="tab-content" id="tab-settings">
        <div style="font-weight: bold; margin-bottom: 12px;">تخصيص الحساب والصور</div>
        <form action="/update_profile" method="POST" enctype="multipart/form-data" style="display: flex; flex-direction: column; gap: 10px;">
            <div>
                <label style="font-size: 12px; color: var(--text-gray);">الصورة الشخصية (Avatar)</label>
                <input type="file" name="avatar" accept="image/*" class="btn-action">
            </div>
            <div>
                <label style="font-size: 12px; color: var(--text-gray);">صورة الغلاف (Cover)</label>
                <input type="file" name="cover" accept="image/*" class="btn-action">
            </div>
            <div>
                <label style="font-size: 12px; color: var(--text-gray);">الاسم الظاهر</label>
                <input name="name" value="{{ user.name }}" class="btn-action" style="text-align: right;" required>
            </div>
            <div>
                <label style="font-size: 12px; color: var(--text-gray);">البايو (Bio)</label>
                <input name="bio" value="{{ user.bio }}" class="btn-action" style="text-align: right;">
            </div>
            <button type="submit" class="btn-action" style="background: var(--neon-green); color: black; margin-top: 5px;">حفظ التغييرات</button>
        </form>
        <a href="/logout" class="btn-action btn-danger" style="margin-top: 20px; display: block;">تسجيل الخروج</a>
    </div>
</div>

<script>
    const socket = io();

    function switchTab(tabId) {
        document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));

        const targetTab = document.getElementById('tab-' + tabId);
        if (targetTab) targetTab.classList.add('active');

        const targetBtn = document.getElementById('btn-' + tabId);
        if (targetBtn) targetBtn.classList.add('active');
    }

    socket.on('chat_broadcast', function(data) {
        const box = document.getElementById('chat-messages');
        const div = document.createElement('div');
        div.className = 'msg-bubble';
        div.innerHTML = '<div class="sender">' + data.sender + ' (@' + data.username + ')</div><div>' + data.text + '</div>';
        box.appendChild(div);
        box.scrollTop = box.scrollHeight;
    });

    function sendMsg() {
        const input = document.getElementById('msg-input');
        if (input.value.trim() !== '') {
            socket.emit('new_message', { text: input.value.trim() });
            input.value = '';
        }
    }

    document.getElementById('msg-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') sendMsg();
    });

    function viewImage(path) {
        window.open('/uploads/' + path, '_blank');
    }

    window.onload = function() {
        const box = document.getElementById('chat-messages');
        if (box) box.scrollTop = box.scrollHeight;
    };
</script>
</body>
</html>
"""

@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    with get_db() as conn:
        user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        all_users = conn.execute('SELECT name, username, user_id_code, avatar FROM users').fetchall()
        messages = conn.execute('SELECT * FROM messages ORDER BY id ASC LIMIT 50').fetchall()
        stories = conn.execute('SELECT * FROM stories ORDER BY id DESC LIMIT 15').fetchall()
        groups = conn.execute('SELECT * FROM groups ORDER BY id DESC').fetchall()
    return render_template_string(
        MAIN_TEMPLATE,
        user=user,
        all_users=all_users,
        messages=messages,
        stories=stories,
        groups=groups
    )

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/update_profile', methods=['POST'])
def update_profile():
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
            fname = f"avatar_{session['user_id']}_{int(time.time())}_{secure_filename(avatar.filename)}"
            avatar.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
            conn.execute('UPDATE users SET avatar = ? WHERE id = ?', (fname, session['user_id']))
        if cover and cover.filename:
            cname = f"cover_{session['user_id']}_{int(time.time())}_{secure_filename(cover.filename)}"
            cover.save(os.path.join(app.config['UPLOAD_FOLDER'], cname))
            conn.execute('UPDATE users SET cover = ? WHERE id = ?', (cname, session['user_id']))
        conn.commit()
    return redirect(url_for('home'))

@app.route('/upload_story', methods=['POST'])
def upload_story():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    file = request.files.get('story_file')
    if file and file.filename:
        sname = f"story_{session['user_id']}_{int(time.time())}_{secure_filename(file.filename)}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], sname))
        with get_db() as conn:
            conn.execute('INSERT INTO stories (user_name, media_path, created_at) VALUES (?, ?, ?)',
                         (session.get('name', 'عضو'), sname, time.time()))
            conn.commit()
    return redirect(url_for('home'))

@app.route('/create_group', methods=['POST'])
def create_group():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    gname = request.form.get('group_name')
    if gname:
        code = str(random.randint(100000, 999999))
        with get_db() as conn:
            conn.execute('INSERT INTO groups (group_name, group_code, created_by) VALUES (?, ?, ?)',
                         (gname, code, session.get('name')))
            conn.commit()
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        username = request.form.get('username', '').lower().strip()
        password = request.form.get('password', '')

        if not name or not username or not password:
            error = 'يرجى ملء جميع الحقول المطلوبة'
        else:
            with get_db() as conn:
                existing = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
                if existing:
                    error = 'اسم المستخدم هذا مأخوذ بالفعل، جرّب غيره'
                else:
                    user_id_code = str(random.randint(10000000, 99999999))
                    hashed_pw = generate_password_hash(password)
                    conn.execute(
                        'INSERT INTO users (user_id_code, name, username, password) VALUES (?, ?, ?, ?)',
                        (user_id_code, name, username, hashed_pw)
                    )
                    conn.commit()
                    return redirect(url_for('login'))
    return render_template_string(AUTH_TEMPLATE, mode='register', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').lower().strip()
        password = request.form.get('password', '')
        with get_db() as conn:
            user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['name'] = user['name']
            session['username'] = user['username']
            return redirect(url_for('home'))
        else:
            error = 'اسم المستخدم أو كلمة المرور غير صحيحة'
    return render_template_string(AUTH_TEMPLATE, mode='login', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@socketio.on('new_message')
def handle_new_message(data):
    if 'user_id' in session:
        text = data.get('text', '').strip()
        if text:
            with get_db() as conn:
                conn.execute('INSERT INTO messages (sender_name, sender_username, content) VALUES (?, ?, ?)',
                             (session['name'], session['username'], text))
                conn.commit()
            emit('chat_broadcast', {
                'text': text,
                'sender': session['name'],
                'username': session['username']
            }, broadcast=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)

