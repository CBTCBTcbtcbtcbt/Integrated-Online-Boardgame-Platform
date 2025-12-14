#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
平台认证模块

模块概述：
    负责用户身份验证和会话管理，提供用户注册、登录、信息查询和房间状态更新等核心功能。
    用户数据使用JSON文件持久化存储，密码采用安全哈希算法加密。

主要功能：
    - 用户注册与账号创建
    - 用户登录与身份验证
    - 用户信息查询
    - 用户房间状态管理
    - HTTP认证路由提供

技术细节：
    - 使用werkzeug.security进行密码加密和验证
    - 用户数据存储在JSON文件中
    - 提供RESTful API接口供前端调用
"""

# 负责用户注册、登录和会话管理功能

from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
import secrets
from datetime import datetime, timedelta

# 用户数据文件路径
# 该文件存储所有用户账号信息，包括加密后的密码和用户属性
USER_FILE = "users.json"

# Token存储 (在内存中管理所有活跃的session tokens)
active_tokens = {}  # {token: {"account": account, "created_at": datetime, "expires_at": datetime}}
user_tokens = {}  # {account: token} - 用于快速查找用户的当前token

def init_users():
    """
    初始化用户数据文件和结构
    
    功能概述：
        确保用户数据文件存在并验证所有用户记录的完整性，特别是room字段
        这是应用启动时的初始化步骤，保证数据结构一致性
    
    处理流程：
        1. 检查用户数据文件是否存在，不存在则创建空文件
        2. 从文件加载现有用户数据
        3. 遍历所有用户记录，确保每个用户都有room字段
        4. 如果进行了字段补充，将更新后的数据保存回文件
    
    日志输出：
        - 创建新文件时记录日志
        - 更新用户数据结构时记录日志
    
    返回值：无
    """
    if not os.path.exists(USER_FILE):
        # 如果文件不存在，创建空文件
        with open(USER_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=4, ensure_ascii=False)
        print(f"创建新的用户数据文件: {USER_FILE}")
        return
    
    # 读取并更新用户数据
    with open(USER_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 确保每个用户都有room字段
    for user in data.values():
        user['room'] = None
    
    # 如果有更新，保存更新后的数据
    with open(USER_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print("用户数据结构已更新，确保所有用户都没有房间字段")

def load_users():
    """
    从users.json文件中读取所有用户信息
    
    返回值：
        dict: 用户信息字典，键为账号，值为用户详细信息
              如果文件不存在或格式错误，返回空字典
    
    核心作用：
        - 提供统一的用户数据加载接口，抽象文件操作细节
        - 异常处理确保系统稳定性
        - 日志记录便于调试和监控
    
    异常处理：
        - 文件不存在时返回空字典
        - JSON格式错误时返回空字典并记录警告日志
    
    日志输出：
        - 成功加载时显示用户数量
        - 文件不存在或格式错误时显示错误信息
    """
    if not os.path.exists(USER_FILE):
        print(f"用户数据文件不存在: {USER_FILE}")
        return {}  # 若文件不存在，返回空字典
    
    try:
        with open(USER_FILE, "r", encoding="utf-8") as f:
            users_data = json.load(f)
        print(f"成功加载用户数据，共 {len(users_data)} 个用户")
        return users_data
    except json.JSONDecodeError as e:
        print(f"警告: 用户数据文件格式错误 - {str(e)}")
        return {}  # 若文件损坏或格式错误，返回空字典

def save_users(users):
    """
    将内存中的用户数据保存回users.json文件
    
    参数：
        users (dict): 用户信息字典，包含所有需要持久化的用户数据
    
    核心作用：
        - 确保用户数据的持久化存储
        - 格式化JSON输出，提高文件可读性和可维护性
        - 异常处理确保程序稳定性
    
    技术特点：
        - 使用utf-8编码确保中文字符正确保存
        - 缩进为4的JSON格式，提高可读性
    
    异常处理：
        - 捕获可能的写入异常，记录错误日志但不中断程序
    
    日志输出：
        - 成功保存时显示用户数量
        - 保存失败时显示错误信息
    
    返回值：无
    """
    try:
        with open(USER_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=4, ensure_ascii=False)
        print(f"用户数据已保存，共 {len(users)} 个用户")
    except Exception as e:
        print(f"保存用户数据失败: {str(e)}")

def register_user(account, password, game_id):
    """
    注册新用户账号
    
    参数：
        account (str): 用户账号，用于登录系统的唯一标识
        password (str): 用户密码，用于身份验证
        game_id (str): 游戏ID（玩家昵称），在游戏中显示给其他玩家
    
    返回值：
        dict: 注册结果字典
            {"ok": bool, "msg": str}
            - ok: 注册是否成功
            - msg: 操作结果描述信息
    
    功能流程：
        1. 验证输入参数的完整性（账号、密码、游戏ID不能为空）
        2. 加载现有用户数据，检查账号是否已存在
        3. 如果账号可用，使用安全哈希算法加密密码
        4. 创建新用户记录，设置初始房间状态为None
        5. 保存更新后的用户数据到文件
    
    安全特性：
        - 密码使用PBKDF2-SHA256算法加密存储
        - 不存储明文密码
    
    日志输出：
        - 记录注册尝试和结果（成功/失败原因）
    """
    # 基本输入校验
    if not account or not password or not game_id:
        print("注册失败: 账号、密码或游戏ID为空")
        return {"ok": False, "msg": "账号、密码和ID不能为空"}
    
    users = load_users()
    
    # 检查账号是否已存在
    if account in users:
        print(f"注册失败: 账号 {account} 已存在")
        return {"ok": False, "msg": "账号已存在"}
    
    # 创建新用户，密码加密存储
    users[account] = {
        "account": account,
        "ID": game_id,
        "password": generate_password_hash(password, method="pbkdf2:sha256"),  # 使用安全哈希存储密码
        "room": None  # 初始未在任何房间
    }
    
    # 保存用户数据
    save_users(users)
    
    print(f"新用户注册成功: 账号={account}, 游戏ID={game_id}")
    return {"ok": True, "msg": "注册成功"}

def generate_session_token():
    """
    生成安全的随机session token
    
    返回值：
        str: 32字节的URL安全随机token字符串
    
    安全特性：
        - 使用secrets模块生成密码学安全的随机数
        - URL安全的base64编码，适合在HTTP中传输
    """
    return secrets.token_urlsafe(32)

def create_token(account):
    """
    为用户创建新的session token
    
    参数：
        account (str): 用户账号
    
    返回值：
        str: 生成的session token
    
    功能流程：
        1. 如果用户已有token，先删除旧token
        2. 生成新的随机token
        3. 设置token过期时间（7天）
        4. 将token信息存储到active_tokens字典
        5. 更新user_tokens映射以便快速查找
    
    日志输出：
        - 记录为哪个用户创建了新token
    """
    # 如果用户已有token，先删除旧token
    if account in user_tokens:
        old_token = user_tokens[account]
        if old_token in active_tokens:
            del active_tokens[old_token]
    
    # 生成新token
    token = generate_session_token()
    expires_at = datetime.now() + timedelta(days=7)  # token 7天后过期
    
    active_tokens[token] = {
        "account": account,
        "created_at": datetime.now(),
        "expires_at": expires_at
    }
    user_tokens[account] = token
    
    print(f"为用户 {account} 创建新token")
    return token

def verify_token(token):
    """
    验证token是否有效
    
    参数：
        token (str): 要验证的session token
    
    返回值：
        str|None: 如果token有效返回对应的账号，否则返回None
    
    功能流程：
        1. 检查token是否存在于active_tokens中
        2. 检查token是否已过期
        3. 如果过期，删除相关记录
        4. 如果有效，返回对应的账号
    
    日志输出：
        - 记录token过期和删除的情况
    """
    if not token or token not in active_tokens:
        return None
    
    token_info = active_tokens[token]
    
    # 检查是否过期
    if datetime.now() > token_info["expires_at"]:
        # Token已过期，删除它
        account = token_info["account"]
        del active_tokens[token]
        if account in user_tokens and user_tokens[account] == token:
            del user_tokens[account]
        print(f"Token已过期并被删除")
        return None
    
    return token_info["account"]

def revoke_token(token):
    """
    撤销token (用于登出)
    
    参数：
        token (str): 要撤销的session token
    
    返回值：
        bool: 是否成功撤销
    
    功能流程：
        1. 检查token是否存在
        2. 删除active_tokens中的记录
        3. 删除user_tokens中的映射
    
    日志输出：
        - 记录token撤销操作
    """
    if token in active_tokens:
        account = active_tokens[token]["account"]
        del active_tokens[token]
        if account in user_tokens and user_tokens[account] == token:
            del user_tokens[account]
        print(f"Token已撤销: 用户 {account}")
        return True
    return False

def login_user(account, password):
    """
    用户登录验证
    
    参数：
        account (str): 用户账号
        password (str): 用户密码
    
    返回值：
        dict: 登录结果字典
            {
                "ok": bool,      # 登录是否成功
                "msg": str,      # 操作结果描述信息
                "user": dict,    # 成功时包含用户信息（不含密码）
                "token": str     # 成功时包含session token
            }
    
    功能流程：
        1. 加载所有用户数据
        2. 检查指定账号是否存在于系统中
        3. 使用哈希验证函数检查密码是否匹配
        4. 登录成功时，生成session token
        5. 构建包含公开信息的用户数据（排除密码等敏感信息）
    
    安全特性：
        - 使用check_password_hash验证密码，防止时序攻击
        - 返回数据中不包含密码等敏感信息
        - 生成随机session token用于后续认证
    
    日志输出：
        - 记录登录尝试和结果，包括成功/失败原因
        - 记录登录用户的基本信息（账号、游戏ID、当前房间）
    """
    users = load_users()
    user = users.get(account)
    
    # 检查用户是否存在
    if not user:
        print(f"登录失败: 用户 {account} 不存在")
        return {"ok": False, "msg": "用户不存在"}
    
    # 检查密码是否正确
    if not check_password_hash(user["password"], password):
        print(f"登录失败: 用户 {account} 密码错误")
        return {"ok": False, "msg": "密码错误"}
    
    # 生成session token
    token = create_token(account)
    
    # 登录成功，构建安全的用户信息返回（不包含密码）
    user_info = {
        "account": account,
        "ID": user["ID"],
        "room": user.get("room")
    }
    
    print(f"用户登录成功: 账号={account}, 游戏ID={user['ID']}, 当前房间={user.get('room', '无')}")
    return {
        "ok": True,
        "msg": "登录成功",
        "user": user_info,
        "token": token  # 返回token给前端
    }

def update_user_room(account, room):
    """
    更新用户所在房间信息
    
    参数：
        account (str): 用户账号
        room (str|None): 房间号，可以是具体房间ID或None（表示离开房间）
    
    返回值：
        bool: 是否更新成功
    
    核心作用：
        - 维护用户与房间的关联状态
        - 当用户加入或离开房间时更新其状态
        - 支持房间管理系统的状态同步
    
    功能流程：
        1. 加载现有用户数据
        2. 检查用户账号是否存在
        3. 记录用户之前所在的房间（如果有）
        4. 更新用户的room字段为新值
        5. 保存更新后的用户数据
    
    日志输出：
        - 记录用户房间变更（从哪个房间到哪个房间）
        - 更新失败时记录错误信息
    """
    users = load_users()
    if account in users:
        old_room = users[account].get("room")
        users[account]["room"] = room
        save_users(users)
        print(f"更新用户房间: 账号={account}, 从房间={old_room}到房间={room}")
        return True
    print(f"更新用户房间失败: 账号={account}不存在")
    return False

def get_user(account):
    """
    获取用户完整信息
    
    参数：
        account (str): 用户账号
    
    返回值：
        dict|None: 完整用户信息字典，如果用户不存在返回None
                   注意：返回的字典包含密码哈希等敏感信息，仅用于内部系统
    
    核心作用：
        - 提供用户数据查询接口
        - 支持内部系统的用户验证和状态检查
    
    安全注意事项：
        - 返回的信息包含敏感数据（如密码哈希）
        - 该函数应仅用于内部系统，不应在API响应中直接返回其结果
    
    日志输出：
        - 记录用户信息查询操作和结果
    """
    users = load_users()
    user = users.get(account)
    if user:
        print(f"获取用户信息: 账号={account}, 游戏ID={user['ID']}, 完整信息={user}")
    else:
        print(f"获取用户信息失败: 账号={account}不存在")
    return user

'''def init_auth_routes(app):
    
    """
    初始化认证相关HTTP路由
    
    参数：
        app (Flask): Flask应用实例
    
    核心作用：
        - 向Flask应用注册用户认证相关的HTTP端点
        - 将路由处理函数与业务逻辑函数连接
        - 提供RESTful API接口供前端调用
    
    路由说明：
        - /register: 用户注册接口
        - 可扩展添加其他认证相关路由
    
    设计模式：
        - 装饰器模式注册路由
        - 闭包函数封装路由逻辑
    """
    @app.route("/register", methods=["POST"])
    def register():
        """
        用户注册HTTP接口
        
        HTTP方法: POST
        路径: /register
        内容类型: application/json
        
        请求体格式(JSON):
        {
            "account": "用户名",     # 必需，登录账号
            "password": "密码",       # 必需，用户密码
            "ID": "游戏昵称"         # 必需，游戏内显示名称
        }
        
        响应格式(JSON):
            成功: {"ok": true, "msg": "注册成功"}
            失败: {"ok": false, "msg": "错误信息"}
        
        功能流程：
            1. 从HTTP请求中提取JSON格式的注册数据
            2. 记录收到的注册请求（日志）
            3. 调用register_user业务逻辑函数处理注册
            4. 将处理结果以JSON格式返回给客户端
        
        错误处理：
            - 所有业务逻辑错误由register_user函数处理并返回
            - 响应统一使用jsonify确保正确的HTTP头部和JSON格式
        """
        # 从请求中获取数据
        data = request.json
        account = data.get("account")
        password = data.get("password")
        game_id = data.get("ID")
        
        print(f"收到注册请求: 账号={account}, 游戏ID={game_id}")
        
        # 调用注册函数
        result = register_user(account, password, game_id)
        
        # 返回结果
        return jsonify(result)


'''
