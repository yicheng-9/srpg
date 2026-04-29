import pygame
import sys
import time
from typing import List, Optional, Tuple
import random
# ==================== 配置 ====================
BOARD_W = 8
BOARD_H = 10
CELL_SIZE = 52
PANEL_WIDTH = 320
WINDOW_WIDTH = CELL_SIZE * BOARD_W + 40 + PANEL_WIDTH
WINDOW_HEIGHT = CELL_SIZE * BOARD_H + 40
FPS = 30

# 颜色
BG_COLOR = (26, 26, 46)
BOARD_BG = (15, 52, 96)
CELL_COLOR = (42, 42, 64)
CELL_BORDER = (58, 58, 85)
CURRENT_TURN_COLOR = (255, 215, 0)
PLAYER_COLOR = (41, 98, 255)
ENEMY_COLOR = (213, 0, 0)
HP_GREEN = (0, 230, 118)
TEXT_WHITE = (255, 255, 255)
TEXT_GRAY = (170, 170, 170)
PANEL_BG = (15, 52, 96)

# ==================== 字体 ====================
def get_font(size):
    try:
        return pygame.font.Font("C:/Windows/Fonts/simhei.ttf", size)
    except:
        try:
            return pygame.font.Font("/System/Library/Fonts/STHeiti Light.ttc", size)
        except:
            try:
                return pygame.font.Font("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc", size)
            except:
                return pygame.font.SysFont("simhei", size)

# ==================== 兵种定义 ====================
CLASS_TEMPLATES = {
    'infantry': {'name': '步兵', 'extraRange': [], 'desc': '基础兵种，攻守平衡'},
    'knight':   {'name': '骑士', 'extraRange': [(0, 2)], 'desc': '前方+2格冲锋'},
    'archer':   {'name': '弓箭手', 'extraRange': [(0, 3)], 'desc': '前方+3格远射'},
    'assassin': {'name': '刺客', 'extraRange': [(0, -1)], 'desc': '后方+1格背刺'},
    'mage':     {'name': '法师', 'extraRange': [(0, 2), (-1, 2), (1, 2)], 'desc': '前方第2行3格'},
    'sword':      {'name': '剑', 'extraRange': [ (-1, 1), (1, 1)], 'desc': '前方3格横扫'}
}

def template_to_map(dx, dy, facing):
    if facing == 'up':    return (dx, -dy)
    elif facing == 'down':  return (-dx, dy)
    elif facing == 'left':  return (-dy, -dx)
    elif facing == 'right': return (dy, dx)
    return (dx, dy)

# ==================== 单位类 ====================
class Unit:
    def __init__(self, id, cls, x, y, facing, faction):
        self.id = id
        self.cls = cls
        self.name = CLASS_TEMPLATES[cls]['name']
        self.x = x
        self.y = y
        self.facing = facing
        self.faction = faction
        self.max_hp = 15
        self.hp = 15
        self.atk = 10
        self.def_base = 5
        self.ap_max = 10
        self.cur_ap = 10
        self.has_been_attacked = False
        self.dead = False
        self.acted = False
        self.has_used_normal_attack = False
        self.has_used_allout_attack = False

    def defense(self, units):
        bonus = 0
        # 检查前后左右四个方向的友方单位
        neighbors = [
            get_unit_at(units, self.x - 1, self.y),   # 左
            get_unit_at(units, self.x + 1, self.y),   # 右
            get_unit_at(units, self.x, self.y - 1),   # 上（前）
            get_unit_at(units, self.x, self.y + 1),   # 下（后）
        ]
        for u in neighbors:
            if u and u.faction == self.faction:
                bonus += 1
        
        # 防御加成上限为3
        bonus = min(bonus, 3)
        return self.def_base + bonus

    def attack_power(self):
        return 10 if self.has_been_attacked else 8

def get_unit_at(units, x, y):
    for u in units:
        if u.x == x and u.y == y and not u.dead:
            return u
    return None

# ==================== 游戏主类 ====================
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("战棋Demo · Pygame版")
        self.clock = pygame.time.Clock()
        self.font_small = get_font(12)
        self.font_normal = get_font(14)
        self.font_large = get_font(18)

        self.units = []
        self.selected_unit = None
        self.current_unit = None
        self.pending_mode = None
        self.turn_count = 1
        self.action_order = []
        self.ai_busy = False
        self.game_over = False
        self.log_messages = []
        self.board_rect = pygame.Rect(20, 20, BOARD_W*CELL_SIZE, BOARD_H*CELL_SIZE)
        self.panel_rect = pygame.Rect(20 + BOARD_W*CELL_SIZE + 20, 20, PANEL_WIDTH-20, WINDOW_HEIGHT-40)
        self.obstacles = set()  # 新增：障碍物坐标集合
        self.init_obstacles()   # 新增：生成障碍物
        self.init_units()
        self.start_new_round()

    def init_obstacles(self):
        """随机生成5个不可通行的障碍物位置"""
        all_positions = [(x, y) for x in range(BOARD_W) for y in range(BOARD_H)]
        
        # 排除初始单位位置
        unit_positions = [(x, y) for _, _, x, y, _, _ in self.base_positions()]
        available = [p for p in all_positions if p not in unit_positions]
        
        # 随机选5个
        self.obstacles = set(random.sample(available, min(5, len(available))))
        for x, y in self.obstacles:
            self.log(f"地图生成障碍物: ({x},{y})")
        def init_obstacles(self):
            """随机生成5个不可通行的障碍物位置"""
        all_positions = [(x, y) for x in range(BOARD_W) for y in range(BOARD_H)]
        
        # 排除初始单位位置
        unit_positions = [(x, y) for _, _, x, y, _, _ in self.base_positions()]
        available = [p for p in all_positions if p not in unit_positions]
        
        # 随机选5个
        self.obstacles = set(random.sample(available, min(5, len(available))))
        for x, y in self.obstacles:
            self.log(f"地图生成障碍物: ({x},{y})")
    def base_positions(self):
        """返回初始单位位置配置（提取出来供复用）"""
        return [
            ('p1', 'infantry', 0, 8, 'up', 'player'),
            ('p2', 'knight', 3, 8, 'up', 'player'),
            ('p3', 'archer', 4, 8, 'up', 'player'),
            ('p4', 'mage', 5, 8, 'up', 'player'),
            ('p5', 'assassin', 7, 8, 'up', 'player'),
            ('p6', 'sword', 2, 8, 'up', 'player'),
            ('e1', 'infantry', 0, 1, 'down', 'enemy'),
            ('e2', 'knight', 3, 1, 'down', 'enemy'),
            ('e3', 'archer', 4, 1, 'down', 'enemy'),
            ('e4', 'mage', 5, 1, 'down', 'enemy'),
            ('e5', 'assassin', 7, 1, 'down', 'enemy'),
            ('e6', 'sword', 2, 1, 'down', 'enemy'),
        ]
    
    def init_units(self):
        base = self.base_positions()
        self.units = [Unit(*args) for args in base]

    def log(self, msg):
        self.log_messages.append(msg)
        if len(self.log_messages) > 50:
            self.log_messages.pop(0)

    # ==================== 回合控制 ====================
    # ==================== 回合控制 ====================
    def build_action_order(self):
        """构建初始行动顺序（仅用于回合开始时重置 acted 状态）"""
        players = [u for u in self.units if u.faction == 'player' and not u.dead]
        enemies = [u for u in self.units if u.faction == 'enemy' and not u.dead]
        order = []
        max_len = max(len(players), len(enemies))
        for i in range(max_len):
            if i < len(players):
                order.append(players[i])
            if i < len(enemies):
                order.append(enemies[i])
        return order

    def get_next_active_unit(self):
        """动态获取下一个应该行动的单位（阵亡者自动跳过，后续提前）"""
        # 按原始顺序找到第一个未行动且存活的单位
        for u in self.action_order:
            if not u.acted and not u.dead:
                return u
        return None

    def start_new_round(self):
        # 重新构建行动顺序（基于当前存活单位）
        self.action_order = self.build_action_order()
        for u in self.units:
            u.acted = False
            u.has_used_normal_attack = False
            u.has_used_allout_attack = False
        self.selected_unit = None
        self.current_unit = None
        self.pending_mode = None
        self.advance_turn()

    def advance_turn(self):
        if self.game_over:
            return
        
        # 动态获取下一个单位，阵亡者自动被跳过
        next_unit = self.get_next_active_unit()
        
        if not next_unit:
            # 所有存活单位都已行动，进入下一回合
            self.turn_count += 1
            self.log(f"=== 第{self.turn_count}回合 ===")
            self.start_new_round()
            return
        
        self.current_unit = next_unit
        self.current_unit.cur_ap = self.current_unit.ap_max
        self.current_unit.has_used_normal_attack = False
        self.current_unit.has_used_allout_attack = False

        if self.current_unit.faction == 'player':
            self.on_player_turn()
        else:
            self.on_enemy_turn()
    def on_player_turn(self):
        self.ai_busy = False
        self.selected_unit = self.current_unit
        self.pending_mode = None
        self.log(f"轮到 {self.current_unit.name} 行动")

    def on_enemy_turn(self):
        if self.game_over:
            return
        self.ai_busy = True
        self.selected_unit = self.current_unit
        self.pending_mode = None
        self.log(f"敌方 {self.current_unit.name} 开始行动")

    def end_unit_turn(self, unit):
        if unit.dead:
            unit.acted = True
            self.selected_unit = None
            self.current_unit = None
            self.pending_mode = None
            if self.check_game_over():
                return
            self.advance_turn()
            return

        enemy_count = 0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                u = get_unit_at(self.units, unit.x + dx, unit.y + dy)
                if u and u.faction != unit.faction and not u.dead:
                    enemy_count += 1

        heal = unit.cur_ap - enemy_count
        old_hp = unit.hp
        unit.hp = max(0, min(unit.max_hp, unit.hp + heal))
        actual = unit.hp - old_hp
        
        # 新增：压力伤害致死判定
        if unit.hp <= 0:
            unit.hp = 0
            unit.dead = True
            self.log(f"{unit.name} 因压力过大倒下了！")
        
        elif actual > 0:
            self.log(f"{unit.name} 回复{actual}点体力 (AP剩余{unit.cur_ap}，周围敌人{enemy_count})")
        elif actual < 0:
            self.log(f"{unit.name} 受到{-actual}点压力伤害！")
        else:
            self.log(f"{unit.name} 体力无变化")

        unit.acted = True
        self.selected_unit = None
        self.current_unit = None
        self.pending_mode = None

        # 如果因压力伤害死亡，记录击败信息
        if unit.dead:
            self.log(f"{unit.name} 被击败！")

        if self.check_game_over():
            return
        self.advance_turn()
    def check_game_over(self):
        p_alive = sum(1 for u in self.units if u.faction == 'player' and not u.dead)
        e_alive = sum(1 for u in self.units if u.faction == 'enemy' and not u.dead)
        if p_alive == 0:
            self.game_over = True
            self.log("💀 游戏结束：敌方胜利！")
            return True
        if e_alive == 0:
            self.game_over = True
            self.log("🎉 游戏结束：玩家胜利！")
            return True
        return False

    # ==================== 攻击/移动范围 ====================
    def get_base_attack_cells(self, unit):
        base = [(0, 1), (-1, 0), (1, 0)]
        extra = CLASS_TEMPLATES[unit.cls]['extraRange']
        all_rel = base + extra
        cells = []
        for dx, dy in all_rel:
            mx, my = template_to_map(dx, dy, unit.facing)
            tx, ty = unit.x + mx, unit.y + my
            if 0 <= tx < BOARD_W and 0 <= ty < BOARD_H:
                cells.append((tx, ty))
        return cells
    def get_move_cells(self, unit):
        """返回可到达的格子及对应真实AP消耗（考虑障碍物）"""
        reachable = {}  # (x,y) -> 真实消耗
        visited = {(unit.x, unit.y): 0}
        queue = [(unit.x, unit.y, 0)]
        head = 0
        
        while head < len(queue):
            x, y, cost = queue[head]
            head += 1
            if cost > 0:
                reachable[(x, y)] = cost
            if cost >= unit.cur_ap:
                continue
            for dx, dy in ((0,-1),(0,1),(-1,0),(1,0)):
                nx, ny = x+dx, y+dy
                if 0 <= nx < BOARD_W and 0 <= ny < BOARD_H:
                    if (nx, ny) in self.obstacles:
                        continue
                    if get_unit_at(self.units, nx, ny) is not None:
                        continue
                    if (nx, ny) not in visited or visited[(nx, ny)] > cost + 1:
                        visited[(nx, ny)] = cost + 1
                        queue.append((nx, ny, cost+1))
        
        return reachable  # 返回字典：坐标->真实消耗
    # ==================== 攻击逻辑 ====================
    def perform_attack(self, target, is_allout):
        if not self.selected_unit or target.dead or self.ai_busy:
            return
        if self.selected_unit != self.current_unit:
            self.log("不是当前行动单位")
            return
        atk_cells = self.get_base_attack_cells(self.selected_unit)
        if (target.x, target.y) not in atk_cells:
            self.log("目标不在攻击范围内！")
            return

        if is_allout:
            if self.selected_unit.has_used_allout_attack:
                self.log("本轮已使用过全力一击")
                return
            if self.selected_unit.cur_ap < 5:
                self.log("AP不足5，无法全力一击")
                return
        else:
            if self.selected_unit.has_used_normal_attack:
                self.log("本轮已使用过普通攻击")
                return
            if self.selected_unit.cur_ap < 3:
                self.log("AP不足3，无法攻击")
                return

        atk_pow = self.selected_unit.attack_power()
        tar_def = target.defense(self.units)
        dmg = max(0, atk_pow - tar_def)

        target.has_been_attacked = True
        self.selected_unit.has_been_attacked = True

        target.hp -= dmg
        if target.hp <= 0:
            target.hp = 0
            target.dead = True

        if is_allout:
            self.selected_unit.cur_ap = 0
            self.selected_unit.has_used_allout_attack = True
            self.log(f"{self.selected_unit.name} 对 {target.name} 发动全力一击，造成{dmg}点伤害！")
        else:
            self.selected_unit.cur_ap -= 3
            self.selected_unit.has_used_normal_attack = True
            self.log(f"{self.selected_unit.name} 攻击 {target.name}，造成{dmg}点伤害（攻:{atk_pow} - 防:{tar_def}）")

        self.pending_mode = None
        if target.dead:
            self.log(f"{target.name} 被击败！")
        self.check_game_over()

    def perform_attack_ai(self, attacker, target, is_allout):
        if attacker.has_used_allout_attack and is_allout:
            return
        if attacker.has_used_normal_attack and not is_allout:
            return
        atk_cells = self.get_base_attack_cells(attacker)
        if (target.x, target.y) not in atk_cells:
            return
        if is_allout and attacker.cur_ap < 5:
            return
        if not is_allout and attacker.cur_ap < 3:
            return

        atk_pow = attacker.attack_power()
        tar_def = target.defense(self.units)
        dmg = max(0, atk_pow - tar_def)

        target.hp -= dmg
        if target.hp <= 0:
            target.hp = 0
            target.dead = True
        target.has_been_attacked = True
        attacker.has_been_attacked = True

        if is_allout:
            attacker.cur_ap = 0
            attacker.has_used_allout_attack = True
            self.log(f"[敌方] {attacker.name} 全力攻击 {target.name}，造成{dmg}点伤害")
        else:
            attacker.cur_ap -= 3
            attacker.has_used_normal_attack = True
            self.log(f"[敌方] {attacker.name} 攻击 {target.name}，造成{dmg}点伤害")

        if target.dead:
            self.log(f"{target.name} 被击败！")

    # ==================== 移动 ====================
    def move_unit_to(self, x, y):
        if not self.selected_unit or self.ai_busy:
            return
        if self.selected_unit != self.current_unit:
            self.log("不是当前行动单位")
            return
        
        # 使用BFS计算的真实消耗
        moves = self.get_move_cells(self.selected_unit)
        if (x, y) not in moves:
            return
        
        cost = moves[(x, y)]  # 真实的绕路消耗，不再是曼哈顿距离
        self.selected_unit.x = x
        self.selected_unit.y = y
        self.selected_unit.cur_ap -= cost
        self.log(f"{self.selected_unit.name} 移动到 ({x},{y})，消耗{cost}AP，剩余AP:{self.selected_unit.cur_ap}")
    # ==================== AI ====================
    def ai_step(self):
        if not self.ai_busy or self.game_over:
            return
        unit = self.current_unit
        if not unit or unit.acted:
            self.ai_busy = False
            return

        targets = [u for u in self.units if u.faction != unit.faction and not u.dead]
        if not targets:
            self.end_unit_turn(unit)
            self.ai_busy = False
            return

        # 找最近目标
        target = min(targets, key=lambda t: abs(t.x - unit.x) + abs(t.y - unit.y))

        # 1. 尝试攻击（如果目标已在当前攻击范围内）
        atk_cells = self.get_base_attack_cells(unit)
        if (target.x, target.y) in atk_cells:
            if not unit.has_used_normal_attack and unit.cur_ap >= 3:
                self.perform_attack_ai(unit, target, False)
                return
            if not unit.has_used_allout_attack and unit.cur_ap >= 5:
                self.perform_attack_ai(unit, target, True)
                return
            # 攻击次数已用完或AP不足，结束回合
            self.end_unit_turn(unit)
            self.ai_busy = False
            return

        # 2. 尝试原地转向（消耗1AP）以便攻击
        if unit.cur_ap >= 1 and not (unit.has_used_normal_attack and unit.has_used_allout_attack):
            original_facing = unit.facing
            for try_dir in ['up', 'down', 'left', 'right']:
                unit.facing = try_dir
                new_atk = self.get_base_attack_cells(unit)
                if (target.x, target.y) in new_atk:
                    unit.cur_ap -= 1
                    self.log(f"[敌方] {unit.name} 转向{try_dir}（消耗1AP）")
                    if not unit.has_used_normal_attack and unit.cur_ap >= 3:
                        self.perform_attack_ai(unit, target, False)
                    elif not unit.has_used_allout_attack and unit.cur_ap >= 5:
                        self.perform_attack_ai(unit, target, True)
                    else:
                        self.end_unit_turn(unit)
                        self.ai_busy = False
                    return
            unit.facing = original_facing

        # 3. 无法攻击，尝试移动（使用BFS找到真实可达的路径）
        if unit.cur_ap >= 1:
            moves = self.get_move_cells(unit)
            
            # 找离目标最近的可移动位置
            best_pos = None
            best_dist = float('inf')
            for (mx, my), cost in moves.items():
                dist = abs(target.x - mx) + abs(target.y - my)
                if dist < best_dist:
                    best_dist = dist
                    best_pos = (mx, my, cost)
            
            if best_pos:
                mx, my, cost = best_pos
                dx = mx - unit.x
                dy = my - unit.y
                step_x = 0 if dx == 0 else (1 if dx > 0 else -1)
                step_y = 0 if dy == 0 else (1 if dy > 0 else -1)
                
                moved = False
                for sx, sy in [(step_x, 0), (0, step_y), (step_x, step_y)]:
                    nx, ny = unit.x + sx, unit.y + sy
                    if (nx, ny) in moves and moves[(nx, ny)] <= unit.cur_ap:
                        unit.x, unit.y = nx, ny
                        unit.cur_ap -= 1
                        # 自动朝向移动方向
                        if abs(sx) >= abs(sy):
                            unit.facing = 'right' if sx > 0 else 'left' if sx < 0 else unit.facing
                        else:
                            unit.facing = 'down' if sy > 0 else 'up' if sy < 0 else unit.facing
                        moved = True
                        break
                
                if not moved:
                    self.end_unit_turn(unit)
                    self.ai_busy = False
                    return
                    
                if unit.cur_ap == 0:
                    self.end_unit_turn(unit)
                    self.ai_busy = False
                return
            else:
                self.log(f"[敌方] {unit.name} 无路可走")
                self.end_unit_turn(unit)
                self.ai_busy = False
                return
        else:
            self.end_unit_turn(unit)
            self.ai_busy = False
   # ==================== 交互（修复按钮坐标） ====================
    def toggle_attack_mode(self):
        if not self.selected_unit or self.ai_busy or self.game_over:
            return
        if self.selected_unit != self.current_unit:
            return
        if self.selected_unit.has_used_normal_attack or self.selected_unit.cur_ap < 3:
            return
        self.pending_mode = 'attack' if self.pending_mode != 'attack' else None

    def toggle_allout_mode(self):
        if not self.selected_unit or self.ai_busy or self.game_over:
            return
        if self.selected_unit != self.current_unit:
            return
        if self.selected_unit.has_used_allout_attack or self.selected_unit.cur_ap < 5:
            return
        self.pending_mode = 'allout' if self.pending_mode != 'allout' else None

    def change_facing(self, direction):
        if not self.selected_unit or self.ai_busy or self.game_over:
            return
        if self.selected_unit != self.current_unit:
            return
        # ---------- 新增：消耗1点AP ----------
        if self.selected_unit.cur_ap < 1:
            self.log("AP不足，无法转向")
            return
        self.selected_unit.facing = direction
        self.selected_unit.cur_ap -= 1
        dir_names = {'up': '上', 'down': '下', 'left': '左', 'right': '右'}
        self.log(f"{self.selected_unit.name} 转向{dir_names[direction]}，消耗1AP，剩余AP:{self.selected_unit.cur_ap}")

    def handle_click(self, mx, my):
        board_left = self.board_rect.left
        board_top = self.board_rect.top
        gx = (mx - board_left) // CELL_SIZE
        gy = (my - board_top) // CELL_SIZE
        if 0 <= gx < BOARD_W and 0 <= gy < BOARD_H:
            unit = get_unit_at(self.units, gx, gy)
            if self.pending_mode and self.selected_unit and self.selected_unit == self.current_unit and not self.ai_busy:
                if unit and unit.faction != self.selected_unit.faction and not unit.dead:
                    self.perform_attack(unit, self.pending_mode == 'allout')
                    return True
                else:
                    self.pending_mode = None
                    return True
            if unit and unit.faction == 'player' and not unit.dead:
                if unit == self.current_unit:
                    if self.selected_unit == unit and unit.cur_ap < unit.ap_max:
                        self.selected_unit = unit
                        self.pending_mode = None
                    else:
                        self.selected_unit = unit
                        unit.cur_ap = unit.ap_max
                        self.pending_mode = None
                    return True
                else:
                    self.log("现在不是该单位的行动轮次")
                    return True
            if self.selected_unit and not unit and self.selected_unit == self.current_unit and not self.ai_busy:
                self.move_unit_to(gx, gy)
                return True
            if not unit and not self.selected_unit:
                self.selected_unit = None
                self.pending_mode = None
        return False

    def handle_panel_click(self, mx, my):
        # ---------- 修复：按钮坐标与绘制坐标保持一致 ----------
        panel_left = self.panel_rect.left + 10
        btn_y = 20 + 350          # 与 draw_panel 中绘制按钮的 Y 坐标一致
        btn_width = 80
        btn_height = 32
        gap = 10

        # 结束行动
        btn1 = pygame.Rect(panel_left, btn_y, btn_width, btn_height)
        if btn1.collidepoint(mx, my):
            if self.selected_unit and not self.ai_busy:
                self.end_unit_turn(self.selected_unit)
            return True
        # 普通攻击
        btn2 = pygame.Rect(btn1.right + gap, btn_y, btn_width, btn_height)
        if btn2.collidepoint(mx, my):
            self.toggle_attack_mode()
            return True
        # 全力一击
        btn3 = pygame.Rect(btn2.right + gap, btn_y, btn_width, btn_height)
        if btn3.collidepoint(mx, my):
            self.toggle_allout_mode()
            return True

        # 方向键（第二行）
        dir_y = btn_y + btn_height + 15
        dir_btn_width = 60
        dir_btn_height = 28
        dir_gap = 5
        dirs = [('↑上', 'up'), ('↓下', 'down'), ('←左', 'left'), ('→右', 'right')]
        for i, (_, dir_code) in enumerate(dirs):
            rx = panel_left + i * (dir_btn_width + dir_gap)
            btn_rect = pygame.Rect(rx, dir_y, dir_btn_width, dir_btn_height)
            if btn_rect.collidepoint(mx, my):
                self.change_facing(dir_code)
                return True
        return False

    # ==================== 绘制 ====================
    def draw_board(self):
        board_left = self.board_rect.left
        board_top = self.board_rect.top
        
        # 绘制格子底色
        for y in range(BOARD_H):
            for x in range(BOARD_W):
                rect = pygame.Rect(board_left + x*CELL_SIZE, board_top + y*CELL_SIZE, CELL_SIZE, CELL_SIZE)
                
                # 新增：障碍物用深灰色显示
                if (x, y) in self.obstacles:
                    pygame.draw.rect(self.screen, (40, 40, 40), rect)
                    pygame.draw.rect(self.screen, (80, 80, 80), rect, 1)
                    # 画一个X表示障碍
                    pygame.draw.line(self.screen, (100, 100, 100), 
                                   (rect.left+5, rect.top+5), (rect.right-5, rect.bottom-5), 2)
                    pygame.draw.line(self.screen, (100, 100, 100), 
                                   (rect.right-5, rect.top+5), (rect.left+5, rect.bottom-5), 2)
                    continue
                
                color = CELL_COLOR
                if self.selected_unit and not self.ai_busy:
                    moves = self.get_move_cells(self.selected_unit)
                    atks = self.get_base_attack_cells(self.selected_unit)
                    if (x, y) in moves and self.pending_mode not in ('attack', 'allout'):
                        color = (0, 100, 200)
                    if (x, y) in atks:
                        color = (180, 40, 40)
                if self.current_unit and self.current_unit.x == x and self.current_unit.y == y and not self.game_over:
                    pygame.draw.rect(self.screen, CURRENT_TURN_COLOR, rect, 3)
                if self.selected_unit and self.selected_unit.x == x and self.selected_unit.y == y:
                    pygame.draw.rect(self.screen, (255, 215, 0), rect, 2)
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, CELL_BORDER, rect, 1)

                unit = get_unit_at(self.units, x, y)
                if unit:
                    cx, cy = rect.centerx, rect.centery
                    radius = 18
                    if unit.faction == 'player':
                        unit_color = (41, 98, 255)
                    else:
                        unit_color = (213, 0, 0)
                    if unit.acted:
                        unit_color = (100, 100, 100)
                    if unit.dead:
                        unit_color = (50, 50, 50)
                    pygame.draw.circle(self.screen, unit_color, (cx, cy), radius)
                    pygame.draw.circle(self.screen, (255,255,255), (cx, cy), radius, 2)
                    arrow = {'up':'↑','down':'↓','left':'←','right':'→'}.get(unit.facing, '?')
                    arr_surf = self.font_small.render(arrow, True, (255,255,255))
                    self.screen.blit(arr_surf, (cx-6, cy-20))
                    name_surf = self.font_small.render(unit.name, True, (255,255,255))
                    hp_surf = self.font_small.render(f"HP:{unit.hp}", True, HP_GREEN)
                    self.screen.blit(name_surf, (cx-name_surf.get_width()//2, cy-8))
                    self.screen.blit(hp_surf, (cx-hp_surf.get_width()//2, cy+4))

    def draw_panel(self):
        panel_left = self.panel_rect.left + 10
        panel_top = self.panel_rect.top
        y_offset = panel_top + 10

        # 回合信息
        if self.game_over:
            turn_text = "游戏结束"
            color = (255, 80, 80)
        elif self.current_unit and self.current_unit.faction == 'player':
            turn_text = f"🛡️ 玩家行动 (第{self.turn_count}回合)"
            color = (100, 150, 255)
        else:
            turn_text = f"⚔️ 敌方行动 (第{self.turn_count}回合)"
            color = (255, 100, 100)
        turn_surf = self.font_large.render(turn_text, True, color)
        self.screen.blit(turn_surf, (panel_left, y_offset))
        y_offset += 40

        # 单位信息
        if self.selected_unit and not self.selected_unit.dead and self.selected_unit.faction == 'player':
            u = self.selected_unit
            lines = [
                f"位置: ({u.x},{u.y}) 朝向{u.facing}",
                f"体力: {u.hp}/{u.max_hp}",
                f"行动点: {u.cur_ap}/{u.ap_max}",
                f"攻击力: {u.attack_power()}{' (首次8)' if not u.has_been_attacked else ''}",
                f"防御力: {u.defense(self.units)} (基础{u.def_base}+站位)",
                f"普通攻击: {'已用' if u.has_used_normal_attack else '可用'}",
                f"全力一击: {'已用' if u.has_used_allout_attack else '可用'}",
                CLASS_TEMPLATES[u.cls]['desc']
            ]
            for line in lines:
                surf = self.font_normal.render(line, True, TEXT_WHITE)
                self.screen.blit(surf, (panel_left, y_offset))
                y_offset += 22
        else:
            msg = "敌方思考中..." if self.ai_busy else ("等待行动" if not self.game_over else "战斗结束")
            surf = self.font_normal.render(msg, True, TEXT_GRAY)
            self.screen.blit(surf, (panel_left, y_offset))
            y_offset += 30

        # ---------- 按钮区域（坐标与 handle_panel_click 一致） ----------
        btn_y = 20 + 350
        btn_width = 80
        btn_height = 32
        gap = 10

        # 结束行动
        btn1 = pygame.Rect(panel_left, btn_y, btn_width, btn_height)
        pygame.draw.rect(self.screen, (41,98,255), btn1, border_radius=6)
        txt1 = self.font_small.render("结束行动", True, (255,255,255))
        self.screen.blit(txt1, (btn1.x+8, btn1.y+6))

        # 普通攻击
        btn2 = pygame.Rect(btn1.right + gap, btn_y, btn_width, btn_height)
        pygame.draw.rect(self.screen, (255,50,50), btn2, border_radius=6)
        mode_text = "【攻击中】" if self.pending_mode == 'attack' else "普通攻击"
        txt2 = self.font_small.render(mode_text, True, (255,255,255))
        self.screen.blit(txt2, (btn2.x+5, btn2.y+6))

        # 全力一击
        btn3 = pygame.Rect(btn2.right + gap, btn_y, btn_width, btn_height)
        pygame.draw.rect(self.screen, (255,140,0), btn3, border_radius=6)
        mode_text3 = "【全力中】" if self.pending_mode == 'allout' else "全力一击"
        txt3 = self.font_small.render(mode_text3, True, (255,255,255))
        self.screen.blit(txt3, (btn3.x+5, btn3.y+6))

        # 方向键
        dir_y = btn_y + btn_height + 15
        dir_btn_width = 60
        dir_btn_height = 28
        dir_gap = 5
        dirs = [('↑上', 'up'), ('↓下', 'down'), ('←左', 'left'), ('→右', 'right')]
        for i, (label, _) in enumerate(dirs):
            rx = panel_left + i * (dir_btn_width + dir_gap)
            btn_rect = pygame.Rect(rx, dir_y, dir_btn_width, dir_btn_height)
            pygame.draw.rect(self.screen, (80,80,100), btn_rect, border_radius=4)
            d_surf = self.font_small.render(label, True, (255,255,255))
            self.screen.blit(d_surf, (rx+15, dir_y+5))

        # 日志
        log_rect = pygame.Rect(panel_left, dir_y + dir_btn_height + 15, PANEL_WIDTH-30, 200)
        pygame.draw.rect(self.screen, (20,20,40), log_rect)
        pygame.draw.rect(self.screen, (80,80,100), log_rect, 1)
        log_y = log_rect.y + 5
        for msg in self.log_messages[-10:]:
            log_surf = self.font_small.render(msg, True, TEXT_GRAY)
            self.screen.blit(log_surf, (log_rect.x+5, log_y))
            log_y += 18
            if log_y > log_rect.bottom - 15:
                break

    def run(self):
        while True:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    if self.board_rect.collidepoint(mx, my):
                        self.handle_click(mx, my)
                    else:
                        self.handle_panel_click(mx, my)

            if self.ai_busy and not self.game_over:
                time.sleep(0.15)
                self.ai_step()

            self.screen.fill(BG_COLOR)
            self.draw_board()
            self.draw_panel()
            pygame.display.flip()

if __name__ == "__main__":
    game = Game()
    game.run()