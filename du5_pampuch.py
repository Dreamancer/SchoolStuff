# -*- coding: utf-8 -*-
import random, sys
from functools import partial

#Zakladna trieda hernej entity
class GameEntity(object):
    #symbol predstavuje unicode znak, ktory sa zobrazi na hernej ploche
    def __init__(self, x, y, symbol):
        self.symbol = symbol
        self.x = x
        self.y = y
        
    def __str__(self):
        return self.symbol

#Trieda, ktoru budeme dedit ak chceme pohyblivu hernu entitu, dedi GameEntity
class Movable(GameEntity):

    #metoda pre pohyb hernej entity
    def move(self, x, y, worldMatrix):
        worldMatrix[self.x][self.y].content = None #nastav obsah terajsieho herneho pola na nic
        self.x = x
        self.y = y
        worldMatrix[x][y].content = self #nastav obsah pola kam sa hybeme na tento objekt

    #pre pohiblivu hernu entity vrati ci sa moze pohnut na x,y pole vo worldMatrix (ak tam nie je stena, alebo Tile z duchom)
    def canMove(self, x, y, worldMatrix):        
        if isinstance(worldMatrix[x][y], Wall) or (isinstance(worldMatrix[x][y], Tile) and isinstance(worldMatrix[x][y].content, Ghost)):
            return False
        return True

#Trieda jedneho herneho pola, dedi GameEntity
class Tile(GameEntity):
    def __init__(self, x, y):
      GameEntity.__init__(self, x, y, "░")
      self.content = None
      
    def __str__(self):
        if self.content != None:
            return self.content.symbol
        else:
            return self.symbol
        
#Trieda steny, dedi GameEntity     
class Wall(GameEntity):
    def __init__(self, x, y):
        GameEntity.__init__(self, x, y, "█")
        
#Trieda hraca, dedi Movable (a implicitne GameEntity)
class Player(Movable):
    def __init__(self, x, y):
        GameEntity.__init__(self, x, y, "☺")
        self.candies = 0
        self.history = []
        self.alive = True

    #Okrem zakladnej implementacie canMove() z Movable pre hraca navyse skontrolujme ci by nevysiel z hracej plochy
    def canMove(self, x, y, worldMatrix):
        if x<0 or x>len(worldMatrix)-1 or y<0 or y>len(worldMatrix[0])-1:
            return False
        else:
            return Movable.canMove(self,x,y,worldMatrix)

    #nacita prikaz na pohyb zo vstupu a ak moze, tak sa pohne, inak hrac straca toto kolo pohyb
    def commandMove(self, worldMatrix):
        command = input("Zadaj ťah: ").upper()
        if self.validCommand(command): #skontroluj vstup
            options = {
                'W': (self.x, self.y-1),
                'S': (self.x, self.y+1),
                'A': (self.x-1, self.y),
                'D': (self.x+1, self.y)}
            moveTup = options[command] #nacitaj suradnice pohybu podla prikazu
            if self.canMove(moveTup[0],moveTup[1],worldMatrix): #skontroluj ci sa mozeme pohnut na zvolene pole
                if isinstance(worldMatrix[moveTup[0]][moveTup[1]].content, Candy): #ak sa hybeme na pole s cukrikom, zvys counter o 1
                    self.candies += 1
                self.history.append(moveTup)#pridaj terajsie pole do historie pohybov
                self.move(moveTup[0], moveTup[1],worldMatrix)  #pohni sa na zvolene pole

    #True ak command je string a jednym z povolenych ovladacich prikazov
    def validCommand(self, command):
        if command in set(['W','S','A','D']):
            return True
        else:
            return False
#Trieda ducha, dedi Movable (a implicitne GameEntity)
class Ghost(Movable):
    def __init__(self, x, y):
        GameEntity.__init__(self, x, y, "⚉")

    #okrem zakldnej implementacie canMove() musime naviac skontrolovat ci na danom poli nie je cukrik aby nam ho duch nezakryl.
    #zistovat ci dany pohyb pre ducha je v hracej ploche nema zmysel, lebo sa vzdy hybe smerom k hracovi, ktory je vzdy v hracom poli.
    def canMove(self, x, y, worldMatrix):
        if isinstance(worldMatrix[x][y], Tile) and isinstance(worldMatrix[x][y].content, Candy):
            return False
        else:
            return Movable.canMove(self, x, y, worldMatrix)

    #Pokusi sa pohnut smerom k hracovi podla tej vzdialenosti (x/y), ktora je dlhsia. Ak sa tym smerom nemoze pohnut, tak stoji.
    def aiMove(self, player, worldMatrix):
        newX = self.x
        newY = self.y
        xDist = player.x - self.x
        yDist = player.y - self.y
        if abs(xDist) > abs(yDist):
            if xDist < 0:
                newX = self.x- 1
            else:
                newX = self.x + 1
        else:
            if yDist < 0:
                newY = self.y - 1
            else:
                newY = self.y + 1
        if self.canMove(newX, newY, worldMatrix):
            return self.move(newX,newY,worldMatrix)  
        return False
                    
    def move(self, x, y, worldMatrix):
        if isinstance(worldMatrix[x][y].content, Player):
                        worldMatrix[x][y].content.symbol = '✝'#ak je na poli kam sa hybeme hrac, zmen jeho symbol na mrtvolu a stoj
                        return True
        else:
            Movable.move(self, x, y, worldMatrix)
            return False
        
#Trieda pre candy, dedi GameEntity        
class Candy(GameEntity):
    def __init__(self, x, y):
        GameEntity.__init__(self, x, y, "☕")

#Trieda pre herny svet, obsahuje vysku, sirku hracej plochy, pole duchov, hraca a samotnu hernu plochu
class World(object):
    def __init__(self, height, width, wallChance, ghostCount):       
        self.height = height
        self.width = width
        self.generateMatrix(height, width, wallChance)
        self.ghosts = self.generateGhosts(ghostCount)
        self.generateCandy()
        self.player = self.generatePlayer()
        self.gameOver = False

    #vytvori hernu plochu podla vysky, sirky a sance pre vytvorenie steny
    def generateMatrix(self, height, width, wallChance):
        self.worldMatrix = []
        for i in range(0,width):
            self.worldMatrix.append([])
            for j in range(0,height):
                wallRoll = random.randint(1,100)
                if wallRoll <= wallChance:
                    self.worldMatrix[i].append(Wall(i,j))
                else:
                    self.worldMatrix[i].append(Tile(i,j))

    #na hracej ploche vygeneruje duchov v pocte definovanom v ghostCount nahodne niekde v rohoch
    def generateGhosts(self, ghostCount):
        ghosts = []
        for i in range(0,ghostCount):
            kvadrant = random.randint(1,4)
            wRange = self.width//5 #plocha kde sa v rohoch generuju duchovia je 1/5 z rozmerov hernej plochy
            hRange = self.height//5
            options = {
                1: (random.randint(0,wRange),random.randint(0,hRange)),
                2: (random.randint(self.width-1-wRange, self.width-1),random.randint(0,hRange)),
                3: (random.randint(0,wRange),random.randint(self.height-1-hRange, self.height-1)),
                4: (random.randint(self.width-1-wRange, self.width-1),random.randint(self.height-1-hRange, self.height-1))}
            coordinates = options[kvadrant] #podla toho ktory kvadrant sa vygeneroval, nacitaj nahodne suradnice z toho kvadrantu
            ghost = self.placeGhost(coordinates[0], coordinates[1])
            ghosts.append(ghost)
        return ghosts

    #vlozi jedneho ducha na suradnicu x,y alebo ak tam nie je miesto, niekde v okoli a vrati pridaneho ducha
    def placeGhost(self, x, y):
        if isinstance(self.worldMatrix[x][y], Tile) and self.worldMatrix[x][y].content == None:
            ghost = Ghost(x,y)
            self.worldMatrix[x][y].content = ghost
            return ghost
        else:
            if x < self.width//2:
                newX = x + random.randint(0,1)
            else:
                newX = x - random.randint(0,1)
            if y < self.height//2:
                newY = y + random.randint(0,1)
            else:
                newY = y - random.randint(0,1)
            return self.placeGhost(newX, newY)

    #na nahodnom mieste v hracej ploche vygeneruje cand. Kym nenajde vhodne miesto, tak skusa nahodne suradnice
    def generateCandy(self):
        while True:
            x = random.randrange(0,self.width)
            y = random.randrange(0,self.height)
            if isinstance(self.worldMatrix[x][y], Tile) and self.worldMatrix[x][y].content == None:
                candy = Candy(x,y)
                self.worldMatrix[x][y].content = candy

                break
    #kym nenajde vhodne miesto skusa nahodne suradnice niekde v okoli stredu hracej plochy (okolie je 1/5 z rozmerov hracej plochy)        
    def generatePlayer(self):
        while True:
            x = random.randrange(self.width//2 - self.width//5, self.width//2 + self.width//5)
            y = random.randrange(self.height//2 - self.height//5, self.height//2 + self.height//5)
            if self.canPlacePlayer(x,y):
                player = Player(x, y)
                self.worldMatrix[x][y].content = player
                return player
            
    #funkcia vrati false ak na suradniciach x,y alebo v ich okoli(nie len susedne ale aj "rohove" polia) je duch, alebo candy, tj ak nie je prazdne
    #v zadani sice nebolo nic o prvotnej vzdialenosti medzi hracom a candy, ale povedzme ze ak by sa hrac vygeneroval hned pri candy bolo by to moc lahke (a takto je to lahsie nakodit :)
    def canPlacePlayer(self, x, y): 
        for i in range(max(0,x-1),min(self.width-1,x+1)):
            for j in range(max(0,y-1),min(self.height-1,y+1)):
                if (isinstance(self.worldMatrix[i][j], Tile) and self.worldMatrix[i][j].content != None) or isinstance(self.worldMatrix[i][j], Wall):
                    return False
        return True

    #False ak sa na hracej ploche nachadza nejaky cukrik
    def noCandy(self):
        for i in range(0,self.width):
            for j in range(0,self.height):
                if isinstance(self.worldMatrix[i][j], Tile) and isinstance(self.worldMatrix[i][j].content, Candy):
                    return False
        return True

    #metoda na zahratie jedneho herneho kola
    def playRound(self):
        self.player.commandMove(self.worldMatrix)
        if self.noCandy(): #ak hrac zjedol v tomto tahu candy, vygeneruj novy
            self.generateCandy()
        for ghost in self.ghosts:
            if ghost.aiMove(self.player, self.worldMatrix): #bud sa pohne a vrati false, alebo, ak na mieste kam by sa pohol stoji hrac, vrati true a stoji
                self.gameOver = True #ak sa duch pohol na miesto kde stoji hrac je koniec hry
    #do hernej plochy zaznaci historiu hracovych pohybov  
    def markPlayerPath(self):
        for coord in self.player.history:
            self.worldMatrix[coord[0]][coord[1]].symbol = '▒'
    
    def __str__(self):
        res = ""
        for i in range(0,self.height):
            for j in range(0, self.width):
                res += str(self.worldMatrix[j][i])
                if j == self.width - 1:
                    res += '\n'
        res += "Candies: " + str(self.player.candies)
        return res

#Trieda samotnej hry
class Game(object):

    #nastavi defaultne nastavenia pre hernu plochu a nastavi "switche" pre prikazy v menu
    def __init__(self):
        self.settings = {
            'width': 20,
            'height': 20,
            'wallChance': 10,
            'ghostCount': 4}
        
        self.cmds = {
            'menu': {
                '1': self.playGame,
                '2': self.settingsMenu,
                '3': sys.exit
                },
            'settings': {
                '1': partial(self.setSetting, 'width'),
                '2': partial(self.setSetting, 'height'),
                '3': partial(self.setSetting, 'wallChance'),
                '4': partial(self.setSetting, 'ghostCount'),
                '5': self.mainMenu
                }
            }
        

    #zobrazi hlavne menu, precita prikaz zo vstupu a ak je paltny, tak ho vykokna. Inak znovu zobrazi hlavne menu 
    def mainMenu(self):
        cmdSet = set(['1','2','3'])
        print("==PAMPUCH - by Jakub Horniak 395904, FI MUNI, 2016==", end='\n')
        print("--Hlavné Menu--",end='\n')
        print("1 - Nová Hra",end='\n')
        print("2 - Možnosti",end='\n')
        print("3 - Koniec", end='\n')
        cmd = input()
        if cmd in cmdSet:
            self.executeCommand('menu', cmd)
        else:
            self.mainMenu()

    #vykonaj prikaz v nejakom menu. cmdType moze byt 'menu' alebo 'settings' , cmd je cislo prikazu v menu, value pre prikazy zadavajuce hodnotu v nastaveniach hry
    def executeCommand(self, cmdType, cmd, value = None):
        if value != None:
            self.cmds[cmdType][cmd](value)
        else:
            self.cmds[cmdType][cmd]()

    #podla parametra setting nastavi prislusne nastavenie hernej plochy na hodnotu vo value
    def setSetting(self, setting, value):
        if (value.isdigit() and int(value) > 0) and ((setting == "ghostCount" and int(value) <= 10) or (setting != "ghostCount" and int(value) <= 100)):
            self.settings[setting] = int(value)
        else:
            print("Neplatná hodnota!", end='\n')
            self.settingsMenu()
    #zobrazi menu nastaveni, precita nastavenie zo vstupu a pokusi sa toto nastavenie zmenit. Ak je neplatny prikaz informuje o tom hraca a znovu zobrazi toto menu
    def settingsMenu(self):
        cmdSet = set(['1','2','3','4','5'])
        print("--Možnosti--", end='\n')
        print("1 - Šírka hracej plochy (1-100): " + str(self.settings['width']),end='\n')
        print("2 - Výška hracej plochy (1-100): " + str(self.settings['height']),end='\n')
        print("3 - Šanca na vygenerovanie steny v %: " + str(self.settings['wallChance']),end='\n')
        print("4 - Počet duchov (0-10): " + str(self.settings['ghostCount']),end='\n--\n')
        print("5 - Naspäť",end='\n--\n')
        print("Zadaj číslo možnosti a novú hodnotu oddelené medzerou, alebo 5 pre hlavné menu",end='\n')
        cmd = input().split(" ")
        if cmd[0] in cmdSet:
            if len(cmd) == 2 and cmd[0] != '5': 
                self.executeCommand('settings', cmd[0], cmd[1])
                self.settingsMenu()
            elif cmd[0] =='5':
                self.executeCommand('settings', cmd[0])
            else:
                print("Nezadaná hodnota!", end='\n')
            self.settingsMenu()
        else:
            print("Neplatná možnosť!", end='\n')
            self.settingsMenu()
              
    #metoda na zahratie hry. Vytvori instanciu herneho sveta podla nastaveni a kym nie je koniec hry v loope vykresli herny svet a zahra kolo
    def playGame(self):
        self.world = World(self.settings['width'],
                           self.settings['height'],
                           self.settings['wallChance'],
                           self.settings['ghostCount'])
        while not self.world.gameOver:
            print(self.world)
            self.world.playRound()
        self.gameOver()

    #vyznaci historiu hracovych pohybov, vykresli svet a vypise "GAME OVER". Potom zobrazi hlavne menu
    def gameOver(self):
        self.world.markPlayerPath()
        print(self.world)
        print("GAME OVER", end="\n\n")
        self.mainMenu()

game = Game()
game.mainMenu()