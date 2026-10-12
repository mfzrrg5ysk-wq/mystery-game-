"""Real SDL input/render integration checks, with no browser or window server."""
import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pygame
from engine import Game
from game import App

class DesktopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g=Game(seed=9);cls.g.settings['tutorial']=False
        cls.app=App(cls.g,smoke=True)

    @classmethod
    def tearDownClass(cls):pygame.quit()

    def test_all_tabs_render_top_and_bottom(self):
        for tab in ['Heroes','Pets','Forge','Rebirth','Quests','Realms','Settings']:
            self.app.set_tab(tab);self.app.draw()
            self.app.scroll=self.app.max_scroll;self.app.draw()
            self.assertTrue(self.app.buttons)
            self.assertEqual(self.app.canvas.get_clip(),pygame.Rect(0,0,1400,900))

    def test_click_input_actually_farms(self):
        self.app.set_tab('Heroes');self.app.modal=None;self.app.draw()
        before=self.g.stats['clicks']
        self.assertTrue(self.app.click_at((400,635)))
        self.assertEqual(self.g.stats['clicks'],before+1)

    def test_keyboard_tabs_and_ability(self):
        self.app.modal=None
        self.app.handle(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_p))
        self.assertEqual(self.app.tab,'Pets')
        self.g.cooldowns['slam']=0
        self.app.handle(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_1))
        self.assertGreater(self.g.cooldowns['slam'],0)

    def test_scrolled_cards_cannot_intercept_header_controls(self):
        self.app.set_tab('Heroes');self.app.draw();self.app.scroll=800;self.app.draw()
        for r,action,enabled in self.app.buttons:
            if r.x>=1190 and r.y>=245:self.assertLessEqual(r.bottom,849)
        self.app.click_at((1040,228))
        self.assertEqual(self.app.buy_amount,10)

    def test_hatch_button_gives_visible_equipped_pet(self):
        self.g.gems=100;self.app.set_tab('Pets');self.app.draw()
        before=len(self.g.pets)
        self.app.click_at((1240,374))
        self.assertEqual(len(self.g.pets),before+1)
        self.app.animate(.02);self.app.draw()

    def test_confirmation_dialog_blocks_farming(self):
        self.app.modal=('rebirth',None);self.app.draw()
        before=self.g.stats['clicks'];self.app.click_at((350,635))
        self.assertEqual(before,self.g.stats['clicks'])
        self.app.click_at((510,653));self.assertIsNone(self.app.modal)

    def test_welcome_has_real_start_button(self):
        self.app.modal=('welcome',None);self.app.draw()
        self.app.click_at((600,659))
        self.assertIsNone(self.app.modal)
        self.assertFalse(self.g.settings['tutorial'])

    def test_resize_maps_input_correctly(self):
        self.app.handle(pygame.event.Event(pygame.VIDEORESIZE,w=960,h=640));self.app.draw()
        point=(400*self.app.scale+self.app.offset[0],635*self.app.scale+self.app.offset[1])
        logical=self.app.mapped_mouse(point)
        self.assertAlmostEqual(logical[0],400);self.assertAlmostEqual(logical[1],635)

if __name__=='__main__':unittest.main(verbosity=2)
