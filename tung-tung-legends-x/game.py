"""Native Linux desktop application. All visuals are drawn locally with SDL."""
from __future__ import annotations
import argparse
from array import array
from collections import OrderedDict
import math
import os
from pathlib import Path
import random
import sys
import time

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame

from content import (TITLE, VERSION, REALMS, HEROES, ITEMS, EGGS, RARITIES, ABILITIES,
                     SOUL_UPGRADES, ACHIEVEMENTS)
from engine import Game, num, save_directory

WIDTH, HEIGHT = 1400, 900
BG = (15, 22, 25)
PANEL = (24, 33, 36)
CARD = (32, 43, 47)
BORDER = (50, 65, 67)
TEXT = (237, 244, 234)
MUTED = (145, 166, 169)
LIME = (211, 247, 103)
GOLD = (255, 211, 118)
PURPLE = (198, 161, 255)
RED = (255, 142, 149)

def mix(a, b, amount): return tuple(int(x*(1-amount)+y*amount) for x, y in zip(a,b))
def rect(x,y,w,h): return pygame.Rect(int(x),int(y),int(w),int(h))

class Audio:
    def __init__(self):
        self.ready = False
        self.sounds = {}
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            for name, hz, duration in [("hit",160,.055),("kill",480,.11),("buy",680,.07),
                                       ("cast",95,.25),("hatch",850,.32),("boss",320,.4),("rebirth",620,.6)]:
                samples = array("h", (int(9000*math.sin(2*math.pi*(hz+hz*.5*t/duration)*t)*(1-t/duration)**2)
                                      for t in (i/22050 for i in range(int(duration*22050)))))
                self.sounds[name] = pygame.mixer.Sound(buffer=samples)
            # A soft four-note ambient loop; no downloaded music or recordings.
            notes = [130.81,164.81,196,146.83]
            samples = array("h")
            for i in range(22050*8):
                t=i/22050
                hz=notes[int(t//2)%4]
                env=math.sin(math.pi*(t%2)/2)**2
                samples.append(int(1800*env*(math.sin(2*math.pi*hz*t)+.3*math.sin(4*math.pi*hz*t))))
            self.music=pygame.mixer.Sound(buffer=samples)
            self.music_channel=None
            self.ready=True
        except pygame.error:
            self.ready=False

    def play(self, name, settings):
        if self.ready and settings["sound"] and name in self.sounds:
            self.sounds[name].set_volume(settings["volume"])
            self.sounds[name].play()

    def update(self, settings):
        if not self.ready: return
        if settings["music"] and self.music_channel is None:
            self.music_channel=self.music.play(loops=-1)
        if self.music_channel:
            self.music_channel.set_volume(settings["volume"]*.5)
            if not settings["music"]:
                self.music_channel.stop()
                self.music_channel=None

class App:
    def __init__(self, game=None, smoke=False, save_dir=None):
        pygame.display.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((1260, 810), pygame.RESIZABLE)
        pygame.display.set_caption(TITLE)
        self.canvas = pygame.Surface((WIDTH,HEIGHT))
        self.smoke = smoke
        self.save_dir = save_dir
        self.game = game or Game.load(save_dir)
        self.audio = Audio()
        self.clock = pygame.time.Clock()
        self.running = True
        self.tab = "Heroes"
        self.scroll = 0
        self.max_scroll = 0
        self.buy_amount = 1
        self.selected_egg = 0
        self.buttons = []
        self.mouse = (0,0)
        self.fonts = {}
        self.rendered_text = OrderedDict()
        self.particles = []
        self.floaters = []
        self.anim_time = 0.0
        self.hit_flash = 0.0
        self.enemy_enter = 0.0
        self.holding = False
        self.hold_time = 0.0
        self.hold_accumulator = 0.0
        self.toasts = []
        self.tooltip = None
        self.modal = None
        self.last_save = time.monotonic()
        self.saved_text = "Autosave ready"
        self.fullscreen=False
        self.offset=(0,0)
        self.scale=1
        self.background_cache={}
        self.ui_rng=random.Random(778)
        self.stars=[(self.ui_rng.randrange(25,565),self.ui_rng.randrange(20,340),self.ui_rng.randrange(1,3)) for _ in range(40)]
        self.font_root=Path(__file__).parent / "assets"
        icon=pygame.Surface((64,64),pygame.SRCALPHA)
        pygame.draw.rect(icon,LIME,(0,0,64,64),border_radius=16)
        pygame.draw.rect(icon,(110,73,42),(20,10,24,42),border_radius=10)
        pygame.draw.circle(icon,TEXT,(28,25),4)
        pygame.draw.circle(icon,TEXT,(40,25),4)
        pygame.draw.circle(icon,BG,(29,25),2)
        pygame.draw.circle(icon,BG,(39,25),2)
        pygame.display.set_icon(icon)
        if self.game.settings["tutorial"]:
            self.modal=("welcome",None)
        elif self.game.offline_report and self.game.offline_report["coins"]>0:
            self.modal=("offline",self.game.offline_report)

    def font(self,size,bold=False,mono=False):
        key=(size,bold,mono)
        if key not in self.fonts:
            filename="mono.ttf" if mono else "bold.ttf" if bold else "regular.ttf"
            path=self.font_root/filename
            self.fonts[key]=pygame.font.Font(str(path) if path.exists() else None,size)
        return self.fonts[key]

    def text(self,string,x,y,size=18,color=TEXT,bold=False,mono=False,center=False,max_width=None):
        string=str(string)
        font=self.font(size,bold,mono)
        if max_width:
            while len(string)>2 and font.size(string)[0]>max_width: string=string[:-2]+"…"
        key=(string,size,color,bold,mono)
        if key not in self.rendered_text:
            self.rendered_text[key]=font.render(string,True,color)
            if len(self.rendered_text)>1000: self.rendered_text.popitem(last=False)
        surface=self.rendered_text[key]
        self.canvas.blit(surface,(int(x-surface.get_width()/2 if center else x),int(y)))
        return surface.get_width()

    def wrap(self,string,x,y,width,size=16,color=MUTED,line_height=24):
        words=string.split()
        line=""
        for word in words:
            test=(line+" "+word).strip()
            if self.font(size).size(test)[0]>width and line:
                self.text(line,x,y,size,color)
                y+=line_height
                line=word
            else: line=test
        if line:
            self.text(line,x,y,size,color)
            y+=line_height
        return y

    def panel(self,r,color=PANEL,radius=18,border=True):
        pygame.draw.rect(self.canvas,color,r,border_radius=radius)
        if border: pygame.draw.rect(self.canvas,BORDER,r,width=1,border_radius=radius)

    def button(self,label,r,action,enabled=True,primary=False,tip=None,small=False,color=None):
        clickable=r.clip(self.canvas.get_clip())
        hovered=clickable.collidepoint(self.mouse)
        fill=color or (LIME if primary else CARD)
        if not enabled: fill=mix(CARD,BG,.25)
        elif hovered: fill=mix(fill,TEXT,.10)
        pygame.draw.rect(self.canvas,fill,r,border_radius=10)
        if not primary: pygame.draw.rect(self.canvas,BORDER,r,width=1,border_radius=10)
        size=12 if r.width<65 else 15 if small else 17
        while size>12 and self.font(size,True).size(label)[0]>r.width-14:size-=1
        self.text(label,r.centerx,r.y+(r.height-(size+3))//2-2,
                  size,BG if primary and enabled else TEXT if enabled else MUTED,
                  bold=True,center=True,max_width=r.width-14)
        if clickable.width and clickable.height:self.buttons.append((clickable,action,enabled))
        if hovered and tip: self.tooltip=tip

    def progress(self,r,fraction,color=LIME):
        pygame.draw.rect(self.canvas,(13,23,26),r,border_radius=max(1,r.height//2))
        fraction=max(0,min(1,fraction))
        if fraction: pygame.draw.rect(self.canvas,color,rect(r.x,r.y,max(2,r.w*fraction),r.h),border_radius=max(1,r.height//2))

    def badge(self,string,x,y,color=LIME):
        w=self.font(12,True).size(string)[0]+18
        pygame.draw.rect(self.canvas,mix(color,BG,.86),rect(x,y,w,25),border_radius=7)
        self.text(string,x+9,y+5,12,color,True)
        return w

    def icon(self,kind,x,y,size=24,color=LIME):
        if kind=="gem":
            pygame.draw.polygon(self.canvas,color,[(x,y-size//2),(x+size//2,y),(x,y+size//2),(x-size//2,y)])
            pygame.draw.line(self.canvas,mix(color,TEXT,.4),(x,y-size//2),(x,y+size//2),2)
        elif kind=="coin":
            pygame.draw.circle(self.canvas,color,(x,y),size//2)
            pygame.draw.circle(self.canvas,mix(color,BG,.3),(x,y),size//2-3,2)
            self.text("T",x,y-size//2+1,size-6,BG,True,center=True)
        elif kind=="soul":
            pygame.draw.circle(self.canvas,color,(x,y-3),size//2-2)
            pygame.draw.polygon(self.canvas,color,[(x-size//2+2,y),(x+size//2-2,y),(x,y+size//2+3)])
            pygame.draw.circle(self.canvas,BG,(x-3,y-4),2)
            pygame.draw.circle(self.canvas,BG,(x+3,y-4),2)
        elif kind=="shard":
            pygame.draw.polygon(self.canvas,color,[(x-7,y+11),(x-4,y-9),(x+8,y-13),(x+6,y+5)])
        else:
            self.text(kind,x,y-12,20,color,True,center=True)

    def set_tab(self,tab):
        self.tab=tab
        self.scroll=0
        self.max_scroll=0

    def toggle(self,key):
        self.game.settings[key]=not self.game.settings[key]

    def safe_save(self):
        if self.smoke: return
        try:
            self.game.save(self.save_dir)
            self.saved_text="Saved "+time.strftime("%H:%M")
            self.last_save=time.monotonic()
        except OSError as e:
            self.game.notify("Could not save: "+str(e)[:80])
            self.saved_text="SAVE FAILED - check disk access"

    def topbar(self):
        self.badge("OFFLINE DESKTOP / v"+VERSION,24,17)
        self.text("TUNG TUNG",24,46,30,TEXT,True)
        self.text("TUNGLEGENDSS",224,48,24,LIME,True)
        self.text("X",451,41,41,LIME,True)
        self.text("FARM. HATCH. REBIRTH. REPEAT.",25,86,12,MUTED,True)
        currencies=[("TUNGS",self.game.coins,"coin",GOLD), ("GEMS",self.game.gems,"gem",PURPLE),
                    ("SOULS",self.game.souls,"soul",LIME), ("SHARDS",self.game.shards,"shard",(129,220,226))]
        for i,(label,value,kind,color) in enumerate(currencies):
            x=532+i*212
            self.panel(rect(x,25,198,73),radius=14)
            self.icon(kind,x+26,62,24,color)
            self.text(label,x+48,35,11,MUTED,True)
            self.text(num(value),x+48,55,23,TEXT,True,mono=True,max_width=141)

    def sidebar(self):
        self.panel(rect(24,120,200,756))
        r=REALMS[self.game.realm()]
        self.text("YOUR EXPEDITION",42,140,11,MUTED,True)
        self.text("Realm "+str((self.game.zone-1)//100+1).zfill(2),42,166,26,r[2],True)
        self.wrap(r[0],42,202,161,17,TEXT,23)
        self.text("STAGE "+str(self.game.zone).zfill(4),42,257,14,MUTED,True,mono=True)
        self.progress(rect(42,288,164,6),((self.game.zone-1)%100)/100,r[2])
        tabs=[("Heroes","01"),("Pets","02"),("Forge","03"),("Rebirth","04"),("Quests","05"),("Realms","06"),("Settings","07")]
        for i,(tab,number) in enumerate(tabs):
            y=322+i*53
            selected=self.tab==tab
            if selected: pygame.draw.rect(self.canvas,LIME,rect(36,y,176,44),border_radius=10)
            self.text(number,49,y+12,12,BG if selected else MUTED,True,mono=True)
            self.text(tab,79,y+10,18,BG if selected else TEXT,True)
            self.buttons.append((rect(36,y,176,44),lambda t=tab:self.set_tab(t),True))
            if tab=="Quests" and self.game.ready_rewards():
                pygame.draw.circle(self.canvas,RED,(195,y+21),8)
                self.text(str(min(9,self.game.ready_rewards())),195,y+13,12,BG,True,center=True)
        pygame.draw.line(self.canvas,BORDER,(42,719),(205,719),1)
        s=self.game.combat_stats()
        self.text("PERMANENT POWER",42,738,11,MUTED,True)
        self.text(num(s["rebirth"]*s["astral"])+"x",42,762,27,LIME,True,mono=True)
        self.text(str(self.game.stats["rebirths"])+" rebirths / "+str(self.game.astrals)+" astrals",42,804,12,MUTED)
        self.text(self.saved_text,42,846,11,MUTED,max_width=164)

    def scenery(self,r):
        realm=self.game.realm()
        if realm not in self.background_cache:
            surface=pygame.Surface((r.w,r.h))
            theme=REALMS[realm][2]
            for y in range(r.h):
                amount=y/r.h
                c=mix((20,38,40),mix(theme,BG,.82),amount)
                pygame.draw.line(surface,c,(0,y),(r.w,y))
            style=REALMS[realm][3]
            rr=random.Random(realm+46)
            for x,y,s in self.stars:
                pygame.draw.circle(surface,mix(theme,TEXT,.15),(x,min(y,r.h-40)),s)
            if style in ("forest","candy","ice"):
                for i in range(13):
                    x=i*49-10
                    h=rr.randrange(130,240)
                    c=mix(theme,BG,.79)
                    pygame.draw.rect(surface,c,(x+15,r.h-h,12,h))
                    if style=="ice":
                        pygame.draw.polygon(surface,c,[(x,r.h),(x+25,r.h-h-30),(x+50,r.h)])
                    else:
                        pygame.draw.circle(surface,c,(x+21,r.h-h+20),rr.randrange(24,45))
            elif style in ("city","forge"):
                for i in range(14):
                    x=i*45
                    h=rr.randrange(85,240)
                    c=mix(theme,BG,.8)
                    pygame.draw.rect(surface,c,(x,r.h-h,35,h))
                    for yy in range(r.h-h+12,r.h-15,25):
                        if rr.random()<.7:pygame.draw.rect(surface,mix(theme,BG,.53),(x+9,yy,4,8))
            elif style=="water":
                for i in range(10):
                    pygame.draw.arc(surface,mix(theme,BG,.65),rect(-20,r.h-100+i*13,r.w+30,50),0,math.pi,2)
            else:
                pygame.draw.circle(surface,mix(theme,BG,.8),(r.w-115,94),52)
                pygame.draw.ellipse(surface,mix(theme,BG,.65),rect(r.w-189,72,148,44),3)
                if style=="storm":
                    pygame.draw.lines(surface,mix(theme,BG,.45),False,[(74,20),(52,74),(87,69),(58,142)],5)
            pygame.draw.ellipse(surface,mix(theme,BG,.87),rect(55,r.h-80,r.w-100,140))
            self.background_cache[realm]=surface
        self.canvas.blit(self.background_cache[realm],r)

    def tung(self,x,y,scale=1,boss=False,variant=0,hit=0):
        """Original wooden character art. Anchored at its feet."""
        s=scale
        motion=math.sin(self.anim_time*2.5)*4 if self.game.settings["motion"] else 0
        x+=int(math.sin(hit*65)*hit*14)
        y+=int(motion)
        def R(a,b,w,h):return rect(x+a*s,y+b*s,w*s,h*s)
        def P(a,b):return (int(x+a*s),int(y+b*s))
        wood=(185,127,79) if not boss else mix((185,127,79),REALMS[self.game.realm()][2],.13)
        if hit>0:wood=mix(wood,TEXT,min(.7,hit*3))
        dark=(89,56,39)
        pygame.draw.ellipse(self.canvas,(10,22,23),R(-66,2,142,22))
        pygame.draw.line(self.canvas,dark,P(-29,-62),P(-39,-2),int(13*s))
        pygame.draw.line(self.canvas,dark,P(29,-62),P(40,-2),int(13*s))
        pygame.draw.ellipse(self.canvas,(143,95,62),R(-65,-9,49,17))
        pygame.draw.ellipse(self.canvas,(143,95,62),R(15,-9,49,17))
        pygame.draw.line(self.canvas,dark,P(-47,-150),P(-90,-95),int(12*s))
        pygame.draw.line(self.canvas,dark,P(48,-143),P(90,-119),int(12*s))
        pygame.draw.line(self.canvas,(147,98,63),P(92,-89),P(118,-215),int(16*s))
        pygame.draw.line(self.canvas,(217,161,103),P(95,-120),P(114,-208),int(5*s))
        pygame.draw.rect(self.canvas,dark,R(-58,-252,116,198),border_radius=int(36*s))
        pygame.draw.rect(self.canvas,wood,R(-53,-247,106,186),border_radius=int(32*s))
        pygame.draw.ellipse(self.canvas,(209,156,99),R(-53,-261,106,38))
        pygame.draw.ellipse(self.canvas,dark,R(-33,-252,66,21),int(2*s))
        pygame.draw.ellipse(self.canvas,dark,R(-17,-247,34,12),int(2*s))
        for i in [-36,-15,16,36]:
            pygame.draw.line(self.canvas,mix(wood,dark,.2),P(i,-220+abs(i)*.4),P(i+4,-85),max(1,int(2*s)))
        for ex in [-23,24]:
            pygame.draw.ellipse(self.canvas,(251,245,211),R(ex-17,-214,34,49))
            pygame.draw.ellipse(self.canvas,(33,30,27),R(ex-6,-203,15,30))
            pygame.draw.circle(self.canvas,(255,255,240),P(ex,-198),max(1,int(3*s)))
        pygame.draw.arc(self.canvas,dark,R(-27,-158,54,34),math.pi+.05,2*math.pi-.05,max(2,int(4*s)))
        pygame.draw.line(self.canvas,dark,P(-37,-227),P(-7,-232),max(2,int(4*s)))
        pygame.draw.line(self.canvas,dark,P(9,-232),P(37,-227),max(2,int(4*s)))
        if boss:
            pygame.draw.polygon(self.canvas,GOLD,[P(-60,-269),P(-57,-312),P(-30,-291),P(0,-326),P(30,-291),P(57,-312),P(60,-269)])
            pygame.draw.rect(self.canvas,(176,134,68),R(-60,-277,120,13))
            for ex in [-33,0,33]:pygame.draw.circle(self.canvas,PURPLE,P(ex,-279),max(2,int(4*s)))

    def pet_sprite(self,pet,x,y,size=24):
        color=RARITIES[pet["rarity"]][3]
        variant=pet["egg"]%3
        pygame.draw.ellipse(self.canvas,mix(color,BG,.83),rect(x-size,y+size*.7,size*2,size*.5))
        if variant==0:
            pygame.draw.polygon(self.canvas,color,[(x-size,y),(x-size//2,y-size),(x,y-size//2),(x+size//2,y-size),(x+size,y)])
        elif variant==1:
            pygame.draw.polygon(self.canvas,color,[(x-size,y+4),(x-size*1.6,y-size),(x,y-size//2),(x+size*1.6,y-size),(x+size,y+4)])
        else:
            pygame.draw.circle(self.canvas,mix(color,TEXT,.3),(int(x),int(y-size*.6)),int(size*.8))
        pygame.draw.ellipse(self.canvas,color,rect(x-size,y-size*.5,size*2,size*1.5))
        pygame.draw.circle(self.canvas,BG,(int(x-size*.35),int(y)),max(2,int(size*.12)))
        pygame.draw.circle(self.canvas,BG,(int(x+size*.35),int(y)),max(2,int(size*.12)))
        pygame.draw.arc(self.canvas,BG,rect(x-size*.24,y+size*.12,size*.5,size*.35),math.pi,2*math.pi,2)
        if pet["shiny"]:self.text("+",x+size-1,y-size-10,18,GOLD,True)

    def combat(self):
        self.panel(rect(244,120,610,552))
        self.badge("BOSS ENCOUNTER" if self.game.is_boss() else "FARMING GROUNDS",264,139,RED if self.game.is_boss() else LIME)
        if self.game.zone>1200:self.badge("ENDLESS",655,139,PURPLE)
        self.text(self.game.enemy_name(),264,179,25,TEXT,True,max_width=390)
        self.text("STAGE "+str(self.game.zone),780,186,13,MUTED,True,mono=True,center=True)
        self.scenery(rect(260,220,578,333))
        bob=math.sin(self.anim_time*1.7)*3 if self.game.settings["motion"] else 0
        self.tung(548,520+bob,.91 if not self.game.is_boss() else .89,self.game.is_boss(),hit=self.hit_flash)
        self.buttons.append((rect(380,233,330,309),self.manual_hit,True))
        selected=[p for p in self.game.pets if p["id"] in self.game.equipped_pets]
        for i,p in enumerate(selected[:5]):
            x=330+i*96
            yy=531+math.sin(self.anim_time*3+i)*4 if self.game.settings["motion"] else 531
            self.pet_sprite(p,x,yy,16)
        for f in self.floaters:
            self.text(f["text"],f["x"],f["y"],f["size"],f["color"],True,center=True)
        for p in self.particles:
            pygame.draw.circle(self.canvas,p["color"],(int(p["x"]),int(p["y"])),max(1,int(p["life"]*5)))
        ratio=self.game.hp/self.game.max_hp
        self.progress(rect(276,565,546,12),ratio,RED if self.game.is_boss() else LIME)
        self.text(num(self.game.hp)+" / "+num(self.game.max_hp)+" HP",276,587,13,MUTED,mono=True)
        if self.game.is_boss():
            self.text(f"{self.game.boss_time:.1f}s remaining",740,587,13,RED,True,center=True)
        else:
            self.text(str(self.game.zone_kills)+" / 5 farmed",751,587,13,MUTED)
        self.button("KNOCK  /  HOLD OR SPACE",rect(276,614,388,40),self.manual_hit,primary=True,tip="Hold this button or hold Space to farm 7 times per second.")
        self.button("<",rect(676,614,43,40),lambda:self.game.move_zone(self.game.zone-1),self.game.zone>1)
        self.button(">",rect(730,614,43,40),lambda:self.game.move_zone(self.game.zone+1),self.game.zone<self.game.max_zone)
        self.button("AUTO" if self.game.auto_progress else "STAY",rect(784,614,53,40),self.toggle_progress,small=True,
                    tip="AUTO moves to the next stage after 5 kills. STAY farms this stage indefinitely.")

    def toggle_progress(self):
        self.game.auto_progress=not self.game.auto_progress

    def manual_hit(self):
        self.game.click()
        self.hit_flash=.24

    def cast(self,key):
        if self.game.cast(key):self.hit_flash=.28

    def ability_tray(self):
        self.panel(rect(244,692,610,184))
        s=self.game.combat_stats()
        self.text("CLICK POWER",264,710,10,MUTED,True)
        self.text(num(self.game.click_damage()),264,729,20,TEXT,True,mono=True)
        self.text("HERO DPS",441,710,10,MUTED,True)
        self.text(num(self.game.idle_damage()),441,729,20,TEXT,True,mono=True)
        self.text("PET MULTIPLIER",629,710,10,MUTED,True)
        self.text(num(s["pet"])+"x",629,729,20,PURPLE,True,mono=True)
        keys=self.game.available_abilities()
        width=(570-(len(keys)-1)*8)/len(keys)
        for i,key in enumerate(keys):
            name,_,_,tip=ABILITIES[key]
            x=264+i*(width+8)
            cd=self.game.cooldowns[key]
            active=self.game.buffs[key]>0
            label=f"{i+1}  "+(f"{cd:.0f}s" if cd>0 and not active else name)
            self.button(label,rect(x,767,width,47),lambda k=key:self.cast(k),cd<=0,primary=cd<=0,
                        color=mix(PURPLE,BG,.25) if active else None,tip=tip,small=True)
            if active:self.text(f"ACTIVE {self.game.buffs[key]:.0f}s",x+width/2,820,10,PURPLE,True,center=True)
            elif cd>0:self.progress(rect(x,819,width,3),1-cd/ABILITIES[key][1],PURPLE)
        if self.game.failed_boss:
            self.button("RETRY STAGE "+str(self.game.failed_boss),rect(264,839,237,25),self.retry_boss,small=True,color=mix(RED,BG,.8))
        else:self.text("Abilities come from equipped gear. Number keys activate them.",264,844,11,MUTED)

    def retry_boss(self):
        if self.game.failed_boss:
            zone=self.game.failed_boss
            self.game.auto_progress=True
            self.game.move_zone(zone)
            self.game.failed_boss=None

    def right_header(self,title,subtitle):
        self.panel(rect(874,120,502,756))
        self.text(title,896,143,27,TEXT,True)
        self.text(subtitle,896,184,12,MUTED,max_width=450)

    def content_clip(self,top=245):
        self.canvas.set_clip(rect(886,top,478,604-(top-245)))

    def finish_content(self,bottom,top=245):
        self.canvas.set_clip(None)
        self.max_scroll=max(0,bottom+self.scroll-849)
        if self.max_scroll:
            self.text("SCROLL TO EXPLORE",896,856,10,MUTED,True)
            fraction=min(1,580/(self.max_scroll+580))
            y=top+(600-600*fraction)*(self.scroll/self.max_scroll)
            pygame.draw.rect(self.canvas,BORDER,rect(1361,y,3,600*fraction),border_radius=2)

    def heroes_panel(self):
        self.right_header("Your knock squad", "Passive DPS. Every 25 hero levels doubles their output.")
        for i,amount in enumerate([1,10,25,100]):
            self.button("BUY "+str(amount),rect(896+i*113,213,105,31),lambda a=amount:setattr(self,"buy_amount",a),
                        primary=self.buy_amount==amount,small=True)
        self.content_clip(258)
        y=260-self.scroll
        self.panel(rect(896,y,448,88),CARD,12)
        self.text("YOUR KNOCK",915,y+13,16,TEXT,True)
        self.text("Lv. "+str(self.game.tap_level)+" / boosts manual & auto clicks",915,y+43,12,MUTED)
        self.button(num(self.game.tap_cost())+" T",rect(1193,y+19,135,43),lambda:self.game.buy_taps(self.buy_amount),
                    self.game.coins>=self.game.tap_cost(),primary=True,small=True,tip="Buy click upgrades using tungs. The selected buy amount also applies here.")
        y+=100
        for i,(name,cost,dps,desc) in enumerate(HEROES):
            level=self.game.heroes[i]
            self.panel(rect(896,y,448,103),CARD,12)
            self.text(str(i+1).zfill(2),912,y+17,14,LIME if level else MUTED,True,mono=True)
            self.text(name,946,y+13,17,TEXT,True,max_width=245)
            self.text("LEVEL "+str(level),946,y+40,11,LIME if level else MUTED,True)
            self.text(desc,915,y+74,12,MUTED,max_width=260)
            actual=min(self.buy_amount,3000-level)
            price=self.game.hero_buy_cost(i,self.buy_amount)
            self.button("+"+str(actual)+" / "+num(price),rect(1193,y+17,135,42),lambda idx=i:self.game.buy_hero(idx,self.buy_amount),
                        level<3000 and self.game.coins>=self.game.hero_cost(i),primary=True,small=True,
                        tip="Buys as many of the selected amount as you can afford. Shown cost is the full batch.")
            if level:
                self.progress(rect(1193,y+77,133,4),(level%25)/25,LIME)
                if rect(1193,y+63,133,25).collidepoint(self.mouse):self.tooltip="Next 2x damage milestone: level "+str((level//25+1)*25)
            else:self.text(num(dps)+" base DPS",1193,y+74,11,MUTED)
            y+=115
        self.finish_content(y,258)

    def pets_panel(self):
        self.right_header("The hatchery", "Equipped pet multipliers multiply together. Auto-equips your best team.")
        self.button("<",rect(896,213,33,30),lambda:setattr(self,"selected_egg",(self.selected_egg-1)%len(EGGS)),small=True)
        self.button(">",rect(1312,213,33,30),lambda:setattr(self,"selected_egg",(self.selected_egg+1)%len(EGGS)),small=True)
        egg=EGGS[self.selected_egg]
        self.text(egg[0],1120,216,17,egg[3],True,center=True)
        self.content_clip(257)
        y=260-self.scroll
        self.panel(rect(896,y,448,151),CARD,12)
        pygame.draw.ellipse(self.canvas,mix(egg[3],BG,.15),rect(917,y+21,58,72))
        pygame.draw.arc(self.canvas,egg[3],rect(922,y+27,48,52),-.2,math.pi+.2,3)
        self.text("Reach stage "+str(egg[2]) if self.game.stats["best_zone"]<egg[2] else "6 species / 6 rarities",995,y+16,15,TEXT,True)
        self.text("Epic every 10. Legendary every 40.",995,y+43,12,MUTED)
        self.text("Mythic every 120. Shiny chance: 2.5%.",995,y+63,12,MUTED)
        pity=self.game.pity[self.selected_egg]
        self.text("Hatches: "+str(pity)+"  /  next epic in "+str(10-pity%10),917,y+111,12,MUTED)
        self.button("HATCH / "+str(egg[1])+" G",rect(1154,y+94,176,39),lambda:self.game.hatch(self.selected_egg),
                    self.game.gems>=egg[1] and self.game.stats["best_zone"]>=egg[2],primary=True,small=True)
        if rect(896,y,448,151).collidepoint(self.mouse):
            self.tooltip="Base odds: Common 58%, Uncommon 24%, Rare 12%, Epic 5%, Legendary 0.9%, Mythic 0.1%. Lucky Shell improves odds. Pity guarantees override these rolls."
        y+=166
        self.text("FORMATION "+str(len(self.game.equipped_pets))+" / "+str(self.game.pet_slots()),896,y+5,13,PURPLE,True)
        self.button("EQUIP BEST",rect(1215,y,129,29),self.game.auto_equip,small=True)
        y+=42
        if not self.game.pets:
            y=self.wrap("Your first 65 gems can hatch two Bamboo Eggs. Claim quests for more gems. Pets and their stars survive rebirths.",910,y+15,420,17,TEXT,27)+30
        pets=sorted(self.game.pets,key=self.game.pet_multiplier,reverse=True)
        for p in pets:
            if y+112<257 or y>849:
                y+=125
                continue
            self.panel(rect(896,y,448,112),CARD,12)
            self.pet_sprite(p,930,y+43,22)
            color=RARITIES[p["rarity"]][3]
            name=("Shiny " if p["shiny"] else "")+self.game.pet_name(p)
            self.text(name,971,y+12,17,TEXT,True,max_width=245)
            self.text(RARITIES[p["rarity"]][0]+" / "+str(p["stars"])+" stars",971,y+39,12,color,True)
            self.text(f"{self.game.pet_multiplier(p):.2f}x",1300,y+18,21,PURPLE,True,mono=True,center=True)
            equipped=p["id"] in self.game.equipped_pets
            self.button("IN TEAM" if equipped else "EQUIP",rect(915,y+73,123,27),lambda pid=p["id"]:self.game.equip_pet(pid),primary=equipped,small=True)
            self.button("FUSE 3",rect(1048,y+73,129,27),lambda pid=p["id"]:self.game.fuse(pid),small=True,tip="3 matching pets become one pet with +1 star and 1.55x power. Max 8 stars.")
            self.button("RECYCLE",rect(1187,y+73,141,27),lambda pid=p["id"]:setattr(self,"modal",("recycle",pid)),small=True,
                        tip="Convert this pet to permanent crafting shards.")
            y+=125
        self.finish_content(y,257)

    def forge_panel(self):
        self.right_header("Gear & abilities", "One item per slot. Gear and upgrade ranks survive both prestige layers.")
        self.text("Bosses drop shards. Recycle spare pets for more.",896,215,12,MUTED)
        self.content_clip()
        y=250-self.scroll
        for item in ITEMS:
            owned=item["id"] in self.game.items
            unlocked=self.game.stats["best_zone"]>=item["zone"]
            equipped=item["id"] in self.game.equipment.values()
            self.panel(rect(896,y,448,137),CARD,12)
            self.icon("shard",923,y+35,25,item["color"])
            self.text(item["name"],947,y+15,18,TEXT if unlocked else MUTED,True)
            self.text(item["slot"].upper()+" / "+("RANK "+str(self.game.items[item["id"]]) if owned else "STAGE "+str(item["zone"])),947,y+42,11,item["color"],True)
            self.text(item["desc"],914,y+71,13,MUTED,max_width=412)
            if owned:
                self.button("EQUIPPED" if equipped else "EQUIP",rect(914,y+98,181,27),lambda iid=item["id"]:self.game.equip_item(iid),primary=equipped,small=True)
                cost=self.game.item_cost(item["id"])
                self.button("RANK UP / "+str(cost)+" S",rect(1106,y+98,222,27),lambda iid=item["id"]:self.game.upgrade_item(iid),
                            self.game.shards>=cost and self.game.items[item["id"]]<50,small=True)
            else:
                self.button("CRAFT / "+str(item["price"])+" G" if unlocked else "LOCKED / STAGE "+str(item["zone"]),
                            rect(914,y+98,414,27),lambda iid=item["id"]:self.game.buy_item(iid),
                            unlocked and self.game.gems>=item["price"],primary=True,small=True)
            y+=150
        self.finish_content(y)

    def rebirth_panel(self):
        self.right_header("Become a louder legend", "Rebirth at 50. Ascend at 300. Earn permanent power.")
        self.text("Damage: "+num(self.game.combat_stats()["rebirth"])+"x souls / "+num(self.game.combat_stats()["astral"])+"x astrals",896,215,13,LIME,True)
        self.content_clip()
        y=250-self.scroll
        self.panel(rect(896,y,448,163),CARD,12)
        self.text("REBIRTH",914,y+16,22,LIME,True)
        self.text("+"+num(self.game.rebirth_reward())+" SOULS",1248,y+21,16,LIME,True,center=True,max_width=162)
        self.wrap("Resets coins, hero levels, click upgrades and stages. Keeps pets, gear, gems, shards, quests and soul upgrades.",914,y+52,411,13,MUTED,21)
        self.button("REBIRTH NOW" if self.game.rebirth_reward() else "REACH STAGE 50",rect(914,y+117,414,32),lambda:setattr(self,"modal",("rebirth",None)),
                    bool(self.game.rebirth_reward()),primary=True,small=True)
        y+=177
        self.panel(rect(896,y,448,155),CARD,12)
        self.text("ASTRAL ASCENSION",914,y+15,20,PURPLE,True)
        self.wrap("Each astral doubles all damage. Resets the run, souls and soul upgrades. Keeps pets, gear, gems, shards and achievements.",914,y+50,413,13,MUTED,21)
        self.button("ASCEND / +"+str(self.game.ascension_reward())+" ASTRALS" if self.game.ascension_reward() else "REACH STAGE 300 THIS RUN",rect(914,y+113,414,30),
                    lambda:setattr(self,"modal",("ascend",None)),bool(self.game.ascension_reward()),small=True,color=mix(PURPLE,BG,.65))
        y+=174
        self.text("SOUL RESEARCH",898,y,13,LIME,True)
        y+=29
        for key,name,base,growth,limit,desc in SOUL_UPGRADES:
            level=self.game.upgrades[key]
            cost=self.game.soul_cost(key)
            self.panel(rect(896,y,448,97),CARD,12)
            self.text(name,914,y+13,17,TEXT,True)
            self.text("RANK "+str(level)+" / "+str(limit),914,y+39,11,LIME,True)
            self.text(desc,914,y+67,12,MUTED,max_width=413)
            self.button("MAXED" if level>=limit else str(cost)+" SOULS",rect(1184,y+16,144,38),lambda k=key:self.game.buy_soul_upgrade(k),
                        level<limit and self.game.souls>=cost,primary=True,small=True)
            y+=109
        self.finish_content(y)

    def quests_panel(self):
        self.right_header("The bounty board", "Repeatable contracts + permanent achievements. All rewards are earned.")
        self.text("No ads. No real-money shop. No accounts.",896,215,12,LIME)
        self.content_clip()
        y=250-self.scroll
        self.text("CONTRACT ROUND "+str(self.game.contract_tier+1),896,y,12,PURPLE,True)
        y+=29
        for i,c in enumerate(self.game.contracts):
            amount=max(0,self.game.stats[c["metric"]]-c["start"])
            done=amount>=c["goal"]
            self.panel(rect(896,y,448,104),CARD,12)
            self.text(c["label"],914,y+14,17,TEXT,True)
            self.text(str(min(amount,c["goal"]))+" / "+str(c["goal"]),914,y+42,12,MUTED,mono=True)
            self.text("+"+str(c["gems"])+" gems / +"+str(3+self.game.contract_tier)+" shards",914,y+76,12,PURPLE)
            self.progress(rect(914,y+65,240,4),amount/c["goal"],PURPLE)
            self.button("CLAIMED" if c["claimed"] else "CLAIM",rect(1200,y+18,127,40),lambda idx=i:self.game.claim_contract(idx),
                        done and not c["claimed"],primary=True,small=True)
            y+=116
        y+=8
        self.text("ACHIEVEMENTS "+str(len(self.game.claimed))+" / "+str(len(ACHIEVEMENTS)),896,y,12,LIME,True)
        y+=29
        for aid,name,metric,goal,reward in ACHIEVEMENTS:
            owned=aid in self.game.claimed
            amount=self.game.stats[metric]
            self.panel(rect(896,y,448,100),CARD,12)
            self.text(name,914,y+14,17,MUTED if owned else TEXT,True,max_width=260)
            self.text(num(min(goal,amount))+" / "+num(goal)+" "+metric.replace("_"," "),914,y+42,12,MUTED)
            self.progress(rect(914,y+72,240,4),amount/goal,LIME)
            self.button("CLAIMED" if owned else "+"+str(reward)+" GEMS",rect(1200,y+22,127,39),lambda a=aid:self.game.claim_achievement(a),
                        amount>=goal and not owned,primary=True,small=True)
            y+=112
        self.finish_content(y)

    def realms_panel(self):
        self.right_header("A very long expedition", "12 realms. 1,200 campaign stages. Endless stages after the final boss.")
        self.text("Lifetime best: "+str(self.game.stats["best_zone"])+" / run best: "+str(self.game.run_best),896,215,13,LIME)
        self.content_clip()
        y=250-self.scroll
        for i,(name,desc,color,style) in enumerate(REALMS):
            stage=i*100+1
            unlocked=self.game.stats["best_zone"]>=stage
            run_unlocked=self.game.max_zone>=stage
            self.panel(rect(896,y,448,116),CARD,12)
            self.text(str(i+1).zfill(2),914,y+15,25,color if unlocked else MUTED,True,mono=True)
            self.text(name,965,y+17,18,TEXT if unlocked else MUTED,True,max_width=350)
            self.text("STAGES "+str(stage)+" - "+str(stage+99),965,y+46,11,color if unlocked else MUTED,True)
            self.text(desc,914,y+80,12,MUTED,max_width=316)
            self.button("TRAVEL" if run_unlocked else "LOCKED",rect(1223,y+74,104,27),lambda z=stage:self.game.move_zone(z),run_unlocked,small=True)
            y+=128
        self.panel(rect(896,y,448,112),mix(PURPLE,BG,.86),12)
        self.text("ENDLESS ECHOES",914,y+18,21,PURPLE,True)
        self.wrap("After stage 1,200, difficulty and rewards keep rising. Rebirth for souls or ascend for astrals to push further.",914,y+52,408,14,TEXT,23)
        self.finish_content(y+125)

    def settings_panel(self):
        self.right_header("Make yourself at home", "The game runs locally. Close it whenever you want; your squad stays.")
        self.button("SAVE NOW",rect(896,212,216,32),self.safe_save,primary=True,small=True)
        self.button("HOW TO PLAY",rect(1124,212,220,32),lambda:setattr(self,"modal",("welcome",None)),small=True)
        self.content_clip(258)
        y=267-self.scroll
        for key,label,desc in [("sound","Sound effects","A satisfying knock, if you want one."),
                               ("music","Ambient music","A quiet, locally generated loop."),
                               ("motion","Character motion","Disable for a calmer screen."),
                               ("particles","Particles","Disable to reduce visual clutter.")]:
            self.panel(rect(896,y,448,83),CARD,12)
            self.text(label,914,y+14,17,TEXT,True)
            self.text(desc,914,y+45,12,MUTED)
            self.button("ON" if self.game.settings[key] else "OFF",rect(1243,y+19,85,38),lambda k=key:self.toggle(k),primary=self.game.settings[key],small=True)
            y+=95
        self.panel(rect(896,y,448,83),CARD,12)
        self.text("Battery mode",914,y+14,17,TEXT,True)
        self.text("30 FPS saves power. Gameplay stays the same.",914,y+45,12,MUTED)
        self.button(str(self.game.settings["fps"])+" FPS",rect(1243,y+19,85,38),self.toggle_fps,small=True)
        y+=99
        self.text("YOUR CAREER",896,y,13,LIME,True)
        y+=30
        for label,value in [("Tungs farmed",num(self.game.stats["kills"])),("Bosses defeated",num(self.game.stats["bosses"])),
                            ("Manual knocks",num(self.game.stats["clicks"])),("Pets hatched",num(self.game.stats["hatches"])),
                            ("Rebirths",str(self.game.stats["rebirths"])),("Time played",f"{self.game.playtime/3600:.1f} hours")]:
            self.text(label,914,y,15,MUTED)
            self.text(value,1210,y,15,TEXT,True)
            y+=28
        y+=19
        self.text("KEYBOARD",896,y,13,LIME,True)
        y+=28
        y=self.wrap("Space: hold to farm. 1-5: abilities. H/P/F/R/Q/M/S: tabs. A: auto-advance. F11: fullscreen. Escape: close dialog or leave fullscreen.",914,y,413,14,MUTED,24)
        y+=15
        y=self.wrap("Offline farming: 25% of idle output, up to 8 hours. Dream Farmer research raises this to 75%. Bosses and stages never advance offline.",914,y,413,14,MUTED,24)
        y+=15
        self.text("Save folder",914,y,13,TEXT,True)
        y+=24
        y=self.wrap(str(save_directory()),914,y,413,12,MUTED,21)
        y+=20
        self.button("RESET ALL PROGRESS",rect(914,y,414,34),lambda:setattr(self,"modal",("reset",None)),small=True,color=mix(RED,BG,.82))
        self.finish_content(y+50,258)

    def toggle_fps(self):self.game.settings["fps"]=30 if self.game.settings["fps"]==60 else 60

    def draw_modal(self):
        if not self.modal:return
        kind,data=self.modal
        overlay=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
        overlay.fill((0,0,0,185))
        self.canvas.blit(overlay,(0,0))
        self.buttons=[]
        self.panel(rect(377,183,646,526),PANEL,24)
        if kind=="welcome":
            self.badge("YOUR NEXT VERY LOUD OBSESSION",403,211)
            self.text("Become the last Tung legend.",403,253,31,TEXT,True)
            steps=[("01","FARM TUNGS","Click the character or hold Space. Buy heroes for idle DPS."),
                   ("02","BUILD YOUR TEAM","Hatch pets, multiply their power, and fuse 3 matching pets."),
                   ("03","BREAK THE CEILING","Craft gear for abilities. Rebirth at 50. Ascend at 300."),
                   ("04","GO THE DISTANCE","12 realms, 1,200 stages, then endless. Progress saves locally.")]
            for i,(n,title,desc) in enumerate(steps):
                yy=314+i*72
                self.text(n,404,yy+2,20,LIME,True,mono=True)
                self.text(title,451,yy,15,TEXT,True)
                self.wrap(desc,451,yy+25,530,13,MUTED,20)
            self.button("LET'S GET KNOCKING",rect(403,635,594,47),self.close_welcome,primary=True)
        elif kind=="offline":
            self.badge("WELCOME BACK",403,213,PURPLE)
            self.text("Your squad kept the beat.",403,262,30,TEXT,True)
            self.text("+"+num(data["coins"])+" TUNGS",403,336,41,GOLD,True,mono=True)
            self.wrap(f"{num(data['kills'])} tungs farmed in {data['seconds']//60} minutes at {int(data['efficiency']*100)}% efficiency. Offline income caps at 8 hours.",403,411,577,18,MUTED,29)
            self.wrap("Spend your earnings on heroes and push the next boss.",403,512,572,18,TEXT,29)
            self.button("COLLECT & CONTINUE",rect(403,630,594,49),lambda:setattr(self,"modal",None),primary=True)
        else:
            labels={"rebirth":("REBIRTH","Start again. Hit much harder.","Coins, heroes, click levels and stages reset. Pets, gear, gems, shards, quests and soul research stay.",f"You earn {self.game.rebirth_reward()} souls."),
                    "ascend":("ASTRAL ASCENSION","A new dimension of power.","The run, souls and ALL soul research reset. Pets, equipment, gems, shards, achievements and astrals stay.",f"You earn {self.game.ascension_reward()} astrals. Each doubles damage."),
                    "recycle":("RECYCLE PET","Trade this pet for shards.","This removes the selected pet and gives crafting shards. The pet cannot be recovered.","Check that you do not need it for fusion."),
                    "reset":("RESET PROGRESS","Start a completely new legend.","This clears ALL current progress. Your existing save will be copied to reset-recovery.json before the new game starts.","Use this only if you want to start over.")}
            badge,title,desc,reward=labels[kind]
            self.badge(badge,403,214,RED if kind=="reset" else PURPLE)
            self.text(title,403,264,29,TEXT,True)
            self.wrap(desc,403,334,574,20,MUTED,32)
            self.wrap(reward,403,479,574,20,LIME,32)
            self.button("CANCEL",rect(403,627,275,51),lambda:setattr(self,"modal",None))
            self.button("CONFIRM",rect(693,627,304,51),lambda:self.confirm_modal(kind,data),primary=True)

    def close_welcome(self):
        self.game.settings["tutorial"]=False
        self.modal=None
        if self.game.offline_report and self.game.offline_report["coins"]>0:
            self.modal=("offline",self.game.offline_report)
            self.game.offline_report=None

    def confirm_modal(self,kind,data):
        if kind=="rebirth":self.game.rebirth()
        elif kind=="ascend":self.game.ascend()
        elif kind=="recycle":self.game.recycle_pet(data)
        elif kind=="reset":
            if not self.smoke:
                import shutil
                directory=Path(self.save_dir) if self.save_dir else save_directory()
                try:
                    self.game.save(directory)
                    shutil.copy2(directory/"save.json",directory/"reset-recovery.json")
                except OSError:
                    self.game.notify("Reset cancelled: could not preserve a recovery save.")
                    self.modal=None
                    return
            settings=self.game.settings.copy()
            self.game=Game()
            self.game.settings=settings
        self.modal=None
        self.scroll=0
        self.safe_save()

    def draw(self):
        self.canvas.fill(BG)
        self.buttons=[]
        self.tooltip=None
        self.topbar()
        self.sidebar()
        self.combat()
        self.ability_tray()
        panels={"Heroes":self.heroes_panel,"Pets":self.pets_panel,"Forge":self.forge_panel,"Rebirth":self.rebirth_panel,
                "Quests":self.quests_panel,"Realms":self.realms_panel,"Settings":self.settings_panel}
        panels[self.tab]()
        for i,toast in enumerate(self.toasts[-3:]):
            y=108+i*40
            w=min(790,self.font(14,True).size(toast[0])[0]+38)
            self.panel(rect(700-w/2,y,w,34),mix(LIME,BG,.85),10)
            self.text(toast[0],700,y+8,14,TEXT,True,center=True,max_width=w-22)
        if self.tooltip and not self.modal:
            w=410
            x=min(WIDTH-w-20,max(20,self.mouse[0]-w/2))
            y=max(110,min(HEIGHT-160,self.mouse[1]-106))
            self.panel(rect(x,y,w,102),BG,12)
            self.wrap(self.tooltip,x+13,y+11,w-26,13,TEXT,21)
        self.draw_modal()
        sw,sh=self.screen.get_size()
        self.scale=min(sw/WIDTH,sh/HEIGHT)
        target=(max(1,int(WIDTH*self.scale)),max(1,int(HEIGHT*self.scale)))
        self.offset=((sw-target[0])//2,(sh-target[1])//2)
        self.screen.fill(BG)
        self.screen.blit(pygame.transform.smoothscale(self.canvas,target),self.offset)
        pygame.display.flip()

    def mapped_mouse(self,pos):
        return ((pos[0]-self.offset[0])/self.scale,(pos[1]-self.offset[1])/self.scale)

    def click_at(self,position):
        for r,action,enabled in reversed(self.buttons):
            if enabled and r.collidepoint(position):
                action()
                return True
        return False

    def handle(self,event):
        if event.type==pygame.QUIT:
            self.running=False
        elif event.type==pygame.VIDEORESIZE and not self.fullscreen:
            self.screen=pygame.display.set_mode((max(840,event.w),max(540,event.h)),pygame.RESIZABLE)
        elif event.type==pygame.MOUSEMOTION:
            self.mouse=self.mapped_mouse(event.pos)
        elif event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
            self.mouse=self.mapped_mouse(event.pos)
            self.click_at(self.mouse)
            if not self.modal and (rect(380,233,330,309).collidepoint(self.mouse) or rect(276,614,388,40).collidepoint(self.mouse)):
                self.holding=True
                self.hold_time=0
                self.hold_accumulator=0
        elif event.type==pygame.MOUSEBUTTONUP and event.button==1:
            self.holding=False
        elif event.type==pygame.MOUSEWHEEL and not self.modal:
            self.scroll=max(0,min(self.max_scroll,self.scroll-event.y*66))
        elif event.type==pygame.WINDOWFOCUSLOST:
            self.holding=False
            self.safe_save()
        elif event.type==pygame.KEYUP and event.key==pygame.K_SPACE:
            self.holding=False
        elif event.type==pygame.KEYDOWN:
            if event.key==pygame.K_ESCAPE:
                if self.modal:self.modal=None
                elif self.fullscreen:self.toggle_fullscreen()
            elif event.key==pygame.K_F11:self.toggle_fullscreen()
            elif self.modal:
                if event.key==pygame.K_RETURN and self.modal[0] in ("welcome","offline"):
                    if self.modal[0]=="welcome":self.close_welcome()
                    else:self.modal=None
            elif event.key==pygame.K_SPACE:
                if not self.holding:self.manual_hit()
                self.holding=True
                self.hold_time=0
            elif pygame.K_1<=event.key<=pygame.K_5:
                index=event.key-pygame.K_1
                keys=self.game.available_abilities()
                if index<len(keys):self.cast(keys[index])
            elif event.key==pygame.K_a:self.toggle_progress()
            elif event.key in (pygame.K_h,pygame.K_p,pygame.K_f,pygame.K_r,pygame.K_q,pygame.K_m,pygame.K_s):
                self.set_tab({pygame.K_h:"Heroes",pygame.K_p:"Pets",pygame.K_f:"Forge",pygame.K_r:"Rebirth",pygame.K_q:"Quests",pygame.K_m:"Realms",pygame.K_s:"Settings"}[event.key])

    def toggle_fullscreen(self):
        self.fullscreen=not self.fullscreen
        self.screen=pygame.display.set_mode((0,0),pygame.FULLSCREEN) if self.fullscreen else pygame.display.set_mode((1260,810),pygame.RESIZABLE)

    def animate(self,dt):
        self.anim_time+=dt
        self.hit_flash=max(0,self.hit_flash-dt)
        if self.holding and not self.modal:
            self.hold_time+=dt
            if self.hold_time>.24:
                self.hold_accumulator+=dt
                while self.hold_accumulator>=1/7:
                    self.manual_hit()
                    self.hold_accumulator-=1/7
        for event in self.game.events:
            kind=event[0]
            if kind=="hit":
                self.hit_flash=.2
                if len(self.floaters)<22:
                    self.floaters.append(dict(text=num(event[1])+ ("!" if event[2] else ""),x=548+random.randint(-65,65),y=330,
                                              life=.85,color=GOLD if event[2] else TEXT,size=25 if event[2] else 19))
            if kind=="kill" and self.game.settings["particles"]:
                for i in range(7 if event[2] else 3):
                    if len(self.particles)>120:break
                    self.particles.append(dict(x=548,y=405,vx=random.uniform(-110,110),vy=random.uniform(-160,-40),life=.65,color=GOLD))
            if kind=="boss":self.toasts.append(("BOSS DEFEATED! Gems and crafting shards collected.",3.3))
            if kind=="hatch":self.set_tab("Pets")
            if kind in ("hit","buy","cast","hatch","boss","rebirth"):self.audio.play(kind,self.game.settings)
        self.game.events.clear()
        for message in self.game.messages:self.toasts.append((message,4.4))
        self.game.messages.clear()
        self.toasts=[(m,t-dt) for m,t in self.toasts if t-dt>0][-3:]
        for f in self.floaters:
            f["life"]-=dt
            f["y"]-=dt*72
        self.floaters=[f for f in self.floaters if f["life"]>0]
        for p in self.particles:
            p["life"]-=dt
            p["x"]+=p["vx"]*dt
            p["y"]+=p["vy"]*dt
            p["vy"]+=260*dt
        self.particles=[p for p in self.particles if p["life"]>0]
        self.audio.update(self.game.settings)

    def run(self,frames=None,screenshot=None):
        count=0
        try:
            self.draw()
            while self.running and (frames is None or count<frames):
                dt=min(.1,self.clock.tick(self.game.settings["fps"])/1000)
                for event in pygame.event.get():self.handle(event)
                if not self.modal:self.game.update(dt)
                self.animate(dt)
                self.draw()
                if not self.smoke and time.monotonic()-self.last_save>30:self.safe_save()
                count+=1
            if screenshot:
                Path(screenshot).parent.mkdir(parents=True,exist_ok=True)
                pygame.image.save(self.canvas,str(screenshot))
        finally:
            self.safe_save()
            pygame.quit()

def main():
    parser=argparse.ArgumentParser(description=TITLE+" - native offline Linux game")
    parser.add_argument("--smoke-test",action="store_true",help="Run a headless-safe UI test without modifying saves")
    parser.add_argument("--frames",type=int)
    parser.add_argument("--screenshot")
    parser.add_argument("--tab",choices=["Heroes","Pets","Forge","Rebirth","Quests","Realms","Settings"],default="Heroes")
    parser.add_argument("--save-dir",help="Use a separate save directory")
    parser.add_argument("--demo",action="store_true",help="Show a separate advanced preview (never overwrites real progress)")
    args=parser.parse_args()
    if args.smoke_test:
        os.environ.setdefault("SDL_VIDEODRIVER","dummy")
        os.environ.setdefault("SDL_AUDIODRIVER","dummy")
    game=None
    if args.smoke_test or args.demo:
        game=Game(seed=8)
        game.settings["tutorial"]=False
    if args.demo:
        game.coins=33000000
        game.gems=1350
        game.shards=125
        game.souls=80
        game.soul_power=115
        game.astrals=2
        game.heroes[:8]=[100,75,50,40,30,25,12,8]
        game.zone=game.max_zone=game.run_best=124
        game.stats["best_zone"]=124
        game.stats["rebirths"]=8
        game.stats["kills"]=6430
        game.stats["clicks"]=1282
        game.stats["bosses"]=119
        game.items.update(twin=4,spoon=2,tempo=3,crown=2)
        game.equipment.update(weapon="twin",charm="spoon",engine="tempo",relic="crown")
        game.pets=[dict(id=i+1,egg=0,rarity=rarity,stars=2,shiny=False) for i,rarity in enumerate([4,3,2])]
        game.next_pet_id=4
        game.auto_equip()
        game.new_enemy()
        game.invalidate()
    try:
        app=App(game=game,smoke=args.smoke_test or args.demo,save_dir=args.save_dir)
        app.set_tab(args.tab)
        app.run(frames=args.frames or (4 if args.smoke_test else None),screenshot=args.screenshot)
        if args.smoke_test:print("PASS: native application initialized, updated, rendered and closed cleanly.")
    except pygame.error as exc:
        print("The desktop window could not start:",exc,file=sys.stderr)
        print("Run this app from Chromebook's Linux Terminal with Linux desktop support enabled.",file=sys.stderr)
        return 1
    return 0

if __name__=="__main__":raise SystemExit(main())
