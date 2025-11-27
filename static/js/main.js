// ================================
// main.js
// 登录 / 房间管理 + 游戏主逻辑（与 index.html 配合使用）
// ================================

// 初始化 Socket.IO 客户端，携带token
var token = localStorage.getItem('session_token');
const socket = io();
console.log('main.js loaded, socket.io connected with token');

// 平台 & 房间相关全局状态
let currentUser = null;   // 当前用户信息 { account, ID, room, password }
let currentRoom = null;   // 当前所在房间号
let currentGame = null;   // 当前游戏ID
let gameState = null;     // 当前游戏状态

// 游戏相关全局状态
let myOrder = null;       // 玩家在游戏中的编号（暂未使用）
let players = {};         // 当前房间的所有玩家信息
let account = null;       // 当前登录账号（用于在游戏中索引玩家）
let playerID = null;      // 当前玩家ID（显示在游戏中，暂未使用）

// ================================
// DOM 事件绑定（登录 / 房间 / 游戏控制）
// ================================

$(document).ready(() => {
  // 登录按钮
  $('#login-btn').click(() => {
    const acc = $('#login-account').val();
    const pwd = $('#login-password').val();

    if (!acc || !pwd) {
      $('#login-message').text('账号和密码不能为空');
      return;
    }

    socket.emit('login', { account: acc, password: pwd });
  });

  // 跳转注册
  $('#show-register-btn').click(() => {
    location.href = '/register';
  });

  // 创建房间按钮
  $('#create-room-btn').click(() => {
    $('#room-hall').hide();
    $('#create-room-panel').show();
  });

  // 取消创建房间
  $('#cancel-create-room-btn').click(() => {
    $('#create-room-panel').hide();
    $('#room-hall').show();
  });

  // 提交创建房间
  $('#create-room-submit-btn').click(() => {
    const roomId = $('#create-room-id').val();

    if (!roomId) {
      $('#create-room-message').text('房间ID不能为空');
      return;
    }
    console.log(`token = ${token}`);
    socket.emit('create_room', { room_id: roomId, token: token });
  });

  // 加入已有房间入口
  $('#join-existing-room-btn').click(() => {
    $('#room-hall').hide();
    $('#join-room-panel').show();
  });

  // 取消加入房间
  $('#cancel-join-room-btn').click(() => {
    $('#join-room-panel').hide();
    $('#room-hall').show();
  });

  // 提交加入房间
  $('#join-room-btn').click(() => {
    const roomId = $('#join-room-id').val();

    if (!roomId) {
      $('#join-room-message').text('房间ID不能为空');
      return;
    }
    console.log(`token = ${token}`);
    socket.emit('join_room', { room_id: roomId, token: token });
  });

  // 选择游戏（不再传 room_id，由后端根据当前用户推断房间）
  $('#select-game-btn').click(() => {
    const gameId = $('#game-select').val();

    if (!gameId) {
      $('#room-message').text('请选择游戏');
      return;
    }

    socket.emit('select_game', { game_id: gameId, token: token });
  });

  // 开始游戏（房主，不再传 room_id）
  $('#start-game-btn').click(() => {
    socket.emit('start_game', { token: token });
  });

  // 离开房间（不再传 room_id）
  $('#leave-room-btn').click(() => {
    socket.emit('leave_room', { token: token });
  });

  // 退出游戏（本质上也是离开房间，不再传 room_id）
  $('#exit-game-btn').click(() => {
    socket.emit('leave_room', { token: token });
  });

  // 退出登录
  $('#logout-btn').click(() => {
    // 清除token和用户信息
    localStorage.removeItem('session_token');
    localStorage.removeItem('user');
    currentUser = null;
    account = null;
    window.location.reload();
  });

  // 跳过回合按钮（游戏操作）
  $('#btnSkip').click(() => {
    // 前端直接封装为游戏内部统一格式：event_name + event_data
    socket.emit('game_event', {
      token: token,
      event_name: 'skip_turn',
      event_data: {}
    });
  });
});

// ================================
// Socket 事件：登录 / 房间 / 平台逻辑
// ================================

// 登录响应
socket.on('login_response', (data) => {
  if (data.ok) {
    // 保存token到localStorage
    if (data.token) {
      localStorage.setItem('session_token', data.token);
    }
    token = localStorage.getItem('session_token');
    console.log(`token = ${token}`);
    // 登录成功
    currentUser = {
      account: data.account,
      ID: data.ID,
      room: data.room,
      password: $('#login-password').val() // 存储密码用于自动重连
    };

    account = data.account; // 用于游戏中根据账号索引玩家

    // 保存到本地存储
    localStorage.setItem('user', JSON.stringify(currentUser));

    // 隐藏登录面板
    $('#login-panel').hide();

    // 如果用户已经在房间中，直接加入房间
      loadAvailableRooms();
      $('#current-account').text(data.account);
      $('#room-hall').show();
    
  } else {
    // 登录失败
    $('#login-message').text(data.msg);
  }
});

// 创建房间响应
socket.on('create_room_response', (data) => {
  if (data.ok) {
    currentRoom = data.room_id;
    $('#create-room-panel').hide();
    // 加载可用游戏
    loadAvailableGames();
    $('#room-panel').show();
  } else {
    $('#create-room-message').text(data.msg);
  }
});

// 加入房间响应
socket.on('join_room_response', (data) => {
  if (data.ok) {
    currentRoom = data.room_id;
    $('#join-room-panel').hide();
    // 加载可用游戏
    loadAvailableGames();
    $('#room-panel').show();
  } else {
    $('#join-room-message').text(data.msg);
  }
});

// 房间信息更新
socket.on('room_info_updated', (data) => {
  if (data.room_id === currentRoom) {
    $('#current-room-id').text(data.room_id);
    $('#current-room-host').text(data.host);

    // 更新玩家列表
    const playersList = $('#current-room-players');
    playersList.empty();
    Object.keys(data.players).forEach(accountKey => {
      const player = data.players[accountKey];
      playersList.append(`<li>${player.ID}${accountKey === data.host ? ' (房主)' : ''}</li>`);
    });

    // 更新游戏选择
    if (data.selected_game) {
      $('#game-select').val(data.selected_game);
    }

    // 更新开始游戏按钮状态
    if (data.host === currentUser.account && data.selected_game) {
      $('#start-game-btn').prop('disabled', false);
    } else {
      $('#start-game-btn').prop('disabled', true);
    }
  }
});

// 游戏选择响应
socket.on('select_game_response', (data) => {
  if (data.ok) {
    $('#room-message').removeClass('message').addClass('success-message');
    $('#room-message').text('游戏选择成功');
    // 房主可以开始游戏
    if (currentUser && currentUser.account === $('#current-room-host').text()) {
      $('#start-game-btn').prop('disabled', false);
    }
  } else {
    $('#room-message').text(data.msg);
  }
});

// 游戏选择广播
socket.on('game_selected', (data) => {
  if (data.room_id === currentRoom) {
    $('#game-select').val(data.game_id);
    // 房主可以开始游戏
    if (currentUser && currentUser.account === $('#current-room-host').text()) {
      $('#start-game-btn').prop('disabled', false);
    }
  }
});

// 开始游戏响应
socket.on('start_game_response', (data) => {
  if (!data.ok) {
    $('#room-message').text(data.msg);
  }
});

// 离开房间响应
socket.on('leave_room_response', (data) => {
  if (data.ok) {
    currentRoom = null;
    currentGame = null;
    gameState = null;
    players = {};

    // 显示房间大厅
    loadAvailableRooms();
    $('#room-panel').hide();
    $('#game').hide();
    $('#room-hall').show();
  }
});

// ================================
// 游戏相关事件 & 核心逻辑（棋盘、回合等）
// ================================

// 点击棋盘格子下棋
function onCellClick(e) {
  const y = e.target.dataset.y;
  const x = e.target.dataset.x;

  const pieceType = document.getElementById('selPiece')?.value || 1;
  console.log("click,", x, y, pieceType);
  // 前端直接封装为游戏内部统一格式：event_name + event_data
  socket.emit('game_event', {
    token: token,
    event_name: 'place',
    event_data: {
      ptype: Number(pieceType),
      row: Number(y),
      col: Number(x)
    }
  });
}

// 下棋结果
socket.on('game_event_result', d => {
  const cmdInfo = document.getElementById('cmdInfo');
  if (cmdInfo) {
    cmdInfo.innerText = d.msg || '';
  }
});

// 回合结束
socket.on('turn_ended', d => {
  if (d.turn && d.players) {
    players = d.players;
    renderTurn(d.turn, d.players);
  }
});

// 棋盘更新
socket.on('board_update', d => {
  if (d.players) {
    players = d.players;
  }
  if (d.board) {
    renderBoard(d.board);
  }
  if (d.turn && d.players) {
    renderTurn(d.turn, d.players);
  }
});

// 游戏开始广播（整合原 login.js 与 main.js 的处理）
socket.on('game_started', d => {
  console.log('游戏开始:', d);
    
    // 如果有跳转URL，执行页面跳转
    if (d.redirect_url) {
        window.location.href = d.redirect_url;
    }

  currentRoom = d.room_id || currentRoom;
  currentGame = d.game_id;
  gameState = d.game_state;

  // 切换到游戏界面
  $('#room-panel').hide();
  $('#game').show();
  $('#current-game-name').text('CCB战棋');

  if (d.game_state) {
    if (d.game_state.players) {
      players = d.game_state.players;
    }
    if (d.game_state.board) {
      renderBoard(d.game_state.board);
    }
    if (d.game_state.turn) {
      renderTurn(d.game_state.turn, d.game_state.players || players);
    }
  }
});

// 游戏状态更新（整合原 login.js 与 main.js 的处理）
socket.on('game_state_updated', d => {
  if (d.room_id && currentRoom && d.room_id !== currentRoom) return;

  if (d.game_state) {
    gameState = d.game_state;

    if (d.game_state.players) {
      players = d.game_state.players;
    }
    if (d.game_state.board) {
      renderBoard(d.game_state.board);
    }
    if (d.game_state.turn) {
      renderTurn(d.game_state.turn, d.game_state.players || players);
    }
  }
});

// 渲染棋盘
function renderBoard(board) {
  const tbl = document.getElementById('board');
  if (!tbl) return; // 如果没有找到棋盘元素，直接返回

  tbl.innerHTML = '';

  if (!board || board.length === 0) {
    console.warn('Empty board data received');
    return;
  }

  // 当前玩家的可见范围（若服务器有返回）
  const currentPlayer = players && account ? players[account] : null;
  const visibleRange = currentPlayer ? currentPlayer[7] : null; // 第8个元素是可见范围

  for (let i = 0; i < board.length; i++) {
    const tr = document.createElement('tr');
    for (let j = 0; j < board[i].length; j++) {
      const td = document.createElement('td');
      td.dataset.y = i;
      td.dataset.x = j;

      let cell;
      try {
        cell = Array.isArray(board[i]) && Array.isArray(board[i][j]) ? board[i][j] : [0, 0];
      } catch (e) {
        console.error('Error accessing board cell:', e);
        cell = [0, 0];
      }

      const isVisible = visibleRange && Array.isArray(visibleRange[i]) && visibleRange[i][j] === 1;

      if (!isVisible) {
        // 不可见的格子显示为灰色
        td.innerText = '';
        td.className = 'fog-cell';
        td.style.backgroundColor = 'gray';
      } else {
        const owner = cell[0] || 0;
        const type = cell[1] || 0;

        if (owner !== 0) {
          td.className = 'p' + owner; // 根据玩家染色
        }

        switch (type) {
          case 1:
            td.innerText = '步兵';
            break;
          case 2:
            td.innerText = '坦克';
            break;
          case 3:
            td.innerText = '炸机';
            break;
          case 4:
            td.innerText = '战机';
            break;
          case 5:
            td.innerText = '城市';
            td.className = 'pp' + owner;
            break;
          case 6:
            td.innerText = '核井';
            break;
          case 7:
            td.innerText = '指挥';
            break;
          default:
            td.innerText = '';
        }
      }

      td.addEventListener('click', onCellClick);
      tr.appendChild(td);
    }
    tbl.appendChild(tr);
  }
}

// 显示当前回合信息与指挥点
function renderTurn(turn, pls) {
  const info = document.getElementById('turnInfo');
  if (info) {
    info.innerText = `第${turn[1]}轮，轮到 #${turn[0]} 玩家`;
  }
  const cmdInfo = document.getElementById('cmdInfo');
  if (cmdInfo) {
    cmdInfo.innerText = ` 指挥点：${pls && account && pls[account] ? (pls[account][2] || 0) : 0}`;
  }
}

// ================================
// 辅助函数：加载房间 / 游戏列表
// ================================

// 加载可用房间列表
function loadAvailableRooms() {
  $.ajax({
    url: '/rooms',
    type: 'GET',
    success: (response) => {
      const roomList = $('#room-list');
      roomList.empty();

      if (!response.rooms || response.rooms.length === 0) {
        roomList.append('<p>暂无房间，请创建新房间</p>');
      } else {
        response.rooms.forEach(room => {
          if (!room.started) { // 只显示未开始的房间
            const roomItem = $('<div class="room-item"></div>');
            roomItem.html(`
              <div>房间ID: ${room.id}</div>
              <div>房主: ${room.host}</div>
              <div>玩家: ${room.players.length}/4</div>
              <div>游戏: ${room.game_selected || '未选择'}</div>
            `);
            roomItem.click(() => {
              socket.emit('join_room', { room_id: room.id, token: token });
            });
            roomList.append(roomItem);
          }
        });
      }
    },
    error: () => {
      console.error('Failed to load room list');
    }
  });
}

// 加载可用游戏列表
function loadAvailableGames() {
  $.ajax({
    url: '/available_games',
    type: 'GET',
    success: (response) => {
      const gameSelect = $('#game-select');
      gameSelect.empty();

      (response.games || []).forEach(game => {
        gameSelect.append(`<option value="${game.id}">${game.name}</option>`);
      });
    },
    error: () => {
      console.error('Failed to load available games');
    }
  });
}
