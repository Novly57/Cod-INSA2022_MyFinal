XX = [-1]
YY = [-1]
ZONEZONE = ""
next_obj = None
previous_zone = ""
ARGMAP = ''

def setARGMAP(argMap):
    global ARGMAP
    ARGMAP = argMap


def filter_entities_by_map(entities, argmap):
    if 'map1' in argmap:
        return [entity for entity in entities if entity.pos_y < 529]
    if 'map2' in argmap:
        return [entity for entity in entities if entity.pos_y > 335 and not (1105<entity.pos_y<1361 and 1895<entity.pos_x<3910)]
    else:
        return entities

def dist(X,Y,X1,Y1):
    return ((X - X1)**2 + (Y - Y1)**2)**(1/2)

def get_nearest_between_two(X,Y,X1,Y1,X2,Y2):
    dist1 = dist(X,Y,X1,Y1)
    dist2 = dist(X,Y,X2,Y2)
    if dist1>dist2:
        return X2,Y2
    else:
        return X1,Y1

def get_zone(X,Y):
    if Y < 280:
        return "ZONE_1"
    elif Y<410 and X > 1015:
        return "ZONE_2"
    elif Y<410 and X < 563:
            return "ZONE_3"
    else:
        return "ZONE_4"

def print_pos(game_state):
    global ZONEZONE
    player = game_state.local_player
    X, Y = player.pos_x, player.pos_y
    if (XX[0] != X):
        XX[0] = X
    if (YY[0] != Y):
        YY[0] = Y
    if (ZONEZONE != get_zone(X,Y)):
        ZONEZONE = get_zone(X,Y)

def getTrueDest(player, X, Y):
    global ARGMAP
    if ('map1' in ARGMAP):
        global previous_zone
        global next_obj
        if previous_zone != get_zone(player.pos_x, player.pos_y):
            next_obj = None
        previous_zone = get_zone(player.pos_x, player.pos_y)
        if next_obj != None:
            return next_obj
        return calculate_true_dest(player, X, Y)
    else:
        return X,Y

def calculate_true_dest(player, X, Y):
    if get_zone(X,Y) != get_zone(player.pos_x, player.pos_y):
        if get_zone(player.pos_x, player.pos_y) == "ZONE_1":
            return get_nearest_between_two(X, Y, 560, 369, 1016, 369)
        if get_zone(player.pos_x, player.pos_y) == "ZONE_2" and get_zone(X,Y) == "ZONE_4":
            return get_nearest_between_two(X, Y, 959, 529, 1244, 529)
        if get_zone(player.pos_x, player.pos_y) == "ZONE_2" and get_zone(X,Y) == "ZONE_1":
            second_obj = 904, 273
            premier_obj = 1020, 369
            if (player.pos_x, player.pos_y) != premier_obj:
                return premier_obj
            else:
                next_obj = second_obj
                return second_obj
        if get_zone(player.pos_x, player.pos_y) == "ZONE_3" and get_zone(X,Y) == "ZONE_4":
            return get_nearest_between_two(X, Y, 326, 529, 623, 529)
        if get_zone(player.pos_x, player.pos_y) == "ZONE_3" and get_zone(X,Y) == "ZONE_1":
            second_obj = 670, 273
            premier_obj = 560, 369
            if (player.pos_x, player.pos_y) != premier_obj:
                return premier_obj
            else:
                next_obj = second_obj
                return second_obj
        if get_zone(player.pos_x, player.pos_y) == "ZONE_4" and get_zone(X,Y) == "ZONE_1":
            second_obj = 1020, 369
            premier_obj = 959, 529
            if (player.pos_x, player.pos_y) != premier_obj:
                return premier_obj
            else:
                next_obj = second_obj
                return second_obj
        if get_zone(player.pos_x, player.pos_y) == "ZONE_4" and get_zone(X,Y) == "ZONE_2":
            second_obj = get_nearest_between_two(X, Y, 1020, 369, 1191, 401)
            premier_obj = get_nearest_between_two(second_obj[0], second_obj[1], 959, 529, 1244, 529)
            if (player.pos_x, player.pos_y) != premier_obj:
                return premier_obj
            else:
                next_obj = second_obj
                return second_obj
        if get_zone(player.pos_x, player.pos_y) == "ZONE_4" and get_zone(X,Y) == "ZONE_3":
            second_obj = get_nearest_between_two(X, Y, 372, 401, 560, 369)
            premier_obj = get_nearest_between_two(second_obj[0], second_obj[1], 326, 529, 623, 529)
            if (player.pos_x, player.pos_y) != premier_obj:
                return premier_obj
            else:
                next_obj = second_obj
                return second_obj
        else:
            return X,Y
    else:
        return X,Y
