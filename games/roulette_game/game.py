from games.base import BaseGame

class RouletteGame(BaseGame):
    """
    Roulette游戏类
    一个简单的测试游戏，用于验证前后端通信
    """
    def __init__(self, room_id):
        """
        初始化Roulette游戏
        
        Args:
            room_id: 房间ID
        """
        super().__init__(room_id)
        self.game_type = 'roulette'
        self.test_message = "Roulette游戏已初始化"
    
    def join(self, account, player_id):
        """
        玩家加入游戏
        
        Args:
            account: 玩家账号
            player_id: 玩家游戏ID
        
        Returns:
            int: 玩家顺序号
        """
        if account in self.players:
            return None
        
        if self.host is None:
            self.host = account
        
        order = len(self.players) + 1
        self.players[account] = {
            'ID': player_id,
            'order': order
        }
        return order
    
    def leave(self, account):
        """
        玩家离开游戏
        
        Args:
            account: 玩家账号
        """
        if account in self.players:
            del self.players[account]
            if account == self.host and self.players:
                self.host = next(iter(self.players.keys()))
    
    def start(self):
        """
        开始游戏
        
        Returns:
            bool: 是否成功开始
        """
        if len(self.players) > 0:
            self.started = True
            return True
        return False
    
    def handle_event(self, account, data):
        """
        处理游戏事件
        
        Args:
            account: 发起事件的玩家账号
            data: 事件数据
        
        Returns:
            dict: 处理结果
        """
        print(f"处理事件: {data}")
        event_name = data.get('event_name')
        
        if event_name == 'test_input':
            # 处理测试输入事件
            user_input = data.get('event_data', {}).get('input', '')
            return {
                'ok': True,
                'msg': f'后端收到来自 {account} 的消息: {user_input}',
                'echo': user_input,
                'timestamp': data.get('event_data', {}).get('timestamp', ''),
                'broadcast': True
            }
        
        return {
            'ok': False,
            'msg': '未知事件类型',
            'broadcast': False
        }
    
    def get_state(self):
        """
        获取游戏状态
        
        Returns:
            dict: 游戏状态数据
        """
        return {
            'game_type': self.game_type,
            'room_id': self.room_id,
            'players': self.players,
            'started': self.started,
            'host': self.host,
            'message': self.test_message
        }

def register_game():
    """
    注册Roulette游戏
    
    Returns:
        dict: 游戏信息
    """
    return {
        'id': 'roulette',
        'name': 'Roulette',
        'description': '一个简单的测试游戏',
        'min_players': 1,
        'max_players': 4,
        'class': RouletteGame,
        'url': '/roulette'
    }
