import csv
import pathlib
import select
import socket
import sys
from time import *
from dataclasses import dataclass
from typing import List, Tuple
from math import pi
from enum import Enum
import toulouseai

def timeit(message):
    print(f"{[time()]} {message}")


class Directions(Enum):
    LEFT = -1
    NEUTRAL = 0
    RIGHT = 1


class Hook(Enum):
    """ État du grappin """
    IDLE = 0
    RETRACT_START = 1
    UNUSED = 2
    RETRACT_END = 3
    FLYING = 4
    GRABBED = 5
    RETRACTED = 6


class Weapons(Enum):
    DEFAULT = 0
    HAMMER = 1
    GUN = 2
    SHOTGUN = 3
    GRENADE = 4
    LASER = 5
    NINJA = 6


class Entities(Enum):
    PICKUP_HEALTH = 0
    PICKUP_ARMOR = 1
    PICKUP_GRENADE = 2
    PICKUP_SHOTGUN = 3
    PICKUP_LASER = 4
    PICKUP_NINJA = 5

    PROJECTILE_GUN = 6
    PROJECTILE_SHTOTGUN = 7
    PROJECTILE_GRENADE = 8
    PROJECTILE_LASER = 9


@dataclass
class PlayerInfo:
    visible: bool = False         # Vrai si l'ennemi est visible sur la caméra
    just_attacked: bool = False   # Vrai si l'ennemi a attaqué depuis le dernier input
    weapon: int = 0               # Numéro de l'arme que le personnage a en main
    pos_x: int = 0                # Position du personnage sur l'axe X
    pos_y: int = 0                # Position du personnage sur l'axe Y

    angle: float = 0              # Angle de tir, entier entre 0 et 2*pi
    direction: int = 0            # Direction de déplacement
    # -1 = gauche, 0, 1 = droite

    hook_state: int = 0           # Rétracté -1, Au repos 0, 1-3 Rétractation en cours, Lancé 4, Accroché 5
    hooked_player: int = 0        # -1 Si vous n'avez agrippé aucun joueur, 1 sinon
    hook_x: int = 0               # Position X du bout du grappin
    hook_y: int = 0               # Position Y du début du grappin

    def __str__(self):
        return f"Player @ ({self.pos_x},{self.pos_y}) to {Directions(self.direction).name} angle {self.angle}rad" \
               f"with {Weapons(self.weapon).name} {'attacked'*self.just_attacked} hook {Hook(self.hook_state).name} @ ({self.hook_x},{self.hook_y}) player {self.hooked_player}"


@dataclass
class Entity:
    pos_x: int = 0          # Position de l'entité sur X
    pos_y: int = 0          # Position de l'entité sur Y
    type: int = 0           # Type d'entité

    def __str__(self):
        return f"{Entities(self.type).name} : ({self.pos_x},{self.pos_y})"


@dataclass
class TW_Output:
    local_player: PlayerInfo # Informations sur le joueur que vous contrôlez
    enemy: PlayerInfo        # Informations sur le joueur ennemi
    entities: List[Entity]   # Liste des entités visibles

    health: int = 0          # Nombre de coeurs restants <= 10
    armor: int = 0           # Nombre de points d'armure <= 10
    ammo: int = 0            # Nombre de coups restants pour l'arme tenue en main
    alive: bool = True       # Vrai si votre joueur est en vie

    def __str__(self):
        if self.alive:
            return f"{self.health}HP {self.armor}DEF {self.ammo}AMMO\n" \
                   f"Local player {self.local_player}\n" \
                   f"Enemy {'visible' * self.enemy.visible + 'invisible' * (not self.enemy.visible)} {self.enemy}\n"
        else:
            return f"mort :'(\n"


@dataclass
class TW_Input:
    direction: int = 0      # Direction de déplacement ; 0 pour neutre, -1 pour gauche et 1 pour droite
    jump: bool = False      # Saut ; False non activé, True activé
    fire: bool = 0          # Arme 1 (clic gauche) ; 0 non activé, 1 activé
    hook: bool = 0          # Grappin (clic droit; 0 non activé, 1 activé
    weapon: int = 0         # Arme équipée, entre 1 et 4
    angle: float = 0        # Angle du pointeur pour la visée entier entre 0 et et 2pi

    def __str__(self):
        return f"Input to {Directions(self.direction).name} angle {self.angle}rad with {Weapons(self.weapon).name}" \
               f"{self.fire * 'fire'} {self.hook * 'hook'} {self.jump * 'jump'}"

class TileType(Enum):
    AIR = "0"
    GROUND = "1"
    SPIKE = "2"
    GROUND_NON_HOOKABLE = "4"
    SPAWN_LOCATION = "192"
    SHIELD = "197"
    HEART = "198"
    SHOTGUN = "199"
    GRENADE = "200"
    NINJA = "201"
    LASER = "202"

class TW_Map():
    height: int = 0             # La hauteur de la carte en nombre de cases
    width: int = 0              # La largeur de la carte en nombre de cases

    # La carte sous la forme d'une liste de liste.
    #
    # On représente donc la grille comme une liste de ligne, chaque ligne est
    # une liste de case, représentant le type de surface.
    # Pour rappel, chaque case fait 32x32 pixels.
    grid: List[List[TileType]]

    def __init__(self, filename):
        with open(filename, "r") as f:
            lines = list(csv.reader(f))
            self.width, self.height = map(int, lines[0])
            self.grid = [[TileType(k) for k in line] for line in lines[1:]]

    def __str__(self):
        grid = "\n".join([' '.join([tile.value for tile in line]) for line in self.grid])
        return f"{self.width} x {self.height}\n{grid}"

class Connector:
    """
    Utilisé pour faire la liaison avec le client : ouvre un socket et communique avec lui
    """

    def __init__(self, address: Tuple[str, int], buffer_size: int, verbose: bool):
        self.address = address
        self.buffer_size = buffer_size
        self.verbose = verbose
        self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

    def send_input(self, input: TW_Input):
        """
        Envoie l'input donné en argument vers le client
        """
        parsed = str.encode(f"{input.direction}:{int(input.jump)}:{int(input.fire)}:{int(input.hook)}:{input.weapon}:{input.angle:.2f}")
        self.socket.sendto(parsed, self.address)

        if self.verbose:
            timeit(f"Send {parsed}")

    def message_waiting(self):
        """
        Retourne vrai si un message envoyé par le client attend d'être lu
        """
        readable, _, _ = select.select([self.socket], [], [self.socket], 0)
        return len(readable) > 0

    def get_output(self, output: TW_Output):
        """
        Met à jour l'état du jeu en fonction des données transmises par le client
        """
        response, _ = self.socket.recvfrom(self.buffer_size)
        response = response.decode()
        if self.verbose:
            timeit(f"Receive {response}")

        if response == "-1":
            output.alive = False
            return
        output.alive = True

        response = response.split(";")

        num_players = int(response[0])
        player1 = map(int, response[1].split(":"))

        output.health = next(player1)
        output.armor = next(player1)
        output.ammo = next(player1)

        output.local_player.weapon = next(player1)
        output.local_player.pos_x = next(player1)
        output.local_player.pos_y = next(player1)
        output.local_player.angle = (next(player1) / 256) % (2 * pi)
        output.local_player.direction = next(player1)
        output.local_player.hooked_player = next(player1)
        output.local_player.hook_state = next(player1)
        output.local_player.hook_x = next(player1)
        output.local_player.hook_y = next(player1)

        if num_players >= 2:
            player2 = map(int, response[2].split(":"))
            output.enemy.visible = True

            output.enemy.weapon = next(player2)
            output.enemy.pos_x = next(player2)
            output.enemy.pos_y = next(player2)
            output.enemy.angle = (next(player2) / 256) % (2 * pi)
            output.enemy.direction = next(player2)
            output.enemy.just_attacked = (next(player2) == 1)

            output.enemy.hooked_player = next(player2)
            output.enemy.hook_state = next(player2)
            output.enemy.hook_x = next(player2)
            output.enemy.hook_y = next(player2)
        else:
            output.enemy.visible = False

        num_entities = int(response[num_players + 1])

        output.entities = []
        for i in range(num_entities):
            parsed_entity = map(int, response[num_players + 2 + i].split(":"))
            output.entities.append(Entity(type=next(parsed_entity),
                                          pos_x=next(parsed_entity),
                                          pos_y=next(parsed_entity)))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python controller.py <chemin_vers_la_map>")
        print("")
        print("Par exemple, pour lancer la map 1, on utilisera: ")
        print("> python controller.py ../maps/map1.csv")
        print("Ou bien depuis la racine du répertoire: ")
        print("> python controller/controller.py maps/map1.csv")
        sys.exit(0)

    print(f"Chargement de la map {sys.argv[1]} ...")
    twmap = TW_Map(pathlib.Path(sys.argv[1]))

    connector = Connector(address=("127.0.0.1", 5000), buffer_size=1024, verbose=False)
    game_state = TW_Output(PlayerInfo(), PlayerInfo(), [])
    controls = TW_Input()

    connector.send_input(controls)      # On envoie des inputs neutres pour l'initialisation

    timeit("Tentative de connexion avec le client...")
    connector.get_output(game_state)    # Puis on attend un premer retour du client

    timeit("Connexion avec le client établie")
    last = time()

    controls.weapon = Weapons.GUN.value

    enemy_positions = []

    # Boucle principale du connecteur
    while True:

        # Envoi des inputs au client à une fréquence max de 20Hz pour éviter le buffering
        if time() - last > 0.05:
            try:
                controls = toulouseai.our_ai(controls, game_state, enemy_positions, twmap, sys.argv[1])
            except:
                controls = controls
            connector.send_input(controls)
            last = time()

        # On attend un retour du client
        connector.get_output(game_state)
        while connector.message_waiting():      # Tant qu'on a une update du client à lire...
            connector.get_output(game_state)    # ...on met à jour l'état du jeu
