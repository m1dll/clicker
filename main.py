import random
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.core.window import Window
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.properties import NumericProperty, StringProperty
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.core.audio import SoundLoader
from kivy import platform

if platform != 'android':
    Window.size = (450, 780)

# ===== ЕКРАН ГОЛОВНОГО МЕНЮ =====
class MenuScreen(Screen):
    def go_game(self):
        App.get_running_app().change_screen("game", "left")

    def go_settings(self):
        App.get_running_app().change_screen("settings", "left")

    def exit_app(self):
        App.get_running_app().stop()

# ===== ЕКРАН ГРИ =====
class GameScreen(Screen):
    score = NumericProperty(0)
    coins = NumericProperty(0)
    level = NumericProperty(1)
    ach_text = StringProperty("Target: Get 50 coins")
    
    back_sound = SoundLoader.load('assets/audios/black_swan_part.mp3')
    back_sound.loop = True
    level_complete_sound = SoundLoader.load('assets/audios/level_complete.ogg')

    def on_pre_enter(self, *args):
        app = App.get_running_app()
        self.score = 0
        self.coins = 0
        app.LEVEL = 0
        app.total_fishes_defeated = 0
        app.total_bosses_defeated = 0
        app.click_power = 1
        app.auto_click_speed = 0
        app.crit_chance = 10
        app.damage_multiplier = 1.0
        self.level = 1
        self.ids.level_complete.opacity = 0
        self.ids.fish.fish_index = 0
        self.update_achievement_text()
        return super().on_pre_enter(*args)

    def on_enter(self, *args):
        self.start_game()
        if self.back_sound:
            self.back_sound.volume = 0.5
            self.back_sound.play()
        
        Clock.schedule_interval(self.passive_damage, 1.0)
        Clock.schedule_interval(self.spawn_golden_fish, 45.0)
        return super().on_enter(*args)

    def on_leave(self, *args):
        if self.back_sound:
            self.back_sound.stop()
        Clock.unschedule(self.passive_damage)
        Clock.unschedule(self.spawn_golden_fish)
        Clock.unschedule(self.next_level)
        Clock.unschedule(self.game_complete)
        return super().on_leave(*args)

    def start_game(self):
        self.ids.fish.new_fish()

    # --- СИСТЕМА ДОСЯГНЕНЬ ---
    def check_achievements(self):
        app = App.get_running_app()
        if app.damage_multiplier == 1.0 and self.coins >= 50:
            app.damage_multiplier = 1.2
            self.ids.fish.spawn_damage_text(225, 600, "ACHIEVEMENT! +20% DMG", color=(1, 0.5, 0, 1))
        elif app.damage_multiplier == 1.2 and app.total_bosses_defeated >= 2:
            app.damage_multiplier = 1.5
            self.ids.fish.spawn_damage_text(225, 600, "ACHIEVEMENT! +50% DMG", color=(1, 0.5, 0, 1))
        
        self.update_achievement_text()

    def update_achievement_text(self):
        app = App.get_running_app()
        if app.damage_multiplier == 1.0:
            self.ach_text = "Target: Get 50 coins (+20% Dmg)"
        elif app.damage_multiplier == 1.2:
            self.ach_text = "Target: Defeat 2 Bosses (+50% Dmg)"
        else:
            self.ach_text = "All Achievements Unlocked! Max Power!"

    # --- МАГАЗИН ЗА МОНЕТИ ---
    def buy_click(self):
        app = App.get_running_app()
        cost = app.click_power * 15
        if self.coins >= cost:
            self.coins -= cost
            app.click_power += 1
            self.check_achievements()

    def buy_autoclick(self):
        app = App.get_running_app()
        cost = (app.auto_click_speed + 1) * 30
        if self.coins >= cost:
            self.coins -= cost
            app.auto_click_speed += 1
            self.check_achievements()

    def buy_crit(self):
        app = App.get_running_app()
        cost = int((app.crit_chance / 10) * 40)
        if app.crit_chance < 50 and self.coins >= cost:
            self.coins -= cost
            app.crit_chance += 5

    # --- СПАВН ЗОЛОТОЇ РИБКИ ---
    def spawn_golden_fish(self, dt):
        if self.ids.get('game_layout'):
            gold_fish = GoldenFish()
            self.ids.game_layout.add_widget(gold_fish)
            gold_fish.swim_across()

    def passive_damage(self, dt):
        app = App.get_running_app()
        fish = self.ids.fish
        
        if app.auto_click_speed > 0 and fish.opacity > 0 and not fish.is_moving and not fish.is_defeated:
            dmg = int(app.auto_click_speed * app.damage_multiplier)
            fish.hp_current -= dmg
            self.ids.hp_bar.value = max(0, fish.hp_current)
            
            self.score += dmg
            self.coins += dmg
            
            fish.spawn_damage_text(fish.center_x, fish.center_y, f"+{dmg}", color=(0.2, 0.6, 1, 1))
            self.check_achievements()

            if fish.hp_current <= 0:
                fish.defeated_logic()
                fish.next_fish_logic()

    def level_complete(self, *args):
        app = App.get_running_app()
        self.ids.level_complete.opacity = 1

        if app.LEVEL + 1 < len(app.LEVELS):
            Clock.schedule_once(self.next_level, 2)
        else:
            Clock.schedule_once(self.game_complete, 2)

        if self.level_complete_sound:
            self.level_complete_sound.play()

    def next_level(self, *args):
        app = App.get_running_app()
        app.LEVEL += 1
        self.level = app.LEVEL + 1
        self.ids.level_complete.opacity = 0
        self.ids.fish.fish_index = 0
        self.start_game()

    def game_complete(self, *args):
        self.ids.level_complete.text = "YOU WIN ALL LEVELS!"
        self.ids.level_complete.opacity = 1
        Clock.schedule_once(self.go_menu, 2)

    def go_menu(self, *args):
        App.get_running_app().change_screen("menu", "right")

# ===== ЕКРАН НАЛАШТУВАНЬ =====
class SettingsScreen(Screen):
    def go_menu(self):
        App.get_running_app().change_screen("menu", "right")

# ===== КЛАС ЗОЛОТОЇ РИБКИ =====
class GoldenFish(Image):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source = 'assets/images/fish1.png'
        self.color = (1, 0.85, 0, 1)
        self.size_hint = (None, None)
        self.size = (80, 80)
        self.x = random.choice([-100, 550])
        self.y = random.randint(300, 500)

    def swim_across(self):
        target_x = 550 if self.x < 0 else -100
        anim = Animation(x=target_x, y=self.y - random.randint(50, 150), duration=3.0)
        anim.bind(on_complete=lambda *args: Clock.schedule_once(lambda dt: self.safe_remove()))
        anim.start(self)

    def safe_remove(self):
        if self.parent:
            self.parent.remove_widget(self)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            app = App.get_running_app()
            game = app.sm.get_screen("game")
            
            bonus = app.click_power * 15
            game.coins += bonus
            
            game.ids.fish.spawn_damage_text(touch.x, touch.y, f"GOLDEN! +{bonus} 🪙", color=(1, 0.85, 0, 1))
            game.check_achievements()
            
            Clock.schedule_once(lambda dt: self.safe_remove())
            return True
        return super().on_touch_down(touch)

# ===== КЛАС РИБИ =====
class Fish(Image):
    fish_current = None
    fish_index = 0
    hp_current = None
    is_moving = False
    is_pulsing = False
    is_defeated = False
    angle = NumericProperty(0)
    base_size = (200, 200)

    click_music = SoundLoader.load('assets/audios/bubble01.mp3')
    defeate_music = SoundLoader.load('assets/audios/fish_def.ogg')

    def on_kv_post(self, base_widget):
        if self.size != [100, 100]:
            self.base_size = list(self.size)
        else:
            self.size = self.base_size
        return super().on_kv_post(base_widget)

    def get_game(self):
        app = App.get_running_app()
        return app.sm.get_screen("game")

    def new_fish(self, *args):
        Animation.cancel_all(self)
        app = App.get_running_app()
        game = self.get_game()

        self.fish_current = app.LEVELS[app.LEVEL][self.fish_index]
        self.source = app.FISHES[self.fish_current]['source']
        
        base_hp = app.FISHES[self.fish_current]['hp']
        
        # --- НОВА ЕКСПОНЕНЦІАЛЬНА ФОРМУЛА МНОЖЕННЯ ЗДОРОВ'Я ---
        # Кожен переможений смайлик множить HP наступного на 1.12 (зростання на 12% від ПОТОЧНОГО значення)
        # Додатково плавно збільшуємо складність залежно від номера поточного рівня (app.LEVEL)
        level_scale = 1.0 + (app.LEVEL * 0.05)
        hp_multiplier = (1.12 ** app.total_fishes_defeated) * level_scale
        
        # Для босів робимо додаткове множення, щоб вони виділялися
        if self.fish_current == 'boss':
            self.hp_current = int(base_hp * hp_multiplier * 2.0)
            self.base_size = (250, 250)
        elif self.fish_current == 'cloun':
            self.hp_current = int(base_hp * hp_multiplier * 3.5) # Клоун у 3.5 раза товщий!
            self.base_size = (280, 280)
        else:
            self.hp_current = int(base_hp * hp_multiplier)
            self.base_size = (200, 200)
        
        game.ids.hp_bar.max = self.hp_current
        game.ids.hp_bar.value = self.hp_current
        game.ids.hp_bar.opacity = 1

        self.size = list(self.base_size)
        self.opacity = 1
        self.angle = 0
        self.is_moving = True
        self.is_pulsing = False
        self.is_defeated = False

        self.x = -self.width
        self.y = game.height / 2 - self.height / 2 + 30
        
        anim_enter = Animation(
            x=game.width / 2 - self.width / 2,
            y=game.height / 2 - self.height / 2 + 30,
            duration=1.2,
            t='out_back'
        )
        
        def arrival(*args):
            self.is_moving = False
        
        anim_enter.bind(on_complete=arrival)
        anim_enter.start(self)

    def spawn_damage_text(self, x, y, text, color=(1, 0.9, 0, 1), font_size="24sp"):
        float_layout = self.parent
        if not float_layout:
            return
            
        lbl = Label(
            text=text,
            font_size=font_size,
            font_name='assets/fonts/lemon-regular.ttf',
            color=color,
            size_hint=(None, None),
            size=("50dp", "30dp"),
            x=x - 25,
            y=y
        )
        float_layout.add_widget(lbl)
        
        anim = Animation(y=y + 110, opacity=0, duration=0.7, t='out_quad')
        
        def remove_label(*args):
            Clock.schedule_once(lambda dt: float_layout.remove_widget(lbl) if float_layout else None)
            
        anim.bind(on_complete=remove_label)
        anim.start(lbl)

    def defeated_logic(self):
        if self.is_defeated:
            return
        self.is_defeated = True
        
        Animation.cancel_all(self)
        game = self.get_game()
        app = App.get_running_app()
        game.ids.hp_bar.opacity = 0

        app.total_fishes_defeated += 1

        if self.fish_current == 'cloun':
            app.total_bosses_defeated += 1
            game.coins += 100
            self.spawn_damage_text(self.center_x, self.center_y + 40, "+100 COINS CLOUN BONUS!", color=(1, 0.2, 0.2, 1))
        elif self.fish_current == 'boss':
            app.total_bosses_defeated += 1
            game.coins += 35
            self.spawn_damage_text(self.center_x, self.center_y + 40, "+35 COINS BONUS!", color=(0, 1, 0, 1))

        w, h = self.base_size
        cx, cy = self.center
        
        anim = Animation(
            angle=360,
            size=(w * 1.8, h * 1.8),
            opacity=0,
            center=(cx, cy),
            duration=0.5,
            t='out_quad'
        )

        def hide(*args):
            self.opacity = 0
            self.angle = 0
            self.size = list(self.base_size)

        anim.bind(on_complete=hide)
        anim.start(self)
        if self.defeate_music:
            self.defeate_music.play()
        game.check_achievements()

    def next_fish_logic(self):
        if len(App.get_running_app().LEVELS[App.get_running_app().LEVEL]) > self.fish_index + 1:
            self.fish_index += 1
            Clock.schedule_once(self.new_fish, 1.2)
        else:
            Clock.schedule_once(self.get_game().level_complete, 1.2)
            self.fish_index = 0

    def pulse(self): 
        if self.is_pulsing or self.is_defeated or self.is_moving:
            return
        self.is_pulsing = True
        
        w, h = self.base_size
        cx, cy = self.center
        
        anim_1 = Animation(size=(w * 1.2, h * 1.2), center=(cx, cy), duration=0.05, t='out_quad')
        anim_2 = Animation(size=(w, h), center=(cx, cy), duration=0.05, t='out_quad')
        
        def finish(*args):
            self.is_pulsing = False
            if not self.is_defeated:
                self.size = list(self.base_size)
        
        anim_click = anim_1 + anim_2
        anim_click.bind(on_complete=finish)
        anim_click.start(self)

    def on_touch_down(self, touch):
        game = self.get_game()
        app = App.get_running_app()
        
        if (
            not self.collide_point(*touch.pos)
            or self.opacity == 0
            or self.is_moving
            or self.is_defeated
        ):
            return True
        
        if self.click_music:
            self.click_music.play()
        self.pulse()

        is_crit = random.randint(1, 100) <= app.crit_chance
        base_dmg = int(app.click_power * app.damage_multiplier)
        
        if is_crit:
            final_dmg = base_dmg * 4
            self.spawn_damage_text(touch.x, touch.y, f"CRIT! +{final_dmg}", color=(0.7, 0.2, 1, 1), font_size="30sp")
        else:
            final_dmg = base_dmg
            self.spawn_damage_text(touch.x, touch.y, f"+{final_dmg}")

        self.hp_current -= final_dmg
        game.ids.hp_bar.value = max(0, self.hp_current)
        
        game.score += final_dmg
        game.coins += final_dmg
        game.check_achievements()

        if self.hp_current > 0:
            return super().on_touch_down(touch)

        self.defeated_logic()
        self.next_fish_logic()
        return super().on_touch_down(touch)

# ===== ГОЛОВНИЙ ДОДАТОК =====
class ClickerApp(App):
    LEVEL = 0
    click_power = NumericProperty(1)
    auto_click_speed = NumericProperty(0)
    crit_chance = NumericProperty(10)
    damage_multiplier = 1.0
    
    total_fishes_defeated = 0 
    total_bosses_defeated = 0
    
    # Базові значення HP (тепер вони множаться по експоненті)
    FISHES = {
        'fish1': {'source': 'assets/images/fish1.png', 'hp': 15},
        'fish2': {'source': 'assets/images/fish2.png', 'hp': 30},
        'boss':  {'source': 'assets/images/boss.png', 'hp': 60},
        'cloun': {'source': 'assets/images/cloun.png', 'hp': 120}
    }
    
    LEVELS = []

    def build(self):
        # Генеруємо 30 рівнів. Кожен 7-й — з Клоуном.
        for lvl_num in range(1, 31):
            if lvl_num % 7 == 0:
                self.LEVELS.append(['fish1', 'fish2', 'fish2', 'cloun'])
            else:
                self.LEVELS.append(['fish1', 'fish1', 'fish2', 'boss'])

        self.sm = ScreenManager()
        self.sm.add_widget(MenuScreen(name="menu"))
        self.sm.add_widget(GameScreen(name="game"))
        self.sm.add_widget(SettingsScreen(name="settings"))
        return self.sm

    def change_screen(self, screen_name, direction):
        self.sm.transition = SlideTransition(direction=direction, duration=0.3)
        self.sm.current = screen_name

if __name__ == '__main__':
    ClickerApp().run()
