'''
Base classes and functions for creatures, NPCs and enemies
'''
from ..utils import roll, SkillCheckResult, GameObject


class Creature(GameObject):
    '''Base class for a creature. Must be subclasses to be used'''
    XP_yield = None
    size = None
    race = None
    type = None

    def __init__(self, STR=1, DEX=1, CON=1, INT=1, WIS=1, CHA=1,
                 AC=1, MAX_HP=1, x=1, y=1, char='@', colour=(0, 0, 0),
                 block_move=False):
        super().__init__(x, y, char, colour, block_move)

        self.MAX_HP = MAX_HP
        self.HP = MAX_HP
        self.AC = AC
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
            'left': None, 'right': None,
            'legs': None, 'cloak': None
        }
        self.pack = []

    @property
    def STR_MOD(self):
        return (self.STR - 10) // 2

    @property
    def DEX_MOD(self):
        return (self.DEX - 10) // 2

    @property
    def CON_MOD(self):
        return (self.CON - 10) // 2

    @property
    def INT_MOD(self):
        return (self.INT - 10) // 2

    @property
    def WIS_MOD(self):
        return (self.WIS - 10) // 2

    @property
    def CHA_MOD(self):
        return (self.CHA - 10) // 2

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

        result = result + getattr(self, stat + '_MOD') + modifier

        if result >= DC:
            return SkillCheckResult(success=True, crit=False)
        else:
            return SkillCheckResult(success=False, crit=False)

    def move_or_melee(self, dx, dy, screen):
        new_x = self.x + dx
        new_y = self.y + dy
        for obj in screen.objects:
            if obj is not self and obj.x == new_x and obj.y == new_y:
                self.basic_attack(obj)
                break
        else:
            self.move(dx, dy, screen)

    def basic_attack(self, target):
        '''
        Make a basic attack against a target. Modifiers and base damage
        must be set in subclasses.
        '''
        weapon = self.equipment.get('right')
        mod = weapon.atk_mod if weapon is not None else 0
        success, crit = self.skill_check('STR', target.AC, mod)
        if success:
            if crit:
                if not weapon:
                    damage = 5
                else:
                    damage = weapon.crit(self)
            else:
                if not weapon:
                    damage = 1
                else:
                    damage = weapon.damage(self)
            target.lose_hp(damage)

    def lose_hp(self, damage):
        '''Take a hit and check for death'''
        self.HP -= damage
        if self.HP <= 0:
            self.CONSIOUS = False
        if self.HP <= -(self.MAX_HP // 2):
            self.die()

    def die(self):
        '''Deal with creature death'''
        raise NotImplementedError
