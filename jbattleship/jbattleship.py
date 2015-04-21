"""
JBattleShip v1.0 by JKornev
Web: http://way.dos.ninja
"""

import random
import sys

#######################
# Game vars

# const configs
c_debug_mode = 0
c_map_rows = 15
c_map_cols = 15
c_ships_peak_lvl = 5

# battle map
g_my_ship_map = []
g_my_shoot_map = []
g_my_ships = []

g_enemy_ship_map = []
g_enemy_shoot_map = []
g_enemy_ships = []

# ui
g_title_msg_bar = ""
g_status_msg_bar = ""
g_input_msg_bar = ""
g_battle_left_msg_bar = ""
g_battle_right_msg_bar = ""

# create ships scene
g_create_manual = True
g_create_ship_state = 0
g_to_create = []
g_new_ship = {}

# battle scene
g_battle_io_state = 0
g_battle_x = 0
g_battle_y = 0

# ai context

# enums
E_SHOOT_FAIL = 0
E_SHOOT_MISS = 1
E_SHOOT_HIT  = 2
E_SHOOT_KILL = 3

E_DIR_UNKN = -1
E_DIR_VERT =  0
E_DIR_HORZ =  1

E_HIT_EMPTY = 0
E_HIT_HIT   = 1
E_HIT_BUSY  = 2

#######################
# CUI graphics & IO

def update_view():
    #clear old view
    #clear_view()

    # title_bar
    print "\n%s\n" % g_title_msg_bar
	
    # battle spaces
    temp = ""
    for x in xrange(1, c_map_cols + 1):
        if (x > 10 and x % 2 == 1):
            temp += "  "
        else:
            temp += "{:<2}".format(str(x))
        
    print "    " + temp + "       " + temp

    temp = ""
    for x in xrange(1, c_map_cols + 1):
        if (x > 10 and x % 2 == 1):
            temp += "{:<2}".format(str(x))
        else:
            temp += "--"
    print "    " + temp + "       " + temp
    
    for x in xrange(0, c_map_rows):
        temp_right = temp_left = " %s |" % str(unichr(96 + x + 1))
        
        for y in xrange(0, c_map_cols):
            temp_left += get_my_cell_str(x, y)
            temp_right += get_enemy_cell_str(x, y)
            
        print temp_left + "   " + temp_right

    temp = ""
    for x in xrange(1, c_map_cols * 2 + 8 - len(g_battle_left_msg_bar)):
        temp += " "
    print "    " + g_battle_left_msg_bar + temp + g_battle_right_msg_bar

    #print status
    print "\n%s\n" % g_status_msg_bar

def clear_view():
    print "\x1b[H\n" # ASCII escape sequences (don't work at the Windows NT)

def get_input_value():
    return raw_input("%s>" % g_input_msg_bar)

def get_my_cell_str(x, y):
    res = ""
    id = g_my_ship_map[x][y]

    if (id == -1):
        if (g_my_shoot_map[x][y] != E_HIT_HIT):
            res += "~ "
        else:
            res += "x "
    else:
        if (g_my_shoot_map[x][y] != E_HIT_HIT):
            res += "%d|" % g_my_ships[id]['size']
        else:
            res += "X|"
            
    return res

def get_enemy_cell_str(x, y):
    global c_debug_mode
    
    res = ""
    id = g_enemy_ship_map[x][y]

    if (id == -1):
        if (g_enemy_shoot_map[x][y] == E_HIT_EMPTY):
            #res += "\xB7 "
            res += "~ "
        else:
            res += "x "
    else:
        if (g_enemy_shoot_map[x][y] == E_HIT_EMPTY):
            res += "~|" if c_debug_mode == 1 else "~ "
        else:
            if (g_enemy_ships[id]['hits'] == g_enemy_ships[id]['size']):
                res += "X|"
            else:
                res += "%d|" % g_enemy_ships[id]['size']
            
    return res

def conv_inx_to_str(inx):
    return str(unichr(96 + inx))
    
#######################
# Game context

def set_title_msg(msg = ""):
    global g_title_msg_bar
    g_title_msg_bar = msg
    
def set_status_msg(msg = ""):
    global g_status_msg_bar
    g_status_msg_bar = msg
    
def set_input_msg(msg = ""):
    global g_input_msg_bar
    g_input_msg_bar = msg

def set_battle_left_msg(msg = ""):
    global g_battle_left_msg_bar
    g_battle_left_msg_bar = msg

def set_battle_right_msg(msg = ""):
    global g_battle_right_msg_bar
    g_battle_right_msg_bar = msg
    
def fill_map(fmap, rows, cols, val):
    del fmap[:]
    for x in xrange(rows):
        row = []
        for y in xrange(cols):
            row.append(val)
        fmap.append(row)

def clear_game_context():
    fill_map(g_my_ship_map, c_map_rows, c_map_cols, -1)
    fill_map(g_my_shoot_map, c_map_rows, c_map_cols, E_HIT_EMPTY)
    fill_map(g_enemy_ship_map, c_map_rows, c_map_cols, -1)
    fill_map(g_enemy_shoot_map, c_map_rows, c_map_cols, E_HIT_EMPTY)
    
    set_title_msg()
    set_status_msg()
    set_input_msg()
    set_battle_left_msg()
    set_battle_right_msg()
    
    del g_my_ships[:]
    del g_enemy_ships[:]

#######################
# Ships control

def insert_ship(battle_space, battle_obj, ship):
    guid = len(battle_obj)
    battle_obj.insert(guid, dict(ship))
    
    if (ship['dir'] == 0):
        for i in xrange(ship['size']):
            battle_space[ ship['x'] + i ][ ship['y'] ] = guid
    else:
        for i in xrange(ship['size']):
            battle_space[ ship['x'] ][ ship['y'] + i ] = guid


def check_insertable_ship(battle_space, ship):
    if (ship['dir'] == 0):
        if (ship['x'] + ship['size'] > c_map_rows):
            return False
        
        for i in xrange(ship['size']):
            if (check_insertable_cell(battle_space, ship['x'] + i, ship['y']) == False):
                return False
                
    else:
        if (ship['y'] + ship['size'] > c_map_cols):
            return False
    
        for i in xrange(ship['size']):
            if (check_insertable_cell(battle_space, ship['x'], ship['y'] + i) == False):
                return False
            
    return True

def check_insertable_cell(battle_space, x, y):
    #check boundary
    if (battle_space[x][y] != -1) \
    or (x > 0 and battle_space[x - 1][y] != -1) \
    or (x + 1 < c_map_rows and battle_space[x + 1][y] != -1) \
    or (y > 0 and battle_space[x][y - 1] != -1) \
    or (y + 1 < c_map_cols and battle_space[x][y + 1] != -1):
        return False
    #check diagonal
    if (x > 0 and y > 0 and battle_space[x - 1][y - 1] != -1) \
    or (x + 1 < c_map_rows and y > 0 and battle_space[x + 1][y - 1] != -1) \
    or (x > 0 and y + 1 < c_map_cols and battle_space[x - 1][y + 1] != -1) \
    or (x + 1 < c_map_rows and y + 1 < c_map_cols and battle_space[x + 1][y + 1] != -1):
        return False
        
    return True
    
def find_spaces_for_ship(battle_space, direct, ship_size):
    spaces = []
    
    if (direct == 0): #horizontal
        for y in xrange(c_map_cols):
            found = 0
            for x in xrange(c_map_rows):
                if (check_insertable_cell(battle_space, x, y) == True):
                    found += 1
                    if (found >= ship_size):
                        spaces.append((x - ship_size + 1, y))
                else:
                    found = 0
                
    else: #vertical
        for x in xrange(c_map_rows):
            found = 0
            for y in xrange(c_map_cols):
                if (check_insertable_cell(battle_space, x, y) == True):
                    found += 1
                    if (found >= ship_size):
                        spaces.append((x, y - ship_size + 1))
                else:
                    found = 0
                    
    return spaces

def generate_ships(battle_space, battle_obj, lvl):
    size = lvl
    count = 1
    
    while (size > 0):

        for i in xrange(count):
            ship = {}
            
            direct = random.randint(0, 1)
            if (direct == 0):
                ship['dir'] = direct
            else:
                ship['dir'] = direct

            spaces = find_spaces_for_ship(battle_space, direct, size)
            if (len(spaces) == 0):
                return False

            inx = random.randint(0, len(spaces) - 1)
            ship['x'] = spaces[inx][0]
            ship['y'] = spaces[inx][1]
            ship['size'] = size
            ship['hits'] = 0

            insert_ship(battle_space, battle_obj, ship)
            
        #increase block
        size -= 1
        count += 1

    return True

#######################
# Battle control

def shoot(battle_space, battle_obj, shoot_map, x, y):

    if (shoot_map[x][y] != E_HIT_EMPTY):
        return E_SHOOT_FAIL

    shoot_map[x][y] = E_HIT_HIT

    id = battle_space[x][y]
    if (id == -1):
        return E_SHOOT_MISS

    battle_obj[id]['hits'] += 1
    if (battle_obj[id]['hits'] == battle_obj[id]['size']):
        return E_SHOOT_KILL #TODO
    
    return E_SHOOT_HIT

g_ai_hit_ship = False
g_ai_shoot_context = {'rank_map' : [], 'targs_x' : [], 'targs_y' : [], 'shoot_dir' : E_DIR_UNKN}
g_ai_wanted_ships = []

def ai_enemy_init():
    global g_ai_hit_ship, g_ai_wanted_ships, g_ai_shoot_context
    
    g_ai_hit_ship = False
    
    g_ai_shoot_context['rank_map'] = []
    g_ai_shoot_context['targs_x'] = []
    g_ai_shoot_context['targs_y'] = []
    g_ai_shoot_context['shoot_dir'] =  E_DIR_UNKN
    
    count = 1
    size = c_ships_peak_lvl
    
    while (size > 0):
        for x in xrange(count):
            g_ai_wanted_ships.append(size)
            
        size -= 1
        count += 1
    
def ai_enemy_shoot_me(battle_space, battle_obj, shoot_map, hit):
    global g_ai_shoot_context, g_ai_hit_ship
    
    if (g_ai_hit_ship == False):#shoot & find ship
    
        if (len(g_ai_wanted_ships) == 0):
            return False
            
        target_size = g_ai_wanted_ships[0]
        calc_target_ranks(shoot_map, target_size, g_ai_shoot_context['rank_map'])
        ranks = get_top_ranks(g_ai_shoot_context['rank_map'])
        if (ranks == None):
            return False
        
        target = random.choice(ranks)
        
        hit['x'] = target[0]
        hit['y'] = target[1]
        hit['res'] = shoot(battle_space, battle_obj, shoot_map,  hit['x'],  hit['y'])
        
        if (hit['res'] == E_SHOOT_HIT):
            g_ai_hit_ship = True
            x = hit['x']
            y = hit['y']
            
            g_ai_shoot_context['targs_x'] = []
            g_ai_shoot_context['targs_y'] = []
                
            append_target_cells(shoot_map, g_ai_shoot_context['targs_x'], g_ai_shoot_context['targs_y'], x, y, E_DIR_UNKN)
            
            if (len(g_ai_shoot_context['targs_x']) == 0 or 0 == len(g_ai_shoot_context['targs_y'])):
                g_ai_shoot_context['shoot_dir'] = E_DIR_VERT if len(g_ai_shoot_context['targs_x']) > 0 else E_DIR_HORZ
            else:
                g_ai_shoot_context['shoot_dir'] = E_DIR_UNKN

    else: # shoot & kill ship
        dir = random.randint(0, 1) if g_ai_shoot_context['shoot_dir'] == E_DIR_UNKN else g_ai_shoot_context['shoot_dir']
        
        if (dir == 0):
            target = random.choice(g_ai_shoot_context['targs_x'])
            g_ai_shoot_context['targs_x'].remove(target)
        else:
            target = random.choice(g_ai_shoot_context['targs_y'])
            g_ai_shoot_context['targs_y'].remove(target)
            
        x = hit['x'] = target[0]
        y = hit['y'] = target[1]
        hit['res'] = shoot(battle_space, battle_obj, shoot_map,  hit['x'],  hit['y'])
        
        if (hit['res'] == E_SHOOT_HIT):
            g_ai_shoot_context['shoot_dir'] = dir
            if (dir ^ 1):
                g_ai_shoot_context['targs_y'] = []
            else:
                g_ai_shoot_context['targs_x'] = []

            append_target_cells(shoot_map, g_ai_shoot_context['targs_x'], g_ai_shoot_context['targs_y'], x, y, dir)
        elif (hit['res'] == E_SHOOT_MISS):
            if (dir == E_DIR_VERT and len(g_ai_shoot_context['targs_x']) == 0):
                g_ai_shoot_context['shoot_dir'] = E_DIR_HORZ
            elif (dir == E_DIR_HORZ and len(g_ai_shoot_context['targs_y']) == 0):
                g_ai_shoot_context['shoot_dir'] = E_DIR_VERT
                
    if (hit['res'] == E_SHOOT_KILL):
        g_ai_hit_ship = False
        id = battle_space[ hit['x'] ][ hit['y'] ]
        for x in g_ai_wanted_ships:
            if (x == battle_obj[id]['size']):
                g_ai_wanted_ships.remove(x)
                #print "remove", x
                break
        
        fill_cells_around_ship(battle_obj[id], shoot_map)

    return True
    
def append_target_cells(shoot_map, targs_x, targs_y, x, y, dir):
    if (dir == E_DIR_UNKN or dir == E_DIR_VERT):
        if (x > 0 and shoot_map[x - 1][y] == E_HIT_EMPTY):
            targs_x.append((x - 1, y))
        if (x + 1 < c_map_rows and shoot_map[x + 1][y] == E_HIT_EMPTY):
            targs_x.append((x + 1, y))
    if (dir == E_DIR_UNKN or dir == E_DIR_HORZ):
        if (y > 0 and shoot_map[x][y - 1] == E_HIT_EMPTY):
            targs_y.append((x, y - 1))
        if (y + 1 < c_map_cols and shoot_map[x][y + 1] == E_HIT_EMPTY):
            targs_y.append((x, y + 1))
    
def calc_target_ranks(shoot_map, target_size, rank_map):
    fill_map(rank_map, c_map_rows, c_map_cols, 0)
    
    for x in xrange(c_map_rows):
        match = 0
        start = 0
        
        for y in xrange(c_map_cols):
            if (match == 0):
                if (shoot_map[x][y] == E_HIT_EMPTY):
                    start = y
                    match = 1
            else:
                if (shoot_map[x][y] == E_HIT_EMPTY):
                    match += 1
                else:
                    match = 0
            
            if (match >= target_size):
                for z in xrange(target_size):
                    rank_map[x][start + z] += 1
                start += 1
    
    #horizontal
    for y in xrange(c_map_cols):
        match = 0
        start = 0
        
        for x in xrange(c_map_rows):
            if (match == 0):
                if (shoot_map[x][y] == E_HIT_EMPTY):
                    start = x
                    match = 1
            else:
                if (shoot_map[x][y] == E_HIT_EMPTY):
                    match += 1
                else:
                    match = 0
            
            if (match >= target_size):
                for z in xrange(target_size):
                    rank_map[start + z][y] += 1
                start += 1
        
def get_top_ranks(rank_map):
    ranks = []
    max = 0
    for x in xrange(c_map_rows):
        for y in xrange(c_map_cols):
            if (rank_map[x][y] > max):
                max = rank_map[x][y]
                ranks = []
                
            if (rank_map[x][y] == max > 0):
                ranks.append((x, y))
                
    return ranks if len(ranks) > 0 else None
    
def check_empty_cell(shoot_map, x, y):
    if (x < 0 or y < 0):
        return False
    if (x >= c_map_rows or y >= c_map_rows):
        return False
    if (shoot_map[x][y] != E_HIT_EMPTY):
        return False
    return True
    
def fill_empty_range(shoot_map, x, y, dir, size):
    if (dir == E_DIR_VERT):
        for n in xrange(size):
            if (check_empty_cell(shoot_map, x + n, y)):
                shoot_map[x + n][y] = E_HIT_BUSY
    else:
        for n in xrange(size):
            if (check_empty_cell(shoot_map, x, y + n)):
                shoot_map[x][y + n] = E_HIT_BUSY 
    
def fill_cells_around_ship(ship, shoot_map):
    x = ship['x']
    y = ship['y']
    dir = ship['dir']
    size = ship['size']
    
    if (dir == E_DIR_VERT):
        fill_empty_range(shoot_map, x - 1, y - 1, dir, size + 2)
        fill_empty_range(shoot_map, x - 1, y + 1, dir, size + 2)
        
        if (check_empty_cell(shoot_map, x - 1, y)):
            shoot_map[x - 1][y] = E_HIT_BUSY
        if (check_empty_cell(shoot_map, x + size, y)):
            shoot_map[x + size][y] = E_HIT_BUSY
                
    else:
        fill_empty_range(shoot_map, x - 1, y - 1, dir, size + 2)
        fill_empty_range(shoot_map, x + 1, y - 1, dir, size + 2)
        
        if (check_empty_cell(shoot_map, x, y - 1)):
            shoot_map[x][y - 1] = E_HIT_BUSY
        if (check_empty_cell(shoot_map, x, y + size)):
            shoot_map[x][y + size] = E_HIT_BUSY

#######################
# Game control

# first scene
def start_game_scene_init():
    set_status_msg("Welcome to the JBattleShip, type 'manual', 'random' or 'credits'")
    set_input_msg("cmd")
    return True
    
def start_game_scene_handler(value):
    global g_create_manual
    
    if (value == "manual"):
        g_create_manual = True
        return True
    if (value == "random"):
        g_create_manual = False
        return True
    elif (value == "credits"):
        set_status_msg("Developer: JKornev <c> http://way.dos.ninja. Type 'manual', 'random' or 'credits'")
        return False
    else:
        set_status_msg("Unknown command, type 'manual', 'random' or 'credits'")
        return False

# second scene
def creating_ships_scene_init():
    global g_to_create, g_create_ship_state, g_new_ship

    if (g_create_manual == False):
        generate_ships(g_my_ship_map, g_my_ships, c_ships_peak_lvl)
        set_status_msg("Type 'next' or 'start'")
        set_input_msg("cmd")
        return

    count = 1
    size = c_ships_peak_lvl
    
    for i in xrange(c_ships_peak_lvl):
        for a in xrange(count):
            g_to_create.append(size)
        
        size -= 1
        count += 1
	
    g_new_ship.clear()
    g_new_ship['hits'] = 1
    
    g_create_ship_state = 0
    set_create_msg()

    return
    
def creating_ships_scene_handler(value):
    global g_to_create, g_create_ship_state, g_new_ship

    if (g_create_manual == False):
        
        if (value == 'next'):
            fill_map(g_my_ship_map, c_map_rows, c_map_cols, -1)
            del g_my_ships[:]
                
            generate_ships(g_my_ship_map, g_my_ships, c_ships_peak_lvl)
            set_status_msg("Next variant are generated, type 'next' or 'start'")
            return False
        elif (value == 'start'):
            return True
        else:
            set_status_msg("Unknown command, type 'next' or 'start'")
            return False
    
    msg = "Creating ship"
    if (g_create_ship_state == 0): #check horizontal
        
        if (len(value) != 1):
            set_status_msg("Error, invalid row number (unknown format)")
            return False 
			
        alph_char = ord('a')
        val_char = ord(value[0])

        if (alph_char > val_char or alph_char + c_map_rows <= val_char):
            set_create_msg("Error, invalid row char")
            return False

        g_new_ship['x'] = val_char - alph_char
        g_create_ship_state += 1
        
    elif (g_create_ship_state == 1): #check vertical
        
        if (not value.isdigit()):
            set_create_msg("Error, invalid column number")
            return False
		
        val = int(value)

        if (val < 1 or val > c_map_cols):
            set_create_msg("Error, invalid column number")
            return False

        g_new_ship['y'] = val - 1
        g_create_ship_state += 1
        
    else: #check direction & insert
        
        if (value == 'h'):
            g_new_ship['dir'] = 1
        elif (value == 'v'):
            g_new_ship['dir'] = 0
        else:
            set_create_msg("Error, invalid direction")
            return False

        g_new_ship['size'] = g_to_create[0]
        if (check_insertable_ship(g_my_ship_map, g_new_ship) == False):
            msg = "Error, invalid ship position"
        else:
            insert_ship(g_my_ship_map, g_my_ships, g_new_ship)
            del g_to_create[0]
            
        g_create_ship_state = 0

    if (len(g_to_create) == 0):
        return True
    else:
        set_create_msg(msg)
    
    return False

def set_create_msg(msg = "Creating ship"):
    set_status_msg("%s (#%d, size:%d)" % (msg, len(g_my_ships) + 1, g_to_create[0]))
    if (g_create_ship_state == 0):
        set_input_msg("chr(a-%s)" % conv_inx_to_str(c_map_rows))
    elif (g_create_ship_state == 1):
        set_input_msg("num(1-%s)" % str(c_map_cols))
    else:
        set_input_msg("pos(h or v)")
    
# third scene
def battle_scene_init():
    global g_battle_io_state
    g_battle_io_state = 0

    set_battle_msg()

def battle_scene_handler(value):
    global g_battle_io_state, g_battle_x, g_battle_y

    msg = "Now let's shoot to the enemy"
    
    if (g_battle_io_state == 0): #check horizontal

        if (len(value) != 1):
            set_status_msg("Error, invalid row number (unknown format)")
            return False 
        
        alph_char = ord('a')
        val_char = ord(value[0])

        if (alph_char > val_char or alph_char + c_map_rows <= val_char):
            set_status_msg("Error, invalid row number (out of range)")
            return False

        g_battle_x = val_char - alph_char
        g_battle_io_state += 1
        
    elif (g_battle_io_state == 1):

        if (not value.isdigit()):
            set_status_msg("Error, invalid column number")
            return False
        
        val = int(value)

        if (val < 1 or val > c_map_cols):
            set_status_msg("Error, invalid column number")
            return False

        g_battle_y = val - 1
        g_battle_io_state = 0

        if (shoot(g_enemy_ship_map, g_enemy_ships, g_enemy_shoot_map, g_battle_x, g_battle_y) == E_SHOOT_FAIL):
            msg = "Error, cant shoot to this cell"
        else:
            if (is_all_ships_destroyed(g_enemy_ships)):
                g_battle_io_state = 2
                set_status_msg("~===|  Congratulations, you are win this battle! :)  |===~")
                set_input_msg("exit")
                return False
        
            hit = {}#x,y,res
            if (not ai_enemy_shoot_me(g_my_ship_map, g_my_ships, g_my_shoot_map, hit)):
                set_status_msg("Error, internal AI problems")
                return False
            
            if (is_all_ships_destroyed(g_my_ships)):
                g_battle_io_state = 2
                set_status_msg("~===|  Game over! You are lose this battle :(  |===~")
                set_input_msg("exit")
                return False
            
            msg = "Enemy hit to %s%d" % (conv_inx_to_str(hit['x'] + 1), hit['y'] + 1)
            if (hit['res'] == E_SHOOT_HIT):
                msg = msg + " and catch your ship!"
            elif (hit['res'] == E_SHOOT_KILL):
                msg = msg + " and kill your ship!"
    else:
        return True
        
    set_battle_msg(msg)
    
    return False

def is_all_ships_destroyed(ships):
    for ship in ships:
        if (ship['hits'] != ship['size']):
            return False
    return True

def set_battle_msg(msg = "Now let's shoot to the enemy"):
    set_status_msg("%s" % msg)
    if (g_battle_io_state == 0):
        set_input_msg("chr(a-%s)" % conv_inx_to_str(c_map_rows))
    else:
        set_input_msg("num(1-%s)" % str(c_map_cols))

def start_game():

    clear_game_context()

    if (generate_ships(g_enemy_ship_map, g_enemy_ships, c_ships_peak_lvl) == False):
        print "Error, can't generate enemy's ships"
        return False

    ai_enemy_init()

    set_title_msg(" ~==========|  JBattleShip v1.0 by JKornev  |==========~ ")
    set_battle_left_msg("you")
    set_battle_right_msg("enemy")

    state = 0
    handlers = {
        0 : (start_game_scene_init,     start_game_scene_handler),
        1 : (creating_ships_scene_init, creating_ships_scene_handler),
        2 : (battle_scene_init,         battle_scene_handler)
    }

    # game cycle
    handlers.get(state)[0]() #first init handler
    while (state < len(handlers)):
        update_view()
        value = get_input_value()

        #call handler
        if (handlers.get(state)[1](value) == True):
            state += 1
            #call init handler for next scene
            if (state < len(handlers)):
                handlers.get(state)[0]()
    
    return True

def enable_mobile():
    global c_map_rows, c_map_cols, c_ships_peak_lvl
    c_map_rows = 12
    c_map_cols = 15
    c_ships_peak_lvl = 4
    
def enable_classic():
    global c_map_rows, c_map_cols, c_ships_peak_lvl
    c_map_rows = 10
    c_map_cols = 10
    c_ships_peak_lvl = 4
    
def enable_secret():
    global c_map_rows, c_map_cols, c_ships_peak_lvl
    c_map_rows = 20
    c_map_cols = 17
    c_ships_peak_lvl = 6

def enable_debug():
    global c_debug_mode
    c_debug_mode = 1

if __name__ == "__main__":
    handlers = {"mobile" : enable_mobile, "classic" : enable_classic, "hard" : enable_secret, "debug"  : enable_debug}
    
    for i in xrange(len(sys.argv) - 1):
        handler = handlers.get(sys.argv[i + 1])
        if (handler == None):
            print("Error, invalid argument!")
            exit()
        else:
            handler()
    
    start_game()
