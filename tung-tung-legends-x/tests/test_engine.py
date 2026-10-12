import copy
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from content import ACHIEVEMENTS, HEROES
from engine import Game, CAP, num

class GameplayTests(unittest.TestCase):
    def test_first_kill_rewards_and_five_kills_unlock_next_stage(self):
        g=Game(seed=1)
        for i in range(5):g.damage(g.hp)
        self.assertEqual(g.zone,2)
        self.assertEqual(g.stats['kills'],5)
        self.assertEqual(g.coins,20)
        self.assertEqual(g.max_zone,2)

    def test_farm_mode_does_not_force_advancement(self):
        g=Game();g.auto_progress=False
        for i in range(10):g.damage(g.hp)
        self.assertEqual(g.zone,1)
        self.assertEqual(g.max_zone,2)
        self.assertTrue(g.move_zone(2))
        self.assertFalse(g.move_zone(3))

    def test_overflow_damage_is_bounded_and_can_clear_multiple_targets(self):
        g=Game();g.damage(CAP)
        self.assertEqual(g.stats['kills'],30)
        self.assertTrue(math.isfinite(g.hp))

    def test_clicks_are_recorded_and_damage_target(self):
        g=Game(seed=5);before=g.hp
        value=g.click()
        self.assertEqual(g.stats['clicks'],1)
        self.assertAlmostEqual(g.hp,before-value)

    def test_hero_purchase_deducts_currency_and_creates_idle_damage(self):
        g=Game();self.assertEqual(g.buy_hero(0),0)
        g.coins=15
        self.assertEqual(g.buy_hero(0),1)
        self.assertAlmostEqual(g.coins,0)
        before=g.hp;g.update(.5)
        self.assertLess(g.hp,before)

    def test_batch_purchase_has_correct_geometric_cost(self):
        g=Game();g.coins=1000
        price=g.hero_buy_cost(0,10)
        g.buy_hero(0,10)
        self.assertAlmostEqual(g.coins,1000-price,places=8)
        self.assertEqual(g.heroes[0],10)

    def test_partial_batch_cannot_overdraw(self):
        g=Game();g.coins=30
        self.assertEqual(g.buy_hero(0,100),1)
        self.assertGreaterEqual(g.coins,0)

    def test_hero_milestone_doubles_compatible_output(self):
        g=Game();g.heroes[0]=24;g.invalidate();a=g.combat_stats()['idle']
        g.heroes[0]=25;g.invalidate();b=g.combat_stats()['idle']
        self.assertAlmostEqual(b/a,50/24)

    def test_click_upgrade_increases_damage_and_deducts_coins(self):
        g=Game();g.coins=8;a=g.click_damage()
        self.assertEqual(g.buy_taps(),1)
        self.assertGreater(g.click_damage(),a)
        self.assertEqual(g.coins,0)

    def test_boss_reward_and_next_stage(self):
        g=Game();g.zone=g.max_zone=10;g.new_enemy()
        g.damage(g.hp)
        self.assertEqual(g.stats['bosses'],1)
        self.assertEqual(g.gems,68)
        self.assertEqual(g.shards,1)
        self.assertEqual(g.zone,11)

    def test_boss_timeout_returns_to_farm_and_pauses_advancement(self):
        g=Game();g.zone=g.max_zone=10;g.new_enemy();g.boss_time=.1
        g.update(.2)
        self.assertEqual(g.zone,9)
        self.assertFalse(g.auto_progress)
        self.assertEqual(g.failed_boss,10)

    def test_slam_has_real_cooldown(self):
        g=Game();self.assertTrue(g.cast('slam'))
        kills=g.stats['kills'];hp=g.hp
        self.assertFalse(g.cast('slam'))
        self.assertEqual((kills,hp),(g.stats['kills'],g.hp))
        for i in range(14):g.update(1)
        self.assertTrue(g.cast('slam'))

    def test_unequipped_item_does_not_grant_ability(self):
        g=Game();g.items['twin']=1
        self.assertNotIn('frenzy',g.available_abilities())
        self.assertFalse(g.cast('frenzy'))
        g.equip_item('twin')
        self.assertTrue(g.cast('frenzy'))
        self.assertAlmostEqual(g.click_damage(),g.combat_stats()['click']*3)

    def test_overdrive_buff_expires(self):
        g=Game();g.heroes[0]=10;g.items['tempo']=1;g.equip_item('tempo')
        base=g.idle_damage();g.cast('overdrive')
        self.assertAlmostEqual(g.idle_damage(),base*3)
        for i in range(20):g.update(1)
        self.assertAlmostEqual(g.idle_damage(),base)

    def test_hatch_debits_gems_and_equips_pet(self):
        g=Game(seed=10);p=g.hatch(0)
        self.assertEqual(g.gems,35)
        self.assertIn(p['id'],g.equipped_pets)
        self.assertGreater(g.combat_stats()['pet'],1)

    def test_locked_or_unaffordable_egg_has_no_side_effects(self):
        g=Game();before=g.gems
        self.assertIsNone(g.hatch(5));self.assertEqual(g.gems,before)
        g.gems=0;self.assertIsNone(g.hatch(0));self.assertEqual(g.stats['hatches'],0)

    def test_pity_guarantees_at_ten_forty_and_120(self):
        g=Game(seed=123);g.gems=100000
        for i in range(1,121):
            pet=g.hatch(0)
            if i%120==0:self.assertEqual(pet['rarity'],5)
            elif i%40==0:self.assertGreaterEqual(pet['rarity'],4)
            elif i%10==0:self.assertGreaterEqual(pet['rarity'],3)

    def test_pet_multipliers_are_a_product(self):
        g=Game();g.pets=[dict(id=i+1,egg=0,rarity=i,stars=1,shiny=False) for i in range(3)]
        g.auto_equip()
        expected=math.prod(g.pet_multiplier(p) for p in g.pets)
        self.assertAlmostEqual(g.combat_stats()['pet'],expected)

    def test_fusion_consumes_exactly_three_matching_pets(self):
        g=Game();g.pets=[dict(id=i+1,egg=0,rarity=0,stars=1,shiny=False) for i in range(4)]
        g.auto_equip();base=g.pet_multiplier(g.pets[0])
        self.assertTrue(g.fuse(1))
        self.assertEqual(len(g.pets),2)
        self.assertAlmostEqual(g.pet_multiplier(g.pets[0]),base*1.55)
        self.assertEqual(g.stats['fusions'],1)
        self.assertFalse(g.fuse(1))

    def test_recycle_removes_pet_and_grants_shards(self):
        g=Game();g.hatch();pid=g.pets[0]['id']
        self.assertTrue(g.recycle_pet(pid))
        self.assertGreater(g.shards,0)
        self.assertEqual(g.pets,[])
        self.assertEqual(g.equipped_pets,[])

    def test_item_unlock_uses_lifetime_best_and_upgrade_cost_is_real(self):
        g=Game();g.gems=1000
        self.assertFalse(g.buy_item('twin'))
        g.stats['best_zone']=20
        self.assertTrue(g.buy_item('twin'))
        self.assertEqual(g.gems,975)
        self.assertEqual(g.equipment['weapon'],'twin')
        self.assertFalse(g.upgrade_item('twin'))
        g.shards=3;self.assertTrue(g.upgrade_item('twin'))
        self.assertEqual(g.shards,0);self.assertEqual(g.items['twin'],2)

    def test_soul_research_spending_does_not_remove_earned_base_multiplier(self):
        g=Game();g.souls=g.soul_power=30
        before=g.combat_stats()['rebirth']
        self.assertTrue(g.buy_soul_upgrade('click'))
        self.assertEqual(g.combat_stats()['rebirth'],before)
        self.assertEqual(g.souls,28)

    def test_formation_research_equips_extra_pets(self):
        g=Game();g.souls=50
        for i in range(5):g.pets.append(dict(id=i+1,egg=0,rarity=0,stars=1,shiny=False))
        g.auto_equip();self.assertEqual(len(g.equipped_pets),3)
        g.buy_soul_upgrade('slots');self.assertEqual(len(g.equipped_pets),4)

    def test_rebirth_reset_and_retention(self):
        g=Game(seed=5);self.assertFalse(g.rebirth())
        g.hatch();g.items['twin']=3;g.equip_item('twin');g.upgrades['start']=1
        g.heroes[0]=20;g.tap_level=10;g.zone=g.max_zone=g.run_best=100
        pets=copy.deepcopy(g.pets);gems=g.gems
        self.assertTrue(g.rebirth())
        self.assertEqual(g.zone,1);self.assertEqual(sum(g.heroes),0);self.assertEqual(g.tap_level,0)
        self.assertEqual(g.pets,pets);self.assertEqual(g.items['twin'],3);self.assertEqual(g.gems,gems)
        self.assertGreater(g.soul_power,0);self.assertEqual(g.upgrades['start'],1)
        self.assertEqual(g.coins,60)

    def test_ascension_resets_souls_and_keeps_collection(self):
        g=Game();g.run_best=300;g.souls=g.soul_power=70;g.upgrades['slots']=2;g.items['twin']=4
        self.assertTrue(g.ascend())
        self.assertEqual(g.astrals,1);self.assertEqual(g.souls,0);self.assertEqual(g.soul_power,0)
        self.assertEqual(sum(g.upgrades.values()),0);self.assertEqual(g.items['twin'],4)
        self.assertEqual(g.combat_stats()['astral'],2)

    def test_achievements_are_one_time(self):
        g=Game();g.click();before=g.gems
        self.assertTrue(g.claim_achievement('first'))
        self.assertEqual(g.gems,before+10)
        self.assertFalse(g.claim_achievement('first'));self.assertEqual(g.gems,before+10)

    def test_contract_completion_refreshes_at_higher_tier(self):
        g=Game()
        for c in g.contracts:g.stats[c['metric']]=c['start']+c['goal']
        for i in range(3):self.assertTrue(g.claim_contract(i))
        self.assertEqual(g.contract_tier,1)
        self.assertTrue(all(not c['claimed'] for c in g.contracts))
        self.assertFalse(g.claim_contract(0))

    def test_offline_caps_time_and_does_not_advance_or_kill_bosses(self):
        g=Game();g.heroes[0]=20;g.zone=g.max_zone=10;g.new_enemy();g.invalidate()
        g.offline(100000)
        self.assertEqual(g.offline_report['seconds'],28800)
        self.assertGreater(g.coins,0);self.assertEqual(g.zone,10);self.assertEqual(g.stats['bosses'],0)

    def test_offline_without_idle_power_is_not_free_money(self):
        g=Game();g.offline(4000)
        self.assertEqual(g.coins,0)

    def test_save_roundtrip_preserves_inventory_cooldown_and_progress(self):
        with tempfile.TemporaryDirectory() as directory:
            g=Game();g.hatch();g.heroes[2]=30;g.coins=12345;g.cast('slam')
            g.save(directory);other=Game.load(directory,apply_offline=False)
            self.assertEqual(g.serialize()['pets'],other.serialize()['pets'])
            self.assertEqual(g.coins,other.coins);self.assertEqual(g.heroes,other.heroes)
            self.assertEqual(g.cooldowns,other.cooldowns)

    def test_corrupt_primary_recovers_backup_and_future_save_keeps_good_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            g=Game();g.coins=10;g.save(directory);g.coins=20;g.save(directory)
            path=Path(directory)/'save.json';path.write_text('broken')
            recovered=Game.load(directory,apply_offline=False)
            self.assertEqual(recovered.coins,10)
            recovered.save(directory)
            self.assertTrue(list(Path(directory).glob('save.corrupt.*.json')))
            backup=json.loads((Path(directory)/'save.backup.json').read_text())
            self.assertEqual(backup['data']['coins'],10)

    def test_save_sanitizes_invalid_numbers_and_duplicate_pet_ids(self):
        g=Game();data=g.serialize();data['coins']=float('nan');data['heroes']=[-2,999999]
        data['pets']=[dict(id=1,egg=90,rarity=40,stars=50,shiny=False)]*2
        other=Game.from_data(data)
        self.assertEqual(other.coins,0);self.assertEqual(other.heroes[:2],[0,3000])
        self.assertEqual(len(other.pets),1);self.assertEqual(other.pets[0]['stars'],8)

    def test_high_end_state_stays_finite_and_json_serializable(self):
        g=Game();g.zone=g.max_zone=g.run_best=10000;g.heroes=[3000]*len(HEROES)
        g.astrals=10000;g.soul_power=1000000;g.invalidate();g.new_enemy()
        for i in range(10):g.click();g.update(1)
        json.dumps(g.serialize(),allow_nan=False)
        self.assertTrue(all(math.isfinite(v) for v in g.combat_stats().values()))
        self.assertEqual(Game.from_data(g.serialize()).zone,g.zone)

    def test_30_and_60_fps_idle_damage_agree(self):
        outcomes=[]
        for fps in (30,60):
            g=Game();g.heroes[0]=1;g.invalidate()
            for i in range(fps):g.update(1/fps)
            outcomes.append(g.hp)
        self.assertAlmostEqual(*outcomes,places=8)

    def test_number_formatting_is_readable_at_extreme_values(self):
        self.assertEqual(num(1000000),'1M')
        self.assertIn('e+',num(1e100))
        self.assertEqual(num(float('inf')),'MAX')

if __name__=='__main__':unittest.main(verbosity=2)
