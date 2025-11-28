#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
游戏平台主应用

应用概述：
    这是一个基于Flask和Socket.IO的在线多人游戏平台，提供用户认证、房间管理、
    游戏加载与运行等核心功能。作为整个应用的入口点，该模块负责初始化所有组件，
    注册HTTP路由和WebSocket事件处理器。

主要功能：
    - Flask应用初始化与配置
    - Socket.IO实时通信支持
    - 用户认证与会话管理
    - 游戏房间的创建与管理
    - 游戏的动态加载与注册
    - RESTful API接口提供

技术栈：
    - Flask：Web应用框架
    - Flask-SocketIO：实时双向通信
    - JSON：数据交换格式
    - os：系统功能支持
"""

# 应用入口文件，负责初始化Flask应用和Socket.IO，注册路由和事件处理器

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import json
import os

# 导入平台模块
from platform.auth import init_users, register_user, login_user, update_user_room
from platform.socket_events import init_socket_events
from platform.room_manager import RoomManager
from games.game_registry import game_registry

# 初始化Flask应用
app = Flask(__name__)
# 配置Flask应用密钥，用于会话安全和Cookie签名
# 注意：生产环境中应使用强随机密钥并从环境变量加载
app.config['SECRET_KEY'] = 'your-secret-key'
# 配置JSON响应不使用ASCII编码，支持中文等非ASCII字符
app.config['JSON_AS_ASCII'] = False

# 初始化SocketIO实例，配置CORS以允许跨域请求
# 注意：生产环境中应限制允许的源为指定域名，而非通配符
# 参数说明：
#   - app: Flask应用实例
#   - cors_allowed_origins: 允许的跨域请求来源
socketio = SocketIO(app, cors_allowed_origins="*")

# 初始化游戏注册表，用于管理和加载所有游戏
# GameRegistry类负责动态发现、注册和实例化游戏
#game_registry = GameRegistry()
# 自动发现并注册所有可用游戏
# 该过程会扫描games目录下的所有游戏模块并注册
game_registry.initialize()

# 初始化房间管理器，用于创建和管理游戏房间
room_manager = RoomManager()

# 初始化用户数据，确保用户文件存在并包含必要字段
# 该函数检查用户数据文件并确保所有用户都有完整的字段结构
init_users()

# 初始化Socket事件处理，传入SocketIO实例和房间管理器
init_socket_events(socketio, room_manager)

@app.route('/')
def index():
    """
    主页面路由
    
    功能：
        返回网站首页，通常是登录页面
    
    返回值：
        渲染后的index.html模板
    
    路由参数：无
    
    模板位置：templates/index.html
    """
    return render_template('index.html')

@app.route('/register')
def register_page():
    print("渲染注册页面")
    return render_template('register.html')  # 注册页面

@app.route('/registerAPI', methods=['POST'])
def register():
    """
    用户注册API
    
    HTTP方法：POST
    路由：/register
    
    功能：
        接收用户注册信息，验证并创建新用户账号
        密码使用安全哈希算法加密存储
        验证输入的合法性和账号唯一性
    
    请求体格式(JSON)：
        {
            "account": "用户名",     # 必需，用于登录的账号名
            "password": "密码",       # 必需，用户密码
            "ID": "游戏昵称"         # 必需，游戏中显示的玩家名称
        }
    
    返回格式(JSON)：
        - 成功：{"ok": true, "msg": "注册成功"}
        - 失败：{"ok": false, "msg": "错误信息"}
        
    错误情况：
        - 缺少必要字段（用户名、密码或游戏ID）
        - 账号已存在
    """
    # 从请求中获取JSON数据
    data = request.json
    account = data.get('account')
    password = data.get('password')
    game_id = data.get('ID')  # 游戏昵称
    
    # 验证必要字段
    if not account or not password or not game_id:
        return jsonify({'ok': False, 'msg': '用户名、密码和游戏ID不能为空'})
    
    # 调用注册函数处理用户注册
    result = register_user(account, password, game_id)
    
    # 返回注册结果
    if result['ok']:
        return jsonify({'ok': True, 'msg': '注册成功'})
    else:
        return jsonify({'ok': False, 'msg': result['msg']})

@app.route('/login', methods=['POST'])
def login():
    """
    用户登录API
    
    HTTP方法：POST
    路由：/login
    
    功能：
        验证用户提供的账号和密码
        成功登录后返回用户基本信息和session token
    
    请求体格式(JSON)：
        {
            "account": "用户名",     # 必需，用户账号
            "password": "密码"       # 必需，用户密码
        }
    
    返回格式(JSON)：
        - 成功：
          {
              "ok": true,
              "msg": "登录成功",
              "token": "session_token",
              "user": {
                  "account": "账号",
                  "ID": "游戏昵称",
                  "room": "当前房间ID或null"
              }
          }
        - 失败：{"ok": false, "msg": "错误信息"}
        
    错误情况：
        - 缺少必要字段
        - 用户不存在
        - 密码错误
    """
    # 从请求中获取JSON数据
    data = request.json
    account = data.get('account')
    password = data.get('password')
    
    # 验证必要字段
    if not account or not password:
        return jsonify({'ok': False, 'msg': '用户名和密码不能为空'})
    
    # 调用登录函数验证用户
    result = login_user(account, password)
    
    # 返回登录结果
    if result['ok']:
        return jsonify({
            'ok': True, 
            'msg': '登录成功',
            'token': result['token'],  # 返回token
            'user': {
                'account': result['user']['account'],
                'ID': result['user']['ID'],
                'room': result['user']['room']
            }
        })
    else:
        return jsonify({'ok': False, 'msg': result['msg']})

@app.route('/available_games')
def available_games():
    """
    获取可用游戏列表API
    
    HTTP方法：GET
    路由：/available_games
    
    功能：
        获取平台上所有可用的游戏信息列表
        这些游戏是通过游戏注册表动态加载的
    
    参数：无
    
    返回格式(JSON)：
        {
            "games": [
                {
                    "id": "游戏唯一标识",
                    "name": "游戏名称",
                    "description": "游戏描述",
                    "min_players": 最小玩家数,
                    "max_players": 最大玩家数
                },
                ...
            ]
        }
    """
    # 从游戏注册表获取所有可用游戏
    games = game_registry.get_available_games()
    # 构造响应数据，每个游戏只返回必要信息
    game_list = []
    for game in games:
        game_list.append({
            'id': game['id'],
            'name': game['name'],
            'description': game['description'],
            'min_players': game['min_players'],
            'max_players': game['max_players']
        })
    return jsonify({'games': game_list})

@app.route('/rooms')
def rooms():
    """
    获取房间列表API
    
    HTTP方法：GET
    路由：/rooms
    
    功能：
        获取平台上所有活跃的游戏房间信息
        包括房间ID、房主、玩家列表、是否已选游戏等信息
    
    参数：无
    
    返回格式(JSON)：
        {
            "rooms": [
                {
                    "id": "房间ID",
                    "host": "房主账号",
                    "players": ["玩家账号列表"],
                    "game_selected": "已选游戏ID或null",
                    "started": 游戏是否已开始(布尔值)
                },
                ...
            ]
        }
    """
    room_list = []
    # 遍历所有房间，收集房间信息
    for room_id, room in room_manager.rooms.items():
        room_list.append({
            'id': room_id,
            'host': room.host_account,  # 房主账号
            'players': list(room.players.keys()),  # 所有玩家账号列表
            'game_selected': room.selected_game,  # 是否已选择游戏
            'started': room.game_started  # 游戏是否已开始
        })
    return jsonify({'rooms': room_list})

@app.route('/roulette')
def roulette():
    """
    Roulette游戏页面路由
    
    HTTP方法：GET
    路由：/roulette
    
    功能：
        渲染roulette游戏页面，用于测试前后端通信
        提供输入框和输出显示区域
    
    参数：无
    
    返回值：
        渲染后的roulette.html模板
    """
    print("访问了roulette路由")
    return render_template('roulette.html')


@app.route('/ccb')
def ccb():
    """
    ccb游戏页面路由
    
    HTTP方法：GET
    路由：/ccb
    
    功能：
        渲染ccb游戏页面，用于测试前后端通信
        提供输入框和输出显示区域
    
    参数：无
    
    返回值：
        渲染后的ccb.html模板
    """
    print("访问了ccb路由")
    return render_template('ccb.html')

if __name__ == '__main__':
    """
    应用程序入口点
    
    功能：
        - 确保必要目录存在
        - 启动SocketIO服务器
        - 开始处理HTTP请求和WebSocket连接
    
    服务器配置：
        - debug=True: 开启调试模式（开发环境使用）
        - host='0.0.0.0': 监听所有网络接口，允许外部访问
        - port=5000: 使用5000端口提供服务
    
    注意：
        - 生产环境中应关闭调试模式
        - 可能需要配置反向代理和Werkzeug服务器以外的WSGI服务器
    """
    # 确保static文件夹存在，用于存放静态资源
    if not os.path.exists('static'):
        os.makedirs('static')
    
    # 确保templates文件夹存在，用于存放HTML模板
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # 启动SocketIO服务器
    print("游戏平台启动中...")
    print(f"游戏数量: {len(game_registry.get_available_games())}")
    #socketio.run(app, debug=True, host='0.0.0.0', port=5000)
    socketio.run(app, debug=False, host='0.0.0.0', port=5000)
