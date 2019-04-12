#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 13 09:25:55 2018
how to use:



@author: hyamanieu
"""

import pygame
import pygame.locals as pgl
from pygame.math import Vector2
import math
import os
import random
import itertools
import sys
import time

murapix_path = os.path.join(os.path.dirname(__file__),'..','..')
sys.path.append(murapix_path)
from murapix.murapix import Murapix, get_panel_adresses,get_deadzone_addresses


#%%Initialize global constants
FPS = 60
MAXSPEED = 60/FPS
MAXSPEED_SQUARED = MAXSPEED**2
MISSILE_SPEED = 5*60/FPS
RIGHT, UP, LEFT, DOWN = range(4)
direction = {pygame.K_UP: UP, pygame.K_DOWN: DOWN,
             pygame.K_LEFT: LEFT, pygame.K_RIGHT: RIGHT}
missile_direction = {None: (0, 0), UP: (0, -MISSILE_SPEED), DOWN: (0, MISSILE_SPEED),
                     LEFT: (-MISSILE_SPEED, 0), RIGHT: (MISSILE_SPEED, 0)}

#Scene constants
INGAME = True #first screen is Ingame



#%% create in game objects
class AllActiveSprites(pygame.sprite.Sprite):
    allactivesprites = pygame.sprite.RenderUpdates()
    fps = None

class Counter(AllActiveSprites):
    def __init__(self, admiral):
        super().__init__()
#        surface = pygame.Surface((8,8), depth=24)
#        key = (0,0,0)#pure white for transparency
#        surface.fill(key)
#        surface.set_colorkey(key)
        self.color = admiral.color
        self.admiral = admiral
        self.respawnTime = self.fps*3
        font = pygame.font.Font(None, 8)
        text = font.render(
                    str((self.respawnTime // self.fps) + 1), False, self.color)
        
        
        
        self.image = text
        self.rect = text.get_rect()
        self.rect.center = admiral.rect.center

    def update(self):
        self.respawnTime -= 1
        font = pygame.font.Font(None, 8)
        text = font.render(
                    str((self.respawnTime // self.fps) + 1), False, self.color)
        self.image = text
        if self.respawnTime < 1:
            self.admiral.replace()
            self.kill()

class Explosion(pygame.sprite.Sprite):
    scratch = None
    def __init__(self, sprite):
        super().__init__()
        self.image = None
        self.radius = 1
        self.radiusIncrement = 1
        self.rect = sprite.rect

    def update(self):
        self.radius += self.radiusIncrement
        pygame.draw.circle(
            self.scratch,
            pygame.Color(215,124,0),
            self.rect.center, self.radius, 1)
        if self.radius > 4:
            self.kill()
        

class Missile(AllActiveSprites):

    def __init__(self, admiral, *args, **kws):
        super(Missile,self).__init__(*args, **kws)
        self.image = pygame.Surface((2,2))
        self.rect = self.image.fill(admiral.color)
        self.direction = None
        self.velocity = None
        self.admiral = admiral
        

    def table(self):
        admiral = self.admiral
        self.add(admiral.missile_pool)
        self.remove(admiral.active_missile, self.allactivesprites)
        return Explosion(self)

    def update(self):
        velocity = self.velocity
        newpos = self.rect.move(velocity[0], velocity[1])
        self.rect = newpos

class Admiral(AllActiveSprites):
    pool = pygame.sprite.Group()
    active = pygame.sprite.Group()
    init_pos = None #must be set directly on class before instancing
    
    
    
    
    def __init__(self, playernumber, *args, NoM=8, **kws):
        """
        playernumber: the id of the player/admiral
        NoM: number of missiles per player
        """
        if self.init_pos is None:
            msg = """Admiral.init_pos must be set before instancing
            It must be a dictionnary with keys being range(NoP), 
            where NoP is the maximum number of players, and the values
            are starting position for each admiral ship."""
            raise AttributeError(msg)
        
        super(Admiral, self).__init__(*args, **kws)
        image_path = os.path.join('images','P'+str(playernumber+1)+'.png')
        self.base_image = pygame.transform.rotate(
                             pygame.image.load(image_path),
                             90)
        self.color = self.base_image.get_at((0,0))
        self.direction = RIGHT
        self.cannon_dir = RIGHT      
        self.invincible = int(2*self.fps)#2 seconds
        
        #variables to control speed
        self.current_speed = Vector2(0,0)
        self.linger = 1/self.fps #lose one "speed" per second if no accel
        self.slowmo_x = 0.#manage decimal speed in x direction
        self.slowmo_y = 0.#manage decimal speed in y direction
        
        
        self.image = self.draw_image()
        self.rect = self.image.get_rect()
        self.rect.center = self.init_pos[playernumber]
        self.playernumber = playernumber
        self.missile_pool = pygame.sprite.Group([Missile(self) for _ in range(NoM)])
        self.active_missile = pygame.sprite.Group()
        self.score = 0
            
    def table(self):
        self.kill()
        self.rect.center = self.init_pos[self.playernumber]
        self.add(self.pool)
        return Counter(self)
        
    def replace(self):
        self.invincible = int(2*self.fps)#2 seconds
        self.add(self.active, self.allactivesprites)
        self.remove(self.pool)
        self.image = self.draw_image()
        pygame.image.save(self.image,'temp.png')
    
    
    def draw_image(self):
        """
        returns a surface object with both cannon and ship drawn in the right
        direction
        """
        dir_ship = self.direction
        dir_cannon=self.cannon_dir
        temp_image = self.base_image.copy()
        pygame.draw.polygon(temp_image, (0,0,0), [(2,2),(2,3),(3,3),(3,2)])
        if dir_cannon == dir_ship:
            pygame.draw.polygon(temp_image, (60,60,60), [(4,3),(4,2), (5,3),(5,2)])
        if (dir_ship - dir_cannon)%4 ==1:#-90° angle
            pygame.draw.polygon(temp_image, (60,60,60), [(2,4),(3,4), (2,5),(3,5)])
        if (dir_ship - dir_cannon)%4 ==3:#+90° angle
            pygame.draw.polygon(temp_image, (60,60,60), [(2,1),(3,1), (2,0),(3,0)])
        if (dir_ship - dir_cannon)%4 ==2:#180° angle
            pygame.draw.polygon(temp_image, (60,60,60), [(1,2),(1,3), (0,2),(0,3)])
        temp_image=pygame.transform.rotate(temp_image,dir_ship*90)
        return temp_image
    

    def update(self):
        if self.invincible>1:
            self.invincible -= 1            
            alpha = int(255*(math.cos(16*math.pi*self.invincible/self.fps)+1)/2)
            image = self.draw_image()
            surface = pygame.Surface(image.get_size(), depth=24)
            key = (0,0,0)#pure white for transparency
            surface.fill(key)
            surface.set_colorkey(key)
            surface.blit(image, (0,0))
            surface.set_alpha(alpha) 
            self.image = surface 
        elif self.invincible == 1:
            self.invincible -= 1
            self.image = self.draw_image()
        
    def shoot_cannon(self,dir_cannon):
        if dir_cannon != self.cannon_dir:
            self.cannon_dir = dir_cannon
            self.image = self.draw_image()
        loc = self.rect.center
        if len(self.missile_pool) > 0:
            missile = self.missile_pool.sprites()[0]
            missile.add(self.active_missile, self.allactivesprites)
            missile.remove(self.missile_pool)
            missile.velocity = velocity = missile_direction[self.cannon_dir]
            missile.rect.center = [loc[0] + velocity[0],loc[1] + velocity[1]]
        
    def move(self, dx, dy):
        acceleration = Vector2((dx,dy))/10
        speed = self.current_speed+acceleration
        if speed.length_squared() > MAXSPEED_SQUARED:
            speed.scale_to_length(MAXSPEED)  
        if not acceleration.length_squared()>0:
            try:
                speed.scale_to_length(max(0,speed.length()-self.linger))
            except ValueError:
                pass#speed already 0
            
        if abs(speed.x) > abs(speed.y):
            direction = LEFT if speed.x < 0 else RIGHT
        else:
            direction = UP if speed.y < 0 else DOWN
        old_direction = self.direction  
        if direction != old_direction and speed.length_squared()>0:
            self.direction = direction
            self.image = self.draw_image()
        
        
        self.current_speed = Vector2(speed)#real speed save
        #now deal with decimals
        self.slowmo_x += speed.x-round(speed.x)
        self.slowmo_y += speed.y-round(speed.y)
        speed.x = round(speed.x)
        speed.y = round(speed.y)
        if abs(self.slowmo_x) > 1:
            speed.x += self.slowmo_x
            self.slowmo_x = 0.
        if abs(self.slowmo_y) > 1:
            speed.y += self.slowmo_y
            self.slowmo_y = 0.
        
        self.rect = self.rect.move(speed.x, speed.y)
#        print(f"\rdecimals: {self.slowmo_x:+0.3f},{self.slowmo_y:+0.3f} ; pos: {self.rect.center} ; curr_speed={self.current_speed} ; speed = {speed}          ",end="")
            
        
class Obstacles(AllActiveSprites):
    def __init__(self, pos, *args, **kws):
        super(Obstacles,self).__init__(*args, **kws)
        self.pos = pos
        self.initial_pos = Vector2(pos)
        self.t = 0
        
    def update(self):
        velocity = Vector2(random.choice([1,-1]+100*[0]), 
                                  random.choice([1,-1]+100*[0]))
        newpos = Vector2(self.rect.center)+velocity
        if newpos.distance_to(self.initial_pos) > 10 :
            velocity = (self.initial_pos - newpos)
            velocity.scale_to_length(math.sqrt(2))
            newpos = Vector2(self.rect.center)+velocity
        self.rect.center = [int(n) for n in newpos]

   

class ScoreBoard(Obstacles):
    def __init__(self, admiral, *args, **kws):
        super(ScoreBoard,self).__init__(*args, **kws)
        self.admiral = admiral
        image = pygame.Surface((17,17))
        self.image = image
        self.rect = image.get_rect()
        self.rect.center = self.pos
        
    def update(self):
        image = self.image
        color_key = (128,16,0)
        image.fill(color_key)
        image.set_colorkey(color_key)
        until_victory = 8-self.admiral.score
        
        if until_victory <1:
            self.weve_got_a_winner()
            
        pygame.draw.circle(image,
                           self.admiral.color,
                           (9,9),
                           8,
                           0)
        pygame.draw.circle(image,
                           (20,20,20),
                           (9,9),
                           until_victory,
                           0)
        
        
        super(ScoreBoard,self).update()
        
    def weve_got_a_winner(self):
            global INGAME
            global WINNER
            INGAME= False
            WINNER = self.admiral
        
    
        
    
class Floaters(Obstacles):
    def __init__(self, *args, big=False,  **kws):
        super(Floaters,self).__init__(*args, **kws)
        if big:
            im_file = "boat"
        else:
            im_file = "buoy"
        self.im_file = im_file
        self.image = pygame.image.load(os.path.join('images',im_file+"1.png"))
        self.rect = self.image.get_rect()
        self.rect.center = self.pos
        self.changeperiod = 4*self.fps#every X seconds
        self.next_image = self.changeperiod
        
    def update(self):
        self.next_image += -1
        if self.next_image==self.changeperiod//2:
            self.image = pygame.image.load(os.path.join('images',
                                                        self.im_file+"2.png"))
        elif self.next_image==0:
            self.image = pygame.image.load(os.path.join('images',
                                                        self.im_file+"1.png"))
            self.next_image = self.changeperiod
        
        
        super(Floaters,self).update()
            
class DeadZones(pygame.sprite.Sprite):
    def __init__(self, xy,wh, *args,  **kws):
        super(DeadZones,self).__init__(*args, **kws)
        x,y = xy
        w,h = wh
        self.image = pygame.Surface((w,h))
        self.rect = self.image.get_rect()
        self.rect.topleft = (x,y)
        pygame.draw.line(self.image,pygame.Color('red'),(0,0),(w,h))        
        pygame.draw.line(self.image,pygame.Color('red'),(0,h),(w,0))
            
#%% Manage joysticks
            
SENSITIVITY = 0.333

def handle_axis(axis_value):
    if axis_value < -SENSITIVITY:
        return -1
    elif axis_value > SENSITIVITY:
        return 1
    return 0

def handle_joystick(joystick):
    x_axis = handle_axis(joystick.get_axis(0))
    y_axis = handle_axis(joystick.get_axis(1))
    return x_axis, y_axis

#%% Make the murapix class
class Amiral_8btn(Murapix):
    
    def __init__(self):
        super(Amiral_8btn, self).__init__()
        self.gamepad = os.path.join(os.path.dirname(__file__),
                                    'gamepad1js4btn.svg')
        
    
    def setup(self):
        self.SCREENRECT = self.scratch.get_rect()
        Explosion.scratch = self.scratch
        pygame.display.set_caption('amiral_8btn')
        
        # game constants
        self.fps = FPS
        
        
        self.setup_ingame()
        self.setup_winner()
        self.setup_comm()
        
        #scene status for while loops
        self.current_scene = 0
        self.scene_select = {
                0: self.ingame_loop,
                1: self.winner_loop,
                2: self.comm_loop
                }
        
    def setup_ingame(self):
        """
        setup the in game screen
        """
        #initialization of sprites
        AllActiveSprites.fps = FPS
        self.bg_period = FPS*3#period between 2 background movement
        self.bg_t = 0
        
        
        #Prepare the joysticks
        pygame.joystick.init()
        self.joysticks = None
        if pygame.joystick.get_count() > 0:
            self.NoP = pygame.joystick.get_count()#number of players (use joystick)
            self.joysticks = [pygame.joystick.Joystick(x) 
                         for x in range(self.NoP)]            
        else:
            self.NoP = 1 #1 player (keyboard)
                
        #prepare background    
        self.background = pygame.Surface(
                (self.SCREENRECT.size[0],
                 self.SCREENRECT.size[1]+1)
                ).convert()
        self.background.fill((0, 110, 255))
        
        #make the waves
        for (x,y) in itertools.product(range(4,self.width,8),
                                        range(4,self.height,8)):
            if (x-4)%16:
                #every even number, move right
                y += 4
            pygame.draw.lines(self.background,(0, 150, 255),False,
                              [(x,y),
                               (x+1,y-1),
                               (x+2,y-1),
                               (x+3,y),])
        
        self.scratch.blit(self.background, (0, 0))
        self.sprites = pygame.sprite.RenderUpdates()
        all_pos = [(x+w//4, y+h//4) for ((x,y),(w,h)) 
                   in get_panel_adresses(self.mapping, self.led_rows)]
        Admiral.init_pos = dict(
                                zip(range(len(all_pos)),
                                all_pos
                                    ))
        Admiral.active = pygame.sprite.RenderUpdates([
                              Admiral(n,self.sprites) for n in range(self.NoP)
                                                            ])
        AllActiveSprites.allactivesprites = self.sprites
        
        #prepare obstacles, including dead zones add them in two groups
        pos_obs_list = [(x+w//2, y+h//2) for ((x,y),(w,h)) in get_panel_adresses(self.mapping, self.led_rows)]
        self.obstacles = pygame.sprite.Group()
        for admiral in Admiral.active:
            self.obstacles.add(ScoreBoard(admiral,pos_obs_list.pop(0)))
        for x,y in pos_obs_list:
            self.obstacles.add(Floaters((x,y), 
                                        big = random.choice((False,True))))
        for xy, wh in get_deadzone_addresses(self.mapping, self.led_rows):
            self.obstacles.add(DeadZones(xy,wh))
        
        self.sprites.add(self.obstacles.sprites())
        self.alldrawings = pygame.sprite.Group()
        
    def setup_winner(self):
        """
        setup the second screen once a winner is selected
        """
        self.winnertime = FPS*4  
        self.wevegotawinner = self.winnertime#how many seconds it shows the winner
        self.winner_radius = max(self.height,self.width)
        self.now = time.time()
        
    def setup_comm(self):
        """
        setup the third screen showing the ad once the game is finished.
        """
        self.dude = 0
        self.dude_2 = 0
        self.dude_3 = 0
        self.dude_4 = 0
        
        self.background2 = pygame.Surface((self.SCREENRECT.size[0],
                                           self.SCREENRECT.size[1])).convert()
        self.background2.fill((0, 0, 0))        
        
        self.font = pygame.font.Font(None, self.height//3)
        self.text = self.font.render(
                    "MURAPIX", False, (128,204,240))
        self.font2 = pygame.font.Font(None, self.height//4)
        self.text2 = self.font2.render(
                    "soon on your", False, (128,204,240))
        self.text3 = self.font2.render(
                    "favorite places'", False, (128,204,240))
        self.text4 = self.font.render(
                    "Walls", False, (128,204,240))
    
    def logic_loop(self):
        clock = self.clock
        self.scene_select[self.current_scene]()
        msg = "\r Raw time: {0}, tick time: {1}, fps: {2}".format(clock.get_rawtime(),
                                                            clock.get_time(),
                                                            clock.get_fps())
        print(msg, end="")
    def graphics_loop(self):
        pass



    def ingame_loop(self):
        self.focus = True
        for event in pygame.event.get():
            if ((event.type == pgl.QUIT) 
                or ((event.type == pgl.KEYDOWN) 
                    and (event.key == pgl.K_ESCAPE))):
                self.RUNNING = False
            if ((event.type == pygame.KEYDOWN)
                  and (event.key in direction.keys())):
                cannon_dir = direction[event.key]
                for admiral in Admiral.active:
                    admiral.shoot_cannon(cannon_dir)
                    
            if (self.joysticks and (event.type == pgl.JOYBUTTONDOWN)):
                for admiral in Admiral.active:
                    playernumber = admiral.playernumber
                    
                    joystick = self.joysticks[playernumber]
                    pressed = []
                    for i in range(joystick.get_numbuttons()):
                        if joystick.get_button(i):
                            pressed.append(i)
                        
                    cannon_dir=None
                    if joystick.get_button(0):
                        cannon_dir = UP
                    if joystick.get_button(1):
                        cannon_dir = RIGHT
                    if joystick.get_button(2):
                        cannon_dir = DOWN
                    if joystick.get_button(3):
                        cannon_dir = LEFT
                    if cannon_dir is not None:
                        admiral.shoot_cannon(cannon_dir)
                        
            if (event.type == pgl.ACTIVEEVENT):
                print(event)
                
        #interaction between admirals, their missiles and other objects
        for admiral in Admiral.active:
            playernumber = admiral.playernumber
            if self.joysticks:
                joystick = self.joysticks[playernumber]
                joystick.init()
                x_axis, y_axis = handle_joystick(joystick)
            else:
                keys = pygame.key.get_pressed()
                x_axis = keys[pgl.K_d] - keys[pgl.K_q]
                y_axis = keys[pgl.K_s] - keys[pgl.K_z]
            for obstacle in pygame.sprite.spritecollide(admiral,self.obstacles,False):
                m_pos = Vector2(obstacle.rect.center)
                a_pos = Vector2(admiral.rect.center)
                new_speed = a_pos-m_pos
                new_speed.scale_to_length(
                            max(1,admiral.current_speed.length())
                                         )
                admiral.current_speed = new_speed
                admiral.move(0, 0)
            if not self.SCREENRECT.contains(admiral.rect):
                new_speed = - admiral.current_speed
                new_speed.scale_to_length(
                            max(1,new_speed.length())
                                         )
                admiral.current_speed = new_speed
                admiral.move(0, 0)
                admiral.rect = admiral.rect.clamp(self.SCREENRECT)
                
            else:
                admiral.move(x_axis, y_axis)                
                
            for missile in admiral.active_missile:
                for ad2 in pygame.sprite.spritecollide(missile, Admiral.active,False):
                    if ad2 != admiral and not ad2.invincible:
                        explosion = missile.table()
                        explosion.add(self.alldrawings)
                        counter = ad2.table()
                        counter.add(self.sprites)
                        admiral.score +=1
                if pygame.sprite.spritecollideany(missile, self.obstacles):
                    explosion = missile.table()
                    explosion.add(self.alldrawings)
                
                if not self.SCREENRECT.contains(missile.rect):
                    missile.table()
                
        #animate background
        self.bg_t +=1
        if self.bg_t>=self.bg_period:
            self.bg_t = 0
        self.scratch.blit(self.background, (0, 2*self.bg_t//(self.bg_period)))#add 1 pixel or not in vertical axis
        self.sprites.update()
        self.sprites.draw(self.scratch)
        self.alldrawings.update()
        
        global INGAME
        if not INGAME:
            self.current_scene +=1
        
        
    def winner_loop(self):
        for event in pygame.event.get():
            if ((event.type == pgl.QUIT) 
                or ((event.type == pgl.KEYDOWN) 
                    and (event.key == pgl.K_ESCAPE))):
                self.RUNNING = False
        
        winnertime = self.winnertime
        self.wevegotawinner -= 1
        if self.wevegotawinner < (winnertime-FPS) and self.wevegotawinner > 2*FPS:
            
            
            self.winner_radius -= max(self.height,self.width)/(winnertime - 3*FPS)
            surface = pygame.Surface(self.scratch.get_size(), depth=24)
            key = (255,255,255)#pure white for transparency
            surface.fill((0,0,0))
            if self.winner_radius > 18:
                pygame.draw.circle(surface,
                                   key,
                                   WINNER.rect.center,
                                   int(self.winner_radius))
            else:                
                pygame.draw.circle(surface,
                                   key,
                                   WINNER.rect.center,
                                   18)
            surface.set_colorkey(key)
            self.scratch.blit(surface, (0,0))
        elif self.wevegotawinner < 2*FPS:
            font = pygame.font.Font(None, self.height//3)
            text = font.render(
                        "WINNER", False, (255,255,255))
            
            self.scratch.blit(text,(self.width//4, self.height//2))
        
        
        if self.wevegotawinner < 1:
            self.current_scene +=1
        
        
        
        
    
    def comm_loop(self):
        
        for event in pygame.event.get():
            if ((event.type == pgl.QUIT) 
                or ((event.type == pgl.KEYDOWN) 
                    and (event.key == pgl.K_ESCAPE))):
                self.RUNNING = False
        
        background = self.background2
        
        self.scratch.blit(background, (0,0))
        
        if self.dude < self.width-(self.width//2 - self.text.get_width()//2):
            self.dude +=2*60/FPS
        elif self.dude_2 < self.width-(self.width//2 - self.text2.get_width()//2):
            self.dude_2 += 2*60/FPS
        elif self.dude_3 < self.width-(self.width//2 - self.text3.get_width()//2):
            self.dude_3 += 2*60/FPS
        elif self.dude_4 < self.width-(self.width//2 - self.text4.get_width()//2):
            self.dude_4 += 2*60/FPS
        self.scratch.blit(self.text,
                          (self.width-int(self.dude), 
                           self.height//8))
        self.scratch.blit(self.text2,
                          (self.width-int(self.dude_2), 
                           3*self.height//8))
        self.scratch.blit(self.text3,
                          (self.width-int(self.dude_3), 
                           4.5*self.height//8))
        self.scratch.blit(self.text4,
                          (self.width-int(self.dude_4), 
                           6*self.height//8))
        
        

def main():

  Amiral_8btn().run()

if __name__ == '__main__':
  main()