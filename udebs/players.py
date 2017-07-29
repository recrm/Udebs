from udebs.interpret import importModule
import random

def createPlayer(function, name, entity, stat=None):
    def wrapper(instance):
        if not isinstance(entity, list):
            choices = instance.getStat(entity, stat)
        else:
            choices = entity
         
        value = function(choices, instance.movestore)
        
        if name not in instance.movestore:
            instance.movestage[name] = [] 
            
        instance.movestage[name].append(value)
        return value

    importModule({name: {
        "f": "f_" + name,
        "args": ["self"],
    }}, {"f_" + name: wrapper})
    
    
def distributionPlayer(name, population, weights, seed=None):
    rand = random.Random(seed)
    
    def player(choices, movestore):
        # This does not work in python 3.5
        rand.choices(population)
        
    createPlayer(player, name, population)
    
def randomPlayer(*args, seed=None, **kwargs):
    rand = random.Random(seed)
    
    def player(choices, movestore):
        return rand.choice(choices)
        
    createPlayer(player, *args, **kwargs)
    
def humanPlayer(*args, **kwargs):
    def player(choices, movestore):
        choice = input("What will you play? ")
        while choice not in choices:
            choice = input("That is not a valid action. Try again. ")
            
        return choice
        
    createPlayer(player, *args, **kwargs)
    
def copyPlayer(name, *args, default=None, **kwargs):
    assert default is not None
    
    def player(choices, movestore):
        for key, value in movestore.items():
            if key != name:
                return value[-1]
                
        return default
        
    createPlayer(player, name, *args, **kwargs)
    
def constantPlayer(*args, constant=None, **kwargs):
    assert constant is not None
    
    def player(*wrapper):
        return constant
        
    createPlayer(player, *args, **kwargs)
    
def grudgerPlayer(name, *args, default=None, trigger=None, **kwargs):
    assert default is not None
    assert trigger is not None
    
    def player(choices, movestore):
        for key, value in movestore.items():
            if key != name:
                if trigger in value:
                    return trigger
                    
        return default
        
    createPlayer(player, name, *args, **kwargs)
