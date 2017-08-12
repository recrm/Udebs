import udebs

if __name__ == "__main__":
    game = udebs.battleStart("xml/pushluck.xml")
    
    while game.controlTime():
        pass
        
    game.controlInit("init")
