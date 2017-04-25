'''
Generation of Party Characters
'''
import yaml
from random import randint, choice
from .config import LIGHT0
from .utils import stat_roll, roll
from .creatures import Creature


def random_ability_scores():
    '''Generate a randomised set of ability scores'''
    return [stat_roll() for _ in range(6)]


def new_PC(name, PC_race='Human', PC_class='Adventurer'):
    '''
    Build a new player character from config files
    '''
    # Load and parse the config files
    races = yaml.load(open('guildmaster/gamedata/races.yaml', 'r'))
    classes = yaml.load(open('guildmaster/gamedata/classes.yaml', 'r'))

    # Pull out the race and class
    PC_race = races[PC_race]
    PC_class = classes[PC_class]

    # Generate ability scores
    ranked_scores = sorted(random_ability_scores(), reverse=True)
    ability_scores = dict(zip(PC_class['statOrder'], ranked_scores))
    ability_scores['MAX_HP'] = sum(PC_class['hitDice']) + ability_scores['VIT']
    ability_scores['MAX_FOCUS'] = (roll(PC_class['focusDice']) +
                                   ability_scores['INT'])

    # Apply racial stat modifiers
    for stat, mod in zip(['STR', 'DEX', 'INT', 'VIT'],
                         PC_race['statBonus']):
        ability_scores[stat] += mod

    PC = Creature(x=0, y=0, char='@', colour=LIGHT0,
                  block_move=False, **ability_scores)

    # Copy over Race details
    PC.speed = PC_race['speed']
    PC.size = PC_race['size']
    PC.vision = tuple(PC_race['vision'])
    PC.type = PC_race['type']
    PC.xp_mod = PC_race['xpMod']
    PC.abilites = PC_race['abilities']
    PC.trained = PC_race['trained']
    PC.agro_base = PC_race['agroBase']

    # Copy over Class details
    PC.hit_dice = PC_class['hitDice']
    PC.focus_dice = PC_class['focusDice']
    PC.trained += PC_class['trained']
    PC.abilites += PC_class['abilities']
    PC.agro_base += PC_class['agroModifier']

    # Fetch starting equipment and gold
    # weapon = choice(PC_class['equipment']['weapons'])
    # PC.equipment['main'] = Weapon(weapons[weapon])

    # armour = choice(PC_class['equipment']['armour'])
    # PC.equipment['chest'] = Armour(armour[armour])

    # pack = PC_race['equipment'] + PC_class['equipment']['items']
    # PC.pack = [Item(i) for i in pack]

    gold_min, gold_max = PC_class['equipment']['gold']
    PC.gold = randint(gold_min, gold_max)

    # Final player properties
    PC.level = 1
    PC.current_xp = 0
    PC.next_level = 50
    PC.player_character = True

    return PC
