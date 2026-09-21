import os
from flask import Flask, request, redirect, url_for, session, render_template_string
from flask_socketio import SocketIO, send
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'higori-platform-vip-secret-2026'
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
                bio TEXT DEFAULT 'VIP Member at Higori Platform',
                visits INTEGER DEFAULT 0
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
    <title>Higori platform - VIP Portal</title>
    <style>
        :root {
            --bg-color: #05080c;
            --card-bg: rgba(13, 21, 30, 0.85);
            --neon-green: #00ff88;
            --neon-glow: 0 0 20px rgba(0, 255, 136, 0.45);
            --border-glow: 1px solid rgba(0, 255, 136, 0.25);
            --text-muted: #8ba2b5;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: system-ui, -apple-system, sans-serif;
        }

        body {
            background: radial-gradient(circle at top, #0f241d 0%, #05080c 70%);
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
            box-shadow: 0 15px 35px rgba(0,0,0,0.6), var(--neon-glow);
            text-align: center;
            position: relative;
            overflow: hidden;
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

        .title {
            font-size: 26px;
            font-weight: 900;
            color: #ffffff;
            letter-spacing: 1px;
            margin-bottom: 6px;
            text-shadow: 0 0 15px rgba(255,255,255,0.2);
        }

        .title span {
            color: var(--neon-green);
            text-shadow: var(--neon-glow);
        }

        .subtitle {
            font-size: 13px;
            color: var(--text-muted);
            margin-bottom: 25px;
        }

        .form-group {
            margin-bottom: 16px;
            text-align: right;
        }

        .form-group label {
            display: block;
            font-size: 12px;
            color: var(--text-muted);
            margin-bottom: 6px;
            padding-right: 4px;
        }

        .input-box {
            width: 100%;
            padding: 14px 16px;
            background: rgba(8, 14, 20, 0.9);
            border: 1px solid #1a2936;
            border-radius: 12px;
            color: #fff;
            font-size: 14px;
            outline: none;
            transition: 0.3s;
        }

        .input-box:focus {
            border-color: var(--neon-green);
            box-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
        }

        .btn-vip {
            width: 100%;
            padding: 14px;
            margin-top: 10px;
            background: linear-gradient(135deg, #00ff88, #00a859);
            border: none;
            border-radius: 12px;
            color: #05080c;
            font-size: 15px;
            font-weight: 800;
            letter-spacing: 1px;
            cursor: pointer;
            box-shadow: var(--neon-glow);
            transition: 0.3s;
        }

        .btn-vip:hover {
            transform: translateY(-2px);
            box-shadow: 0 0 25px rgba(0, 255, 136, 0.7);
        }

        .toggle-link {
            margin-top: 22px;
            font-size: 13px;
            color: var(--text-muted);
        }

        .toggle-link a {
            color: var(--neon-green);
            text-decoration: none;
            font-weight: bold;
        }

        .error-msg {
            background: rgba(255, 75, 75, 0.15);
            border: 1px solid #ff4b4b;
            color: #ff6b6b;
            padding: 10px;
            border-radius: 8px;
            font-size: 12px;
            margin-bottom: 18px;
        }
    </style>
</head>
<body>

<div class="vip-card">
    <div class="vip-badge">VIP ACCESS</div>
    <div class="title">Higori <span>platform</span></div>
    
    {% if mode == 'register' %}
        <div class="subtitle">إنشاء حساب مستخدم جديد ومميّز</div>
        {% if error %}<div class="error-msg">{{ error }}</div>{% endif %}
        <form method="POST">
            <div class="form-group">
                <label>الاسم المستعار (الظاهر للجميع)</label>
                <input class="input-box" name="name" placeholder="مثلاً: أسامة" required>
            </div>
            <div class="form-group">
                <label>اسم المستخدم (Username بالإنجليزية)</label>
                <input class="input-box" name="username" placeholder="مثلاً: osama_vip" required>
            </div>
            <div class="form-group">
                <label>كلمة المرور السرية</label>
                <input class="input-box" type="password" name="password" placeholder="••••••••" required>
            </div>
            <button class="btn-vip" type="submit">إنشاء الحساب الآن</button>
        </form>
        <div class="toggle-link">
            لديك حساب بالفعل؟ <a href="/login">تسجيل الدخول</a>
        </div>
    {% else %}
        <div class="subtitle">سجّل دخولك للوصول للدردشة المباشرة</div>
        {% if error %}<div class="error-msg">{{ error }}</div>{% endif %}
        <form method="POST">
            <div class="form-group">
                <label>اسم المستخدم</label>
                <input class="input-box" name="username" placeholder="اسم المستخدم" required>
            </div>
            <div class="form-group">
                <label>كلمة المرور</label>
                <input class="input-box" type="password" name="password" placeholder="••••••••" required>
            </div>
            <button class="btn-vip" type="submit">دخول النظام</button>
        </form>
        <div class="toggle-link">
            مستخدم جديد؟ <a href="/register">إنشاء حساب VIP</a>
        </div>
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

        body {
            background-color: var(--bg-dark);
            color: #ffffff;
            font-family: system-ui, -apple-system, sans-serif;
            margin: 0;
            padding: 15px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        .container {
            width: 100%;
            max-width: 440px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .app-title {
            text-align: center;
            font-size: 22px;
            font-weight: 900;
            letter-spacing: 2px;
            color: var(--neon-green);
            text-shadow: var(--neon-glow);
            margin: 10px 0 5px 0;
        }

        .btn-settings-top {
            background: linear-gradient(180deg, #00bd67, #007a43);
            color: white;
            border: none;
            padding: 12px;
            border-radius: 12px;
            font-weight: bold;
            font-size: 15px;
            cursor: pointer;
            box-shadow: var(--neon-glow);
            margin-bottom: 5px;
        }

        .nav-bar {
            display: flex;
            justify-content: space-between;
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 10px 12px;
        }

        .nav-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
            cursor: pointer;
            color: var(--text-gray);
            font-size: 12px;
            transition: 0.2s;
            flex: 1;
        }

        .nav-item.active {
            color: var(--neon-green);
            font-weight: bold;
        }

        .nav-item .icon {
            font-size: 20px;
        }

        .nav-item.active .icon {
            filter: drop-shadow(0 0 6px var(--neon-green));
        }

        .tab-content {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 16px;
            min-height: 440px;
            display: none;
            flex-direction: column;
        }

        .tab-content.active {
            display: flex;
        }

        .status-header {
            font-size: 15px;
            font-weight: bold;
            margin-bottom: 15px;
        }
        .add-status {
            display: flex;
            flex-direction: column;
            align-items: center;
            width: fit-content;
            gap: 5px;
            cursor: pointer;
        }
        .status-avatar {
            width: 65px;
            height: 65px;
            border-radius: 50%;
            border: 2px dashed var(--neon-green);
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 28px;
            background: #152430;
        }
        .no-status-msg {
            margin-top: auto;
            margin-bottom: auto;
            text-align: center;
            color: var(--text-gray);
            font-size: 14px;
        }

        #chat-messages {
            flex: 1;
            height: 320px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-bottom: 10px;
        }
        .msg-bubble {
            background-color: #0b3d2c;
            padding: 8px 12px;
            border-radius: 10px;
            max-width: 80%;
            word-wrap: break-word;
            font-size: 13px;
        }
        .msg-bubble .sender {
            font-size: 11px;
            color: var(--neon-green);
            font-weight: bold;
            margin-bottom: 2px;
        }
        .chat-inputs {
            display: flex;
            gap: 8px;
        }
        .chat-inputs input {
            flex: 1;
            padding: 12px;
            background: #14222d;
            border: 1px solid var(--border-color);
            border-radius: 10px;
            color: white;
            outline: none;
        }
        .chat-inputs button {
            background: var(--neon-green);
            color: black;
            border: none;
            padding: 12px 18px;
            border-radius: 10px;
            font-weight: bold;
            cursor: pointer;
        }

        .profile-cover {
            width: 100%;
            height: 120px;
            background: linear-gradient(135deg, #1f4037, #99f2c8);
            border-radius: 12px;
            position: relative;
            margin-bottom: 45px;
        }
        .profile-pic {
            width: 75px;
            height: 75px;
            border-radius: 50%;
            border: 3px solid var(--card-bg);
            background: #152430;
            position: absolute;
            bottom: -35px;
            right: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 32px;
        }
        .online-dot {
            width: 12px;
            height: 12px;
            background: var(--neon-green);
            border-radius: 50%;
            position: absolute;
            bottom: 2px;
            left: 2px;
            border: 2px solid var(--card-bg);
        }
        .user-id-card {
            background: #14222d;
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 10px 14px;
            font-size: 12px;
            margin-top: 10px;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 15px;
        }
        .stat-box {
            background: #14222d;
            border: 1px solid var(--border-color);
            padding: 12px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-num { font-size: 20px; font-weight: bold; color: var(--neon-green); }
        .stat-label { font-size: 12px; color: var(--text-gray); }

        .settings-menu {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .menu-item {
            background: #14222d;
            border: 1px solid var(--border-color);
            padding: 14px;
            border-radius: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 14px;
            cursor: pointer;
        }
        .menu-item.danger {
            background: rgba(255, 75, 75, 0.1);
            border-color: #ff4b4b;
            color: #ff4b4b;
            font-weight: bold;
            justify-content: center;
            text-decoration: none;
        }
    </style>
</head>
<body>

<div class="container">
    <div class="app-title">Higori platform</div>
    <button class="btn-settings-top" onclick="switchTab('settings')">الإعدادات</button>

    <div class="nav-bar">
        <div class="nav-item active" id="btn-status" onclick="switchTab('status')">
            <span class="icon">⛺</span>
            <span>الحالات</span>
        </div>
        <div class="nav-item" id="btn-chats" onclick="switchTab('chats')">
            <span class="icon">💬</span>
            <span>الدردشات</span>
        </div>
        <div class="nav-item" id="btn-groups" onclick="switchTab('groups')">
            <span class="icon">🎯</span>
            <span>مجموعات</span>
        </div>
        <div class="nav-item" id="btn-people" onclick="switchTab('people')">
            <span class="icon">👥</span>
            <span>أشخاص</span>
        </div>
        <div class="nav-item" id="btn-profile" onclick="switchTab('profile')">
            <span class="icon">👤</span>
            <span>بروفايلي</span>
        </div>
    </div>

    <div class="tab-content active" id="tab-status">
        <div class="status-header">الحالات (24 ساعة)</div>
        <div class="add-status">
            <div class="status-avatar">+</div>
            <span style="font-size: 12px; color: var(--text-gray);">أضف</span>
        </div>
        <div class="no-status-msg">لا حالات حديثة.</div>
    </div>

    <div class="tab-content" id="tab-chats">
        <div style="font-weight: bold; margin-bottom: 10px; color: var(--neon-green);">غرفة المحادثة المباشرة VIP</div>
        <div id="chat-messages"></div>
        <div class="chat-inputs">
            <input type="text" id="msg-input" placeholder="اكتب رسالتك..." autocomplete="off">
            <button onclick="sendMsg()">إرسال</button>
        </div>
    </div>

    <div class="tab-content" id="tab-groups">
        <div style="font-weight: bold; margin-bottom: 15px;">مجموعاتي</div>
        <div style="background: #14222d; padding: 14px; border-radius: 10px; display: flex; justify-content: space-between; align-items: center; border: 1px solid var(--border-color);">
            <div>
                <div style="font-weight: bold;">FREE FIRE VIP</div>
                <div style="font-size: 11px; color: var(--text-gray);">ID: 73138911</div>
            </div>
            <button style="background: var(--border-color); color: white; border: none; padding: 6px 14px; border-radius: 6px;">عرض</button>
        </div>
    </div>

    <div class="tab-content" id="tab-people">
        <div style="font-weight: bold; margin-bottom: 15px;">الأعضاء المتصلين</div>
        <div class="menu-item">
            <div>
                <div style="font-weight: bold;">HUSSAM 👑</div>
                <div style="font-size: 11px; color: var(--text-gray);">ID: 46750674</div>
            </div>
            <span style="color: var(--neon-green); font-size: 13px;">عضو VIP</span>
        </div>
    </div>

    <div class="tab-content" id="tab-profile">
        <div class="profile-cover">
            <div class="profile-pic">
                🥷
                <div class="online-dot"></div>
            </div>
        </div>
        
        <div style="font-size: 18px; font-weight: bold;">{{ name }} <span style="color: var(--neon-green);">✔</span></div>
        <div style="color: var(--neon-green); font-size: 12px; margin-top: 2px;">● متصل الآن (VIP)</div>

        <div class="user-id-card">
            <div style="display: flex; justify-content: space-between;"><span>USERNAME:</span> <b>@{{ username }}</b></div>
            <div style="display: flex; justify-content: space-between;"><span>VIP ID:</span> <b>{{ user_id_code }}</b></div>
        </div>

        <div class="stats-grid">
            <div class="stat-box">
                <div class="stat-num">1</div>
                <div class="stat-label">صديق</div>
            </div>
            <div class="stat-box">
                <div class="stat-num">{{ visits }}</div>
                <div class="stat-label">زيارة</div>
            </div>
        </div>
    </div>

    <div class="tab-content" id="tab-settings">
        <div class="settings-menu">
            <div class="menu-item"><span>تعديل البروفايل</span> <span>›</span></div>
            <div class="menu-item"><span>خلفية الدردشة</span> <span>›</span></div>
            <div class="menu-item"><span>من زار بروفايلي</span> <span>›</span></div>
            <div class="menu-item"><span>الرسائل المجهولة</span> <span>›</span></div>
            <a href="/logout" class="menu-item danger">تسجيل الخروج</a>
        </div>
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
</script>
</body>
</html>
"""

@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template_string(
        MAIN_TEMPLATE,
        name=session.get('name'),
        username=session.get('username'),
        user_id_code=session.get('user_id_code'),
        visits=random.randint(5, 18)
    )

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
            session['user_id_code'] = user['user_id_code']
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
        socketio.emit('chat_broadcast', {
            'text': data['text'],
            'sender': session['name'],
            'username': session['username']
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)

