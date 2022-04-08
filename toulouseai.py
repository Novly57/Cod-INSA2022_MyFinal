import random as rd
import numpy
from controller import PlayerInfo, TW_Input, TW_Map, TW_Output, TileType, Weapons
import mouvement
import math

TRAJECTORY_PREDICTION_LOOKBACK = 6
BULLET_SPEED = 4000
TICK_LENGTH = 1/20
RANDOM_SHOOT_CHANCE = 0.1
RAFALE_DISTANCE = 400
SHOTGUN_DIST = 250
SHOTGUN_CHECK_CHANCE = 0.1
GRENADE_CHECK_CHANCE = 0.1
GRENADE_DIST = 250

player_has_shotgun = False
player_has_grenade = False


def our_ai(controls: TW_Input, game_state: TW_Output, enemy_positions, twmap: TW_Map, arg):
    if(game_state.alive):
        hooked = True if controls.hook ==1 else False
        # ne lache pas l'adversaire apres l'avoir
        if not (game_state.local_player.hooked_player == 0):
            controls.hook = 0
        controls = mouvement.movement(controls, game_state, twmap, arg)
        controls = shoot(controls, game_state, enemy_positions, twmap, arg)
        enemy_positions = update_enemy_positions(game_state, enemy_positions)
        if 'map1' in arg:
            if game_state.local_player.pos_y > 550 and not hooked:
                controls = grapin(controls,game_state,twmap)
    else:
        global player_has_shotgun
        global player_has_grenade
        player_has_shotgun = False
        player_has_grenade = False
    return controls


def shoot(controls: TW_Input, game_state: TW_Output, enemy_positions, twmap: TW_Map, argmap):
    player = game_state.local_player
    enemy = game_state.enemy
    state = mouvement.get_move_state(game_state)
    global player_has_shotgun
    global player_has_grenade

    if rd.random() < SHOTGUN_CHECK_CHANCE:
        controls.weapon = Weapons.SHOTGUN.value

    if 'map3' in argmap and rd.random() < GRENADE_CHECK_CHANCE:
        controls.weapon = Weapons.GRENADE.value

    if (player.weapon == Weapons.SHOTGUN.value):
        player_has_shotgun = True
        if (game_state.ammo == 0):
            player_has_shotgun = False

    if (player.weapon == Weapons.GRENADE.value):
        player_has_grenade = True
        if (game_state.ammo == 0):
            player_has_grenade = False

    if not isTrajectoryFree(player, enemy, twmap):

        controls.fire = False
        return controls

    if state == mouvement.Move_state.MELEE:
        controls.weapon = Weapons.HAMMER.value
        if (player_has_shotgun):
            controls.weapon = Weapons.SHOTGUN.value
        if (player_has_grenade):
            controls.weapon = Weapons.GRENADE.value

        controls.angle = get_enemy_direction(
            player, enemy) + math.pi/2
        controls.fire = not controls.fire
        return controls
    elif (state == mouvement.Move_state.FLEE or state == mouvement.Move_state.ATTACK):
        dist = get_distance_to_entity(player, enemy)

        if (player_has_shotgun and dist < SHOTGUN_DIST):
            controls.weapon = Weapons.SHOTGUN.value
        else:
            controls.weapon = Weapons.GUN.value

        if (player_has_grenade and dist < GRENADE_DIST):
            controls.weapon = Weapons.GRENADE.value
        else:
            controls.weapon = Weapons.GUN.value

        controls.angle = predict_trajectory(
            player, enemy, enemy_positions) + math.pi/2

        # close enough -> attack non stop
        if dist < RAFALE_DISTANCE:
            controls.fire = not controls.fire
            if (player.weapon == Weapons.SHOTGUN.value or enemy.weapon != Weapons.SHOTGUN.value):
                controls.angle = get_enemy_direction(
                    player, enemy) + math.pi/2
                controls.hook = 1
        # a little bit farther away -> take it easy
        elif (game_state.ammo > 7 or rd.random() < RANDOM_SHOOT_CHANCE):
            controls.fire = not controls.fire

        return controls

    elif state == mouvement.Move_state.PASSIVE:
        if rd.random() < SHOTGUN_CHECK_CHANCE:
            controls.weapon = Weapons.SHOTGUN.value
        if 'map3' in argmap and rd.random() < GRENADE_CHECK_CHANCE:
            controls.weapon = Weapons.GRENADE.value
        if (player.weapon == Weapons.SHOTGUN.value):
            player_has_shotgun = True
            if (game_state.ammo == 0):
                player_has_shotgun = False

        if (player.weapon == Weapons.GRENADE.value):
            player_has_grenade = True
            if (game_state.ammo == 0):
                player_has_grenade = False
        controls.fire = False
        enemy_positions = []
        return controls
    else:
        return controls


def get_enemy_direction(player: PlayerInfo, enemy: PlayerInfo):
    dir_enemy = math.atan2(-(enemy.pos_y-player.pos_y),
                           enemy.pos_x-player.pos_x)
    dir_enemy %= 2*math.pi
    return dir_enemy


def predict_trajectory(player: PlayerInfo, enemy: PlayerInfo, enemy_positions):
    dir_enemy = get_enemy_direction(player, enemy)

    (vx, vy) = predict_enemy_pos(enemy_positions)

    dir_movement_enemy = math.atan2(-vy, vx)
    dir_movement_enemy %= 2*math.pi

    phi = dir_movement_enemy - dir_enemy
    alpha = (vx**2 + vy**2)**0.5 / BULLET_SPEED  # (enemy speed / bullet speed)
    beta = alpha * math.sin(phi)

    # bullet cant reach enemy
    if abs(beta) >= 1:
        return 0.0

    shoot_angle = dir_enemy + math.asin(beta)
    return shoot_angle


def predict_enemy_pos(enemy_positions):
    N = len(enemy_positions)
    if N < TRAJECTORY_PREDICTION_LOOKBACK:
        return (0, 0)

    pos_x = [enemy_positions[i][0] for i in range(N)]
    pos_y = [enemy_positions[i][1] for i in range(N)]

    next_enemy_x = numpy.poly1d(numpy.polyfit(range(N), pos_x, 3))(N)
    next_enemy_y = numpy.poly1d(numpy.polyfit(range(N), pos_y, 2))(N)

    current_enemy_x = enemy_positions[-1][0]
    current_enemy_y = enemy_positions[-1][1]

    return ((next_enemy_x - current_enemy_x)/TICK_LENGTH, (next_enemy_y-current_enemy_y)/TICK_LENGTH)


def update_enemy_positions(game_state: TW_Output, enemy_positions):
    enemy_positions.append((game_state.enemy.pos_x, game_state.enemy.pos_y))
    if len(enemy_positions) > TRAJECTORY_PREDICTION_LOOKBACK:
        enemy_positions.pop(0)
    return enemy_positions


def get_distance_to_entity(origin: PlayerInfo, target: PlayerInfo):
    return ((target.pos_x - origin.pos_x)**2 + (target.pos_y - origin.pos_y)**2)**0.5


def isTrajectoryFree(origin: PlayerInfo, target: PlayerInfo, twmap: TW_Map):
    originPos = origin.pos_x//32, origin.pos_y//32
    targetPos = target.pos_x//32, target.pos_y//32
    dist = math.floor(((targetPos[1] - originPos[1])
                       ** 2 + (targetPos[0] - originPos[0])**2)**0.5 + 0.5)

    if dist == 0:
        return True

    dy = (targetPos[1] - originPos[1]) / dist
    dx = (targetPos[0] - originPos[0]) / dist

    try:
        trace = [float(originPos[0]), float(originPos[1])]
        for _ in range(dist):
            block = twmap.grid[int(trace[1])][int(trace[0])].value
            if (block == TileType.GROUND.value or block == TileType.SPIKE.value or block == TileType.GROUND_NON_HOOKABLE.value):
                return False
            trace[0] += dx
            trace[1] += dy
        return True
    except:
        return False

def grapin(controls: TW_Input, game_state: TW_Output,twmap: TW_Map):
    # angle Gauche x = 435 y = 529
    # angle Droit x = 1126 y = 529
    positionPlayer = game_state.local_player.pos_x,game_state.local_player.pos_y
    if positionPlayer[0]<(435+1126)//2: # on est a gauche
        dir_grap = math.atan2(-(529 - game_state.local_player.pos_y),435 - game_state.local_player.pos_x)
        dir_grap %= 2 * math.pi
        controls.angle = dir_grap + math.pi/2
        controls.hook = 1
    else :
        dir_grap = math.atan2(-(529 - game_state.local_player.pos_y), 1126 - game_state.local_player.pos_x)
        dir_grap %= 2 * math.pi
        controls.angle = dir_grap + math.pi/2
        controls.hook = 1
    return controls
