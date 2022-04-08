from controller import TW_Input, TW_Output, TileType, Weapons
from enum import Enum
import random as rd
from pathFind import *
import toulouseai

tick = 0
first_y = -1000

need_shotgun = True
shotgun_cooldown = 0

jumped_this_turn = False
jumped_last_turn = False

MELEE_DISTANCE = 64
FLEE_DISTANCE = 250
ATTACK_DISTANCE = 600
RANDOM_JUMP_CHANCE = 0.1


def set_first_y(Y):
    global first_y
    if first_y == -1000:
        first_y = Y


def upTick():
    global tick
    tick += 1


def getTick(controls):
    global tick
    if first_y < 500:
        if (tick < 60):
            return predef(tick, controls)
        else:
            return controls
    else:
        if (tick < 80):
            return predef2(tick, controls)
        else:
            return controls
    return controls


def predef(tick, controls):
    if tick < 16:
        controls.direction = 1
        controls.jump = 0
        return controls
    if tick < 25:
        controls.direction = 0
        controls.jump = 0
        return controls
    if tick < 27:
        controls.direction = -1
        controls.jump = 0
        return controls
    if tick < 29:
        controls.direction = 0
        controls.jump = 0
        return controls
    if tick < 34:
        controls.direction = -1
        controls.jump = 0
        return controls
    if tick < 39:
        controls.direction = -1
        controls.jump = 1
        return controls
    if tick < 43:
        controls.direction = -1
        controls.jump = 0
        return controls
    if tick < 48:
        controls.direction = -1
        controls.jump = 1
        return controls
    if tick < 60:
        controls.direction = -1
        controls.jump = 0
        return controls


def predef2(tick, controls):
    if tick < 20:
        controls.direction = 1
        controls.jump = 0
        return controls
    if tick < 23:
        controls.direction = 1
        controls.jump = 1
        return controls
    if tick < 38:
        controls.direction = 1
        controls.jump = 0
        return controls
    if tick < 49:
        controls.direction = -1
        controls.jump = 0
        return controls
    if tick < 54:
        controls.direction = -1
        controls.jump = 1
        return controls
    if tick < 59:
        controls.direction = -1
        controls.jump = 0
        return controls
    if tick < 67:
        controls.direction = -1
        controls.jump = 1
        return controls
    if tick < 80:
        controls.direction = -1
        controls.jump = 0
        return controls


def jump_this_turn():
    global jumped_this_turn
    jumped_this_turn = True


def should_jump_this_turn():
    global jumped_this_turn
    global jumped_last_turn
    if jumped_this_turn:
        if not jumped_last_turn:
            jumped_last_turn = True
            jumped_this_turn = False
            return True
    jumped_this_turn = False
    jumped_last_turn = False
    return False


def check_shotgun(controls):
    global need_shotgun
    global shotgun_cooldown
    if shotgun_cooldown == 0:
        controls.weapon = 3
        shotgun_cooldown = 100
    else:
        controls.weapon = 0
        shotgun_cooldown -= 1


def update_shotgun_status(game_state):
    global need_shotgun
    if game_state.local_player.weapon == 3:
        if game_state.ammo < 3:
            need_shotgun = True
        else:
            need_shotgun = False


class Move_state(Enum):
    PASSIVE = 0
    ATTACK = 1
    MELEE = 2
    FLEE = 3


def isWall(tileValue):
    return tileValue == TileType.GROUND.value or tileValue == TileType.GROUND_NON_HOOKABLE.value or tileValue == TileType.SPIKE.value


def checkForWall(controls, game_state, twmap):
    positionPlayer = game_state.local_player.pos_x//32, game_state.local_player.pos_y//32
    if positionPlayer[0] > 0 and positionPlayer[1] > 0 and positionPlayer[0] < twmap.width and positionPlayer[1] < twmap.height:
        if isWall(twmap.grid[positionPlayer[1]][positionPlayer[0] + controls.direction].value):
            jump_this_turn()


def set_controls_from_coord(controls, game_state, X, Y, twmap):
    player = game_state.local_player
    X, Y = getTrueDest(player, X, Y)
    if X < player.pos_x:
        controls.direction = -1
    else:
        controls.direction = 1
    if Y < player.pos_y:
        jump_this_turn()
    return controls


def FindHealth(controls: TW_Input, game_state: TW_Output, twmap, argmap):
    player = game_state.local_player
    update_shotgun_status(game_state)
    mindist = 1000
    goto = None
    for entity in filter_entities_by_map(game_state.entities, argmap):
        # si l'entité est de la vie ou du shield
        if (entity.type == 0 or entity.type == 1):
            distance = abs(entity.pos_x - player.pos_x) + \
                abs(entity.pos_y - player.pos_y)
            # recherche de la plus proche
            if distance < mindist:
                mindist = distance
                goto = entity
    # si une entité est trouvée
    if goto is not None:
        X, Y = goto.pos_x, goto.pos_y
        controls = set_controls_from_coord(controls, game_state, X, Y, twmap)
        return controls
    else:
        return None


def FindWeapon(controls: TW_Input, game_state: TW_Output, twmap, argmap):
    player = game_state.local_player
    mindist = 1000
    goto = None
    for entity in filter_entities_by_map(game_state.entities, argmap):
        # si l'entité est de la vie ou du shield
        global need_shotgun
        if entity.type != 0 and entity.type != 1 and (not toulouseai.player_has_shotgun or entity.type != 7) and (not toulouseai.player_has_grenade or entity.type != 8):
            distance = abs(entity.pos_x - player.pos_x) + \
                abs(entity.pos_y - player.pos_y)
            # recherche de la plus proche
            if distance < mindist:
                mindist = distance
                goto = entity
    # si une entité est trouvée
    if goto is not None:
        X, Y = goto.pos_x, goto.pos_y
        controls = set_controls_from_coord(controls, game_state, X, Y, twmap)
        return controls
    else:
        return None


def Wait(controls: TW_Input, game_state: TW_Output, twmap):
    """Etat d'attente, sauts + petits déplacements latéraux aléatoire"""
    if rd.random() < 0.5:
        controls.direction = 1
    else:
        controls.direction = -1
    if rd.random() > 0.7:
        jump_this_turn()
    else:
        pass
    return controls


def movement(controls: TW_Input, game_state: TW_Output, twmap, argMap):
    upTick()
    set_first_y(game_state.local_player.pos_y)
    setARGMAP(argMap)
    move_state = get_move_state(game_state)
    enemy_dist = get_distance_to_entity(game_state, game_state.enemy)
    # passif
    if move_state.value == move_state.PASSIVE.value or (move_state.value == move_state.FLEE.value and enemy_dist > FLEE_DISTANCE):
        if game_state.health < 5:
            # recherche de vie
            tempo = FindHealth(controls, game_state, twmap, argMap)
            # si de la vie est trouvée
            if tempo is not None:
                controls = tempo
            # sinon
            else:
                Wait(controls, game_state, twmap)
        # recherche d'arme
        else:
            if ('map3' not in argMap and not toulouseai.player_has_shotgun) or ('map3' in argMap and not toulouseai.player_has_grenade):
                tempo = FindWeapon(controls, game_state, twmap, argMap)
                if tempo is not None:
                    controls = tempo
            else:
                Wait(controls, game_state, twmap)
    elif move_state.value == move_state.FLEE.value:  # combat distance
        if game_state.local_player.pos_x > game_state.enemy.pos_x:
            controls.direction = 1
        else:
            controls.direction = -1
    elif move_state.value == move_state.ATTACK.value:
        X, Y = game_state.enemy.pos_x, game_state.enemy.pos_y
        controls = set_controls_from_coord(controls, game_state, X, Y, twmap)
    else:  # melee
        if game_state.enemy.weapon != Weapons.SHOTGUN:
            if game_state.local_player.pos_x < game_state.enemy.pos_x:
                controls.direction = 1
            else:
                controls.direction = -1
        else:
            if game_state.local_player.pos_x > game_state.enemy.pos_x:
                controls.direction = 1
            else:
                controls.direction = -1
    if 'map1' in argMap and game_state.local_player.pos_x > 1270:
        controls.direction = -1
        jump_this_turn()
    if 'map1' in argMap and game_state.local_player.pos_x < 315:
        controls.direction = 1
        jump_this_turn()
    checkForWall(controls, game_state, twmap)
    if rd.random() < RANDOM_JUMP_CHANCE:
        jump_this_turn()
    if should_jump_this_turn():
        controls.jump = 1
    else:
        controls.jump = 0
    if 'map2' in argMap:
        player = game_state.local_player
        if player.pos_x < 1785 and player.pos_y < 817:
            controls.direction = 1
        if player.pos_x > 4010 and player.pos_y < 817:
            controls.direction = -1
        if 2500 > player.pos_x > 1900:
            controls.direction = -1
        if 3915 > player.pos_x > 3500:
            controls.direction = 1
    if 'map3' in argMap:
        player = game_state.local_player
        controls = getTick(controls)
        if player.pos_x < 500:
            controls.direction = 1
    check_shotgun(controls)
    return controls


def get_move_state(game_state: TW_Output):
    if (not game_state.enemy.visible):
        return Move_state.PASSIVE

    enemy_dist = get_distance_to_entity(game_state, game_state.enemy)

    if (game_state.health + game_state.armor) >= 9 and enemy_dist >= MELEE_DISTANCE:
        return Move_state.ATTACK
    if (game_state.health + game_state.armor) <= 4 and enemy_dist >= MELEE_DISTANCE:
        return Move_state.FLEE
    if game_state.enemy.weapon != Weapons.SHOTGUN.value and enemy_dist >= MELEE_DISTANCE:
        return Move_state.FLEE

    if enemy_dist < MELEE_DISTANCE:
        return Move_state.MELEE
    elif enemy_dist < FLEE_DISTANCE:
        return Move_state.FLEE
    elif enemy_dist < ATTACK_DISTANCE:
        return Move_state.ATTACK
    else:
        return Move_state.PASSIVE


def get_distance_to_entity(gamestate, entity):
    player = gamestate.local_player
    return ((entity.pos_x - player.pos_x) ** 2 + (entity.pos_y - player.pos_y) ** 2) ** (1 / 2)
