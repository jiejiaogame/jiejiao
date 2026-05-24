# friend.py - 完整好友系统（支持实时通知、日志面板带按钮）
import sqlite3
import json
from datetime import datetime
from core import DB_PATH, users_ws

def init_friend_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS friendships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user1 TEXT NOT NULL,
        user2 TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at TEXT,
        updated_at TEXT,
        UNIQUE(user1, user2)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS game_invites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_user TEXT NOT NULL,
        to_user TEXT NOT NULL,
        room_id TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT,
        expires_at TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS private_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_user TEXT NOT NULL,
        to_user TEXT NOT NULL,
        message TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        is_read INTEGER DEFAULT 0
    )''')
    conn.commit()
    conn.close()

init_friend_db()

def get_friends(username):
    """获取好友列表（已接受的）"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT 
            CASE WHEN user1 = ? THEN user2 ELSE user1 END as friend,
            status,
            created_at
        FROM friendships 
        WHERE (user1 = ? OR user2 = ?) AND status = 'accepted'
    """, (username, username, username))
    rows = c.fetchall()
    conn.close()
    
    friends = []
    for row in rows:
        friend_name = row[0]
        is_online = friend_name in users_ws
        # 获取好友头像
        from core import get_user
        user = get_user(friend_name)
        avatar = user.get("avatar", "hero.png") if user else "hero.png"
        friends.append({
            "name": friend_name,
            "online": is_online,
            "since": row[2],
            "avatar": avatar
        })
    return friends

def get_pending_requests(username):
    """获取收到的好友申请"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT user1, created_at
        FROM friendships 
        WHERE user2 = ? AND status = 'pending'
    """, (username,))
    rows = c.fetchall()
    conn.close()
    return [{"from": row[0], "time": row[1]} for row in rows]

def get_sent_requests(username):
    """获取已发送的好友申请"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT user2, created_at
        FROM friendships 
        WHERE user1 = ? AND status = 'pending'
    """, (username,))
    rows = c.fetchall()
    conn.close()
    return [{"to": row[0], "time": row[1]} for row in rows]

async def send_friend_request(from_user, to_user):
    """发送好友申请（异步，支持 WebSocket 推送）"""
    if from_user == to_user:
        return {"success": False, "msg": "不能添加自己为好友"}
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT status FROM friendships 
        WHERE (user1 = ? AND user2 = ?) OR (user1 = ? AND user2 = ?)
    """, (from_user, to_user, to_user, from_user))
    existing = c.fetchone()
    
    if existing:
        if existing[0] == "accepted":
            conn.close()
            return {"success": False, "msg": "已经是好友了"}
        elif existing[0] == "pending":
            conn.close()
            return {"success": False, "msg": "已发送过好友申请"}
    
    now = datetime.now().isoformat()
    c.execute("""
        INSERT INTO friendships (user1, user2, status, created_at, updated_at)
        VALUES (?, ?, 'pending', ?, ?)
    """, (from_user, to_user, now, now))
    conn.commit()
    conn.close()
    
    # 如果对方在线，通过 WebSocket 发送实时通知（带申请详情）
    if to_user in users_ws:
        try:
            await users_ws[to_user].send_text(json.dumps({
                "type": "friend_request",
                "from": from_user,
                "msg": f"📨 {from_user} 请求添加你为好友"
            }))
        except:
            pass
    
    return {"success": True, "msg": "好友申请已发送"}

def accept_friend_request(username, from_user):
    """同意好友请求，并通知双方刷新列表"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute("""
        UPDATE friendships 
        SET status = 'accepted', updated_at = ?
        WHERE user1 = ? AND user2 = ? AND status = 'pending'
    """, (now, from_user, username))
    affected = c.rowcount
    conn.commit()
    conn.close()
    
    if affected > 0:
        # 通知双方刷新好友列表
        import asyncio
        if from_user in users_ws:
            asyncio.create_task(users_ws[from_user].send_text(json.dumps({
                "type": "friend_list_update"
            })))
        if username in users_ws:
            asyncio.create_task(users_ws[username].send_text(json.dumps({
                "type": "friend_list_update"
            })))
        return {"success": True, "msg": "已添加好友"}
    return {"success": False, "msg": "好友申请不存在"}

def reject_friend_request(username, from_user):
    """拒绝好友请求"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        DELETE FROM friendships 
        WHERE user1 = ? AND user2 = ? AND status = 'pending'
    """, (from_user, username))
    affected = c.rowcount
    conn.commit()
    conn.close()
    
    if affected > 0:
        return {"success": True, "msg": "已拒绝好友申请"}
    return {"success": False, "msg": "好友申请不存在"}

def delete_friend(username, friend_name):
    """删除好友"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        DELETE FROM friendships 
        WHERE (user1 = ? AND user2 = ? OR user1 = ? AND user2 = ?) AND status = 'accepted'
    """, (username, friend_name, friend_name, username))
    affected = c.rowcount
    conn.commit()
    conn.close()
    
    if affected > 0:
        # 通知双方刷新好友列表
        import asyncio
        if friend_name in users_ws:
            asyncio.create_task(users_ws[friend_name].send_text(json.dumps({
                "type": "friend_list_update"
            })))
        if username in users_ws:
            asyncio.create_task(users_ws[username].send_text(json.dumps({
                "type": "friend_list_update"
            })))
        return {"success": True, "msg": "已删除好友"}
    return {"success": False, "msg": "好友不存在"}

# 发送私聊消息（离线存储）
def send_private_message(from_user, to_user, message):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute("""
        INSERT INTO private_messages (from_user, to_user, message, timestamp, is_read)
        VALUES (?, ?, ?, ?, 0)
    """, (from_user, to_user, message, now))
    conn.commit()
    conn.close()
    
    # 如果对方在线，实时推送
    if to_user in users_ws:
        import asyncio
        asyncio.create_task(users_ws[to_user].send_text(json.dumps({
            "type": "private_msg",
            "from": from_user,
            "msg": message,
            "timestamp": now
        })))
    return {"success": True}

# 获取未读私聊消息
def get_unread_messages(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT id, from_user, message, timestamp
        FROM private_messages 
        WHERE to_user = ? AND is_read = 0
        ORDER BY timestamp ASC
    """, (username,))
    rows = c.fetchall()
    # 标记为已读
    for row in rows:
        c.execute("UPDATE private_messages SET is_read = 1 WHERE id = ?", (row[0],))
    conn.commit()
    conn.close()
    return [{"from": row[1], "msg": row[2], "time": row[3]} for row in rows]