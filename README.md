# IOBP1.0 游戏平台项目文档

## 项目概述

IOBP1.0 是一个基于 Flask 和 Socket.IO 开发的多人在线游戏平台，支持多用户同时在线进行游戏。平台采用模块化设计，将用户认证、房间管理和游戏逻辑清晰分离，便于扩展和维护。

## 项目结构

```
IOBP1.0_test/
├── app.py                      # 应用主入口文件
├── ccb.py                      # CCB游戏核心逻辑
├── platform/                   # 平台核心模块
│   ├── __init__.py
│   ├── auth.py                 # 用户认证模块
│   ├── room_manager.py         # 房间管理模块
│   └── socket_events.py        # Socket事件处理模块
├── games/                      # 游戏模块
│   ├── __init__.py
│   ├── base.py                 # 游戏基类
│   ├── game_registry.py        # 游戏注册表
│   └── ccb_game/               # CCB游戏模块目录
├── static/                     # 静态资源目录
│   ├── css/
│   ├── images/
│   └── js/
├── templates/                  # HTML模板目录
│   ├── games/
│   ├── index.html
│   ├── platform/
│   └── register.html
└── users.json                  # 用户数据存储文件
```

## 系统架构

系统采用三层架构设计：

1. **应用层**：由 `app.py` 负责初始化和协调各个模块
2. **平台层**：处理用户认证、房间管理和Socket事件
3. **游戏层**：实现游戏逻辑，基于游戏基类接口

### 核心流程图

1. **用户登录与房间创建流程**：
   - 用户注册/登录
   - 创建或加入房间
   - 选择游戏
   - 开始游戏

2. **游戏事件处理流程**：
   - 客户端发送游戏事件
   - Socket事件处理器接收并验证
   - 转发到对应的游戏实例处理
   - 广播游戏状态更新

## 模块详解

### 1. 应用入口 (app.py)

负责初始化Flask应用和Socket.IO，注册路由和事件处理器，是整个系统的入口点。

**主要功能**：
- 初始化应用配置和中间件
- 注册API路由
- 协调平台各模块
- 启动服务器

### 2. 认证模块 (platform/auth.py)

处理用户注册、登录和用户数据管理。

**主要功能**：
- 用户注册与账号验证
- 用户登录与密码校验
- 用户数据持久化存储
- 用户房间状态管理

### 3. 房间管理模块 (platform/room_manager.py)

管理游戏房间的创建、加入、离开等操作。

**主要功能**：
- 创建和维护游戏房间
- 管理房间内玩家
- 处理游戏选择和加载
- 协调游戏实例与房间的关系

### 4. Socket事件处理模块 (platform/socket_events.py)

处理实时通信相关的事件，是客户端与服务器交互的桥梁。

**主要功能**：
- 管理用户Socket会话
- 处理登录、房间操作事件
- 转发游戏特定事件
- 广播游戏状态更新

### 5. 游戏基类 (games/base.py)

定义所有游戏必须实现的接口，提供游戏框架。

**主要功能**：
- 定义游戏核心接口
- 提供游戏状态管理基础
- 规定游戏事件处理方法

### 6. 游戏注册表 (games/game_registry.py)

负责游戏的自动发现、注册和实例创建。

**主要功能**：
- 自动扫描并注册游戏模块
- 维护游戏信息列表
- 根据游戏ID创建游戏实例

### 7. CCB游戏 (ccb.py)

一个策略战棋类游戏的实现，支持多人对战和AI对手。

**主要功能**：
- 地图管理和游戏状态维护
- 玩家回合制游戏逻辑
- 单位放置和移动规则
- AI机器人对手

## 核心API

### 认证相关API

- `POST /register` - 用户注册
- `POST /login` - 用户登录

### 游戏平台API

- `GET /available_games` - 获取可用游戏列表
- `GET /rooms` - 获取房间列表

### Socket事件

#### 用户相关
- `login` - 用户登录

#### 房间相关
- `create_room` - 创建房间
- `join_room` - 加入房间
- `leave_room` - 离开房间
- `select_game` - 选择游戏
- `start_game` - 开始游戏

#### 游戏相关
- `game_event` - 处理游戏事件

## 数据结构

### 用户数据
```json
{
  "account": "用户名",
  "ID": "游戏昵称",
  "password": "加密密码",
  "room": "所在房间ID或null"
}
```

### 房间数据
```json
{
  "room_id": "房间ID",
  "host_account": "房主账号",
  "players": {"account": "玩家信息"},
  "selected_game": "已选择游戏ID",
  "game_started": "游戏是否已开始"
}
```

### 游戏信息
```json
{
  "id": "游戏ID",
  "name": "游戏名称",
  "description": "游戏描述",
  "min_players": 最小玩家数,
  "max_players": 最大玩家数,
  "class": "游戏类"
}
```

## 技术栈

- **后端框架**: Flask + Flask-SocketIO
- **数据存储**: JSON文件存储
- **实时通信**: Socket.IO
- **密码加密**: Werkzeug Security

## 部署说明

1. 安装依赖：
```bash
pip install flask flask-socketio werkzeug
```

2. 启动服务：
```bash
python app.py
```

服务将在 http://0.0.0.0:5000 启动。

## 扩展指南

### 添加新游戏

1. 在 `games/` 目录下创建新游戏文件夹
2. 创建 `game.py` 文件，实现游戏类并继承 `BaseGame`
3. 实现 `register_game()` 函数注册游戏信息
4. 游戏将被自动发现并注册到平台

## 开发注意事项

1. 确保所有游戏类都实现了 `BaseGame` 接口
2. 密码存储使用 Werkzeug 的 `generate_password_hash` 函数
3. Socket事件处理需要验证用户登录状态
4. 游戏实例状态需要定期广播给房间内所有玩家