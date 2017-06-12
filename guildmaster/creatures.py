'''
Base classes and functions for creatures, NPCs and enemies
'''
import yaml
from random import choice, randint
from .config import LIGHT0, BRIGHT_RED, FADED_RED, BRIGHT_YELLOW, FADED_GREEN
from .config import BRIGHT_ORANGE, BRIGHT_PURPLE, LEVEL_UP_XP_MULTIPLIER
from .utils import roll, SkillCheckResult, GameObject, Message


# load the enemy definitions
enemies = yaml.load(open('guildmaster/gamedata/enemies.yaml', 'r'))


class Creature(GameObject):
    '''Base class for a creature. Must be subclasses to be used'''
    XP_yield = None
    size = None
    race = None
    type = None
    name = None
    alive = True
    vision = (0, 0)
    agro_range = 0
    player_character = False

    def __init__(self, STR=1, DEX=1, INT=1, VIT=1,
                 MAX_HP=1, MAX_FOCUS=0, x=1, y=1, char='@',
                 colour=(0, 0, 0), block_move=True):
        super().__init__(x, y, char, colour, block_move)

        self.MAX_HP = MAX_HP
        self.HP = MAX_HP
        self.MAX_FOCUS = MAX_FOCUS
        self.FOCUS = MAX_FOCUS
        self.consious = True
        self.stunned = False

        self.STR = STR
        self.DEX = DEX
        self.INT = INT
        self.VIT = VIT

        self.equipment = {
            'head': None, 'chest': None,
            'main': None, 'offhand': None,
            'hands': None, 'feet': None,
            'legs': None, 'cloak': None,
            'belt': None, 'necklace': None,
            'ring1': None, 'ring2': None
        }
        self.pack = []

    @property
    def AC(self):
        '''AC reduces damage on hit'''
        AC = 0
        for item in self.equipment.values():
            if hasattr(item, 'AC_base'):
                AC += item.AC_base
        return AC

    @property
    def EV(self):
        '''Evaison gives a change to avoid attacks'''
        EV = 0
        dex_mod = self.DEX
        for item in self.equipment.values():
            if hasattr(item, 'dex_mod'):
                item_dex_mod = item.dex_mod(self)
                dex_mod = min(dex_mod, item_dex_mod)

        return EV + dex_mod

    def skill_check(self, stat, DC, modifier=0):
        '''
        Make a skill check against a base stat. Additional modifiers are
        applied by the caller.
        '''
        result = roll()

        if result == 1:
            return SkillCheckResult(success=False, crit=True)
        if result == 20:
            return SkillCheckResult(success=True, crit=True)

        result = result + getattr(self, stat) + modifier

        if result >= DC:
            return SkillCheckResult(success=True, crit=False)
        else:
            return SkillCheckResult(success=False, crit=False)

    def move_or_melee(self, dx, dy, screen):
        '''Move to a new cell or attack the creature in it'''
        new_x = self.x + dx
        new_y = self.y + dy

        if self.player_character:
            for obj in screen.current_map.objects:
                if obj.alive and obj.x == new_x and obj.y == new_y:
                    attack_messages = self.basic_attack(obj, screen)
                    return attack_messages
        else:
            if screen.player.x == new_x and screen.player.y == new_y:
                attack_messages = self.basic_attack(screen.player, screen)
                return attack_messages

        # Nothing to attack so just try to move
        interaction_messages = self.move(dx, dy, screen)
        return interaction_messages

    def basic_attack(self, target, screen):
        '''
        Make a basic attack against a target. Modifiers and base damage
        must be set in subclasses.
        '''
        messages = []
        weapon = self.equipment.get('main')
        mod = weapon.atk_mod if weapon is not None else 0

        success, crit = self.skill_check('STR', target.AC, mod)
        if success:
            if crit:
                if not weapon:
                    damage = 5
                else:
                    damage = weapon.crit()
            else:
                if not weapon:
                    damage = 1
                else:
                    damage = weapon.damage()
            if crit:
                msg = '{} crit {} for {} damage!'
            else:
                msg = '{} hit {} for {} damage'
            messages.append(
                Message(msg.format(self.name, target.name, damage), LIGHT0))
            target_messages, target_died = target.lose_hp(damage)
            if target_died and self.player_character:
                self.current_xp += target.XP_yield
                if self.current_xp >= self.next_level:
                    self.level_up()
                screen.send_enemy_to_back(target)

            messages.extend(target_messages)
        return messages

    def equip(self, item, slot):
        '''Attempt to equip an item'''
        messages = []
        current = self.equipment.get(slot)
        if current is not None:
            self.pack.append(current)
        self.equipment[slot] = item
        # Handle effects on equip (identify, curse etc...)
        equip_messages = item.on_equip(self)
        messages.append(
            Message('{} equipped {}'.format(self.name, item.name), LIGHT0))
        messages.extend(equip_messages)
        return messages

    def lose_hp(self, damage):
        '''Take a hit and check for death'''
        messages = []
        died = False

        self.HP -= damage
        if self.HP <= 0:
            self.die()
            died = True
            messages.append(Message('{} died'.format(self.name), BRIGHT_RED))
        else:
            if self.player_character:
                self.set_colour()
        return messages, died

    def set_colour(self):
        '''Set the player colour based on health'''
        if self.HP / self.MAX_HP >= 0.75:
            self.colour = LIGHT0
        elif self.HP / self.MAX_HP >= 0.50:
            self.colour = BRIGHT_YELLOW
        elif self.HP / self.MAX_HP >= 0.25:
            self.colour = BRIGHT_ORANGE
        elif self.HP / self.MAX_HP < 0.25:
            self.colour = BRIGHT_RED

    def rest(self):
        '''Recover HP and SP from resting'''
        if self.HP < self.MAX_HP:
            hp = roll(self.hit_dice) // 2
            messages = self.heal(hp)
        else:
            messages = []

        if self.MAX_FOCUS > 0 and (self.FOCUS < self.MAX_FOCUS):
            focus_messages = self.recover_focus(1)
            messages.extend(focus_messages)

        if len(messages) == 0:
            # Already max HP and SP
            msg = Message('You already feel well rested', LIGHT0)
            messages.append(msg)

        return messages

    def heal(self, amount):
        '''heal up to self.MAX_HP'''
        self.HP += amount

        if self.HP > self.MAX_HP:
            self.HP = self.MAX_HP

        if self.player_character:
            self.set_colour()

        msg = Message('{} recovered {} hit points'.format(self.name, amount),
                      LIGHT0)
        return [msg]

    def recover_focus(self, amount):
        '''recover focus points up to MAX_FOCUS'''
        self.FOCUS += amount

        if self.FOCUS > self.MAX_FOCUS:
            self.FOCUS = self.MAX_FOCUS

        msg = Message('{} recovered {} spell points'.format(self.name, amount),
                      LIGHT0)
        return [msg]

    def die(self):
        '''Deal with creature death'''
        self.char = '%'
        self.colour = FADED_RED
        self.block_move = False
        self.alive = False

    def level_up(self):
        '''Deal with level up'''
        # Reset XP bar and bump level counter
        self.current_xp -= self.next_level
        self.next_level *= LEVEL_UP_XP_MULTIPLIER
        self.next_level = int(self.next_level)
        self.level += 1

        # Increase HP
        hp_up = roll(self.hit_dice) + getattr(self, 'VIT')
        self.MAX_HP += hp_up
        self.HP += hp_up

        # Increase Focus
        focus_up = roll(self.focus_dice) + getattr(self, 'INT')
        self.MAX_FOCUS += focus_up
        self.FOCUS += focus_up

        # TODO : class based perks / abilities
        #        spell slot increase etc

    def use_item(self, item):
        '''Use an item'''
        return [Message('You need to implement using items!', BRIGHT_PURPLE)]

    def search(self, map):
        '''Search in all adjacent squares for traps and hidden doors'''
        messages = []
        # TODO: add in modifiers from equipment? (maybe handle in skill check)
        #       look for traps
        res = self.skill_check('INT', 20)
        if res.success:
            for tile in map.neighbouring_tiles(self.x, self.y):
                if tile.name == 'secret_door':
                    tile.closed_door()
                    messages.append(
                        Message('You found a secret door!', LIGHT0))
        return messages

    def act(self, screen):
        '''Basic AI'''
        if not self.alive:
            return []

        floor = screen.current_map
        messages = []
        current_agro = floor.lmap[self.y][self.x].agro_weight
        if current_agro <= self.agro_range:
            dx, dy = 0, 0
            options = floor.neighbouring_tiles(self.x, self.y,
                                               include_offsets=True)
            for offset, tile in options:
                if tile.agro_weight < current_agro and not tile.block_move:
                    dx, dy = offset
                    # x, y = self.x + dx, self.y + dy
                    current_agro = tile.agro_weight
        else:
            dx, dy = randint(-1, 1), randint(-1, 1)

        messages = self.move_or_melee(dx, dy, screen)
        return messages


def enemy(name, x, y):
    '''Create a new enemy'''
    conf = enemies[name]
    STR, DEX, INT, VIT = conf['stats']
    enemy = Creature(
        STR=STR, DEX=DEX, INT=INT, VIT=VIT, MAX_HP=conf['hp'],
        MAX_FOCUS=conf['focus'], x=x, y=y, char=conf['character'],
        colour=FADED_GREEN)
    # XXX: this needs to convert str to var
    # colour=conf['colour'])
    enemy.XP_yield = conf['xp']
    enemy.size = conf['size']
    enemy.race = name
    enemy.type = conf['type']
    enemy.name = name
    enemy.size = conf['size']
    enemy.vision = tuple(conf['vision'])
    enemy.agro_range = conf['agroRange']

    for equipment_type, options in conf['equipment'].items():
        enemy.equipment['equipment_type'] = choice(options)

    return enemy
