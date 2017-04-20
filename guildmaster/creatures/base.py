'''
Base classes and functions for creatures, NPCs and enemies
'''
from random import choice
from ..config import LIGHT0, BRIGHT_RED, FADED_RED, BRIGHT_YELLOW
from ..config import BRIGHT_ORANGE, BRIGHT_PURPLE, LEVEL_UP_XP_MULTIPLIER
from ..utils import roll, SkillCheckResult, GameObject, Message


class Creature(GameObject):
    '''Base class for a creature. Must be subclasses to be used'''
    XP_yield = None
    size = None
    race = None
    type = None
    name = None
    alive = True
    player_character = False

    def __init__(self, STR=1, DEX=1, CON=1, INT=1, WIS=1, CHA=1,
                 MAX_HP=1, MAX_SP=0, x=1, y=1, char='@',
                 colour=(0, 0, 0), block_move=False):
        super().__init__(x, y, char, colour, block_move)

        self.MAX_HP = MAX_HP
        self.HP = MAX_HP
        self.MAX_SP = MAX_SP
        self.SP = MAX_SP
        self.consious = True
        self.stunned = False

        self.STR = STR
        self.DEX = DEX
        self.CON = CON
        self.INT = INT
        self.WIS = WIS
        self.CHA = CHA

        self.equipment = {
            'head': None, 'chest': None,
            'main': None, 'offhand': None,
            'legs': None, 'cloak': None,
            'belt': None, 'necklace': None,
            'ring1': None, 'ring2': None
        }
        self.pack = []

    def modifier(self, stat):
        '''Compute the modifier for a stat'''
        # TODO: check for item and status effects
        return (getattr(self, stat) - 10) // 2

    @property
    def passive_perception(self):
        base = 10 + self.modifier('WIS')
        # TODO: handle item effects
        return base

    @property
    def AC(self):
        AC = 0
        dex_mod = self.modifier('DEX')

        for item in self.equipment.values():
            if hasattr(item, 'AC_base'):
                AC += item.AC_base
                item_dex_mod = item.dex_mod(self)
                dex_mod = min(dex_mod, item_dex_mod)

        if AC == 0:
            return 10 + dex_mod
        else:
            return AC + dex_mod

    def skill_check(self, stat, DC, modifier=0,
                    advantage=False, disadvantage=False):
        '''
        Make a skill check against a base stat. Additional modifiers are
        applied by the caller.
        '''
        if advantage and disadvantage:
            # having both cancels out
            advantage = disadvantage = False

        result = roll()

        if result == 1:
            return SkillCheckResult(success=False, crit=True)
        if result == 20:
            return SkillCheckResult(success=True, crit=True)

        if advantage:
            result = max(result, roll())
        elif disadvantage:
            result = min(result, roll())

        result = result + self.modifier(stat) + modifier

        if result >= DC:
            return SkillCheckResult(success=True, crit=False)
        else:
            return SkillCheckResult(success=False, crit=False)

    def move_or_melee(self, dx, dy, screen):
        '''Move to a new cell or attack the creature in it'''
        new_x = self.x + dx
        new_y = self.y + dy

        for obj in screen.objects:
            if obj.alive and obj.x == new_x and obj.y == new_y:
                attack_messages = self.basic_attack(obj)
                return attack_messages
        else:
            self.move(dx, dy, screen)
            return []

    def basic_attack(self, target):
        '''
        Make a basic attack against a target. Modifiers and base damage
        must be set in subclasses.
        '''
        messages = []
        weapon = self.equipment.get('main')
        mod = weapon.atk_mod if weapon is not None else 5

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
            target_messages = target.lose_hp(damage)
            if not target.alive and self.player_character:
                self.xp += target.XP_yield
                if self.xp >= self.next_level:
                    self.level_up()

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
        self.HP -= damage
        if self.HP <= 0:
            self.die()

            msg = Message('{} died'.format(self.name), BRIGHT_RED)
            return [msg]
        else:
            if self.player_character:
                if self.HP / self.MAX_HP > 0.75:
                    self.colour = LIGHT0
                elif self.HP / self.MAX_HP > 0.50:
                    self.colour = BRIGHT_YELLOW
                elif self.HP / self.MAX_HP > 0.35:
                    self.colour = BRIGHT_ORANGE
                elif self.HP / self.MAX_HP > 0.20:
                    self.colour = BRIGHT_RED
        return []

    def die(self):
        '''Deal with creature death'''
        self.char = '%'
        self.colour = FADED_RED
        self.block_move = False
        self.alive = False

    def level_up(self):
        '''Deal with level up'''
        # Reset XP bar and bump level counter
        self.xp -= self.next_level
        self.next_level *= LEVEL_UP_XP_MULTIPLIER
        self.level += 1

        # Increase HP
        hp_up = roll(self.PC_class.hit_dice) + self.modifier('CON')
        self.MAX_HP += hp_up
        self.HP += hp_up

        # Increase SP for casters
        spell_stat = self.PC_class.spell_stat
        if spell_stat is not None:
            sp_up = roll(self.PC_class.spell_dice) + self.modifier(spell_stat)
            self.MAX_SP += sp_up
            self.SP += sp_up

        # every third level increases a random stat by 1
        if self.level % 3 == 0:
            stat = choice(
                [self.STR, self.DEX, self.CON, self.INT, self.WIS, self.CHA])
            stat += 1

        # TODO : class based perks / abilities
        #        spell slot increase etc

    def use_item(self, item):
        '''Use an item'''
        return [Message('You need to implement using items!', BRIGHT_PURPLE)]
