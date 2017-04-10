#-*- coding: utf-8 -*-
# Anne LoVerso
# Python Set Game
import pygame
import math
from pygame.locals import *
import random
import time
from abc import ABCMeta, abstractmethod
import planes
import planes.gui
import os,yaml
from bidi.algorithm import get_display
from class_utils import Button
from class_utils import ScreenText
import gettext

####################
# DEFINE CONSTANTS #
####################

WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768

CARD_WIDTH = 200
CARD_HEIGHT = 100

top_margin = 50
left_margin = 50
space_horiz = ((3*WINDOW_WIDTH/4)-2*left_margin-3*CARD_WIDTH)/2

BLACK = (0, 0, 0)
GREEN = (10, 200, 10)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
RED = (255,0,0)

MODE_HOME = 0
MODE_GAME = 1

NOTIME = 0
EASY = 4
MEDIUM = 2
HARD = 1

NUM_HINTS = 100
TIME_DEDUC = 3000

ROOT = os.path.dirname(os.path.realpath(__file__))
IMG = os.path.join(ROOT,"img")

FONT_BIG = pygame.font.Font ("arial.ttf", 40)
FONT_SMALL = pygame.font.Font ("arial.ttf", 20)

colors = ['green', 'red', 'purple']
shapes = ['oval', 'diamond', 'squiggle']
numbers = [1,2,3]
shades = ['filled','shaded', 'empty']

'''
Given three cards, checks whether they form a Set
Args: card1, card2, card3 - objects of type Card
Returns: True if cards form a Set, False otherwise
'''
def check_set (card1, card2, card3):
    color_check = all_same_or_all_diff (card1.color, card2.color, card3.color)
    shape_check = all_same_or_all_diff (card1.shape, card2.shape, card3.shape)
    num_check = all_same_or_all_diff (card1.number, card2.number, card3.number)
    shade_check = all_same_or_all_diff (card1.shade, card2.shade, card3.shade)
    return color_check and shape_check and num_check and shade_check

'''
Given three attributes (one from each of three cards), checks whether the
they are either all the same, or all different
Functions as a helper method to check_set
Args: attr1, attr2, attr3 - attributes of a card (color, shape, number, shade)
Returns: True if all three attributes are equal OR none of them are equal, False otherwise
'''
def all_same_or_all_diff (attr1, attr2, attr3):
    if attr1 == attr2 and attr2 == attr3:
        return True
    elif (attr1 != attr2) and (attr2 != attr3) and (attr3 != attr1):
        return True
    else:
        return False

'''
Helper function, takes a game time in seconds and formats it into a human-readable string
Returns string in format, for example: "1m 20s"
'''
def format_secs (secs):
    minutes = secs / 60
    seconds = secs % 60
    return str (minutes) + "m " + str (seconds) + "s"

'''
a Card has attributes of color, shape, number, and shade
'''
class Card (planes.Plane):
    def __init__ (self, name, color, shape, number, shade):
        planes.Plane.__init__ (self, name, pygame.Rect(0,0,CARD_WIDTH,CARD_HEIGHT), False, False)
        self.color = color
        self.shape = shape
        self.number = number
        self.shade = shade
        self.been_clicked = False

    def __eq__ (self, other):
        if isinstance(other,Card):
            return  self.color == other.color and \
                    self.shape == other.shape and \
                    self.number == other.number and \
                    self.shade == other.shade
        else:
            return False

    def __ne__ (self, other):
        return not self.__eq__(other)

    def clicked (self, button_name):
        self.been_clicked = not self.been_clicked

    def update (self):
        pass

'''
The TimeBox is a box that serves as a timer, slowly moving down and filling the screen
'''
class TimeBox (planes.Plane):
    def __init__ (self, name, rect, speed):
        planes.Plane.__init__ (self, name, rect, False, False)
        # time is time for box to move to bottom of screen in seconds
        self.speed = speed
        self.image.fill ((100,100,100))
        self.counter = 1 # need this because it can't move by fractional pixels

    def update (self):
        self.counter += 1
        if self.speed != 0 and self.rect.y < 0 and (self.counter % self.speed) == 0:
            self.rect.y += 1

##################
# BUTTON CLASSES #
##################

# GAME BUTTON
### When clicked, adds three new cards if no Set on the board
class AddThreeCardsButton (Button):
	def __init__(self, name, rect, callback, model):
		Button.__init__ (self, name, rect, callback, model)
		self.image = pygame.image.load (IMG+"/plus3_icon.png")

	def clicked (self, button_name):
		if self.model.check_in_play():
			if not self.model.check_if_any_sets:
				self.model.add_new_cards (3)

# GAME BUTTON
### When clicked, gives a hint
### If Set on the board: highlights the next card in the Set
### If no Set on board: adds three new cards
### Ignores cards already clicked, so user should not click when cards are highlighted
class HintButton (Button):
	def __init__(self, name, rect, callback, model):
		Button.__init__ (self, name, rect, callback, model)
		self.image = pygame.image.load (IMG+"/hint_icon.png")

	def clicked (self, button_name):
		if self.model.check_in_play():
			if (self.model.hints_left > 0):
				self.model.hints_left -= 1
				for card1 in self.model.in_play_cards:
						for card2 in self.model.in_play_cards:
							for card3 in self.model.in_play_cards:
								if card1 != card2 and card2 != card3 and card1 != card3:
									if check_set (card1, card2, card3):
										if not card1.been_clicked:
											card1.been_clicked = True
											return
										elif not card2.been_clicked:
											card2.been_clicked = True
											return
										else:
											card3.been_clicked = True
											return
				self.model.add_new_cards (3)

# GAME BUTTON
### When clicked, pauses time in game
class PauseButton (Button):
	def __init__(self, name, rect, callback, model):
		Button.__init__ (self, name, rect, callback, model)
		self.image = pygame.image.load (IMG+"/pause_icon.png")

	def clicked (self, button_name):
		if not (self.model.check_if_lost() or self.model.check_if_won()):
			if self.model.paused_time_at != 0: # game is already paused, act as play button
				self.model.pause_time += pygame.time.get_ticks() - self.model.paused_time_at
				self.model.paused_time_at = 0
			else:
				self.model.paused_time_at = pygame.time.get_ticks()

# GAME BUTTON (pause screen)
### When clicked, return to Homescreen
class BackButton (Button):
	def __init__(self, name, rect, callback, model):
		Button.__init__ (self, name, rect, callback, model)
		self.image = pygame.image.load (IMG+"/back_icon.png")

	def clicked (self, button_name):
		self.model.model.game = None
		self.model.model.mode = MODE_HOME

# GAME BUTTON (pause screen)
### When clicked, resume game time
class PlayButton (Button):
	def __init__(self, name, rect, callback, model):
		Button.__init__ (self, name, rect, callback, model)
		self.image = pygame.image.load (IMG+"/start_icon.png")

	def clicked (self, button_name):
		if self.model.check_if_won() or self.model.check_if_lost(): # if game over act as restart button
			self.model.model.game = None
			self.model.model.game = Game (self.model.model.game_select, self.model.model)
		else:
			self.model.pause_time += pygame.time.get_ticks() - self.model.paused_time_at
			self.model.paused_time_at = 0

# GAME BUTTON (pause screen)
### Restarts the game by creating a new Game object
class RestartButton (Button):
	def __init__(self, name, rect, callback, model):
		Button.__init__ (self, name, rect, callback, model)
		self.image = pygame.image.load (IMG+"/restart_icon.png")

	def clicked (self, button_name):
		self.model.model.game = None
		self.model.model.game = Game (self.model.model.game_select, self.model.model)

# HOME BUTTON
### Starts a new game by creating a new Game object
class StartButton (Button):
	def __init__(self, name, rect, callback, model):
		Button.__init__ (self, name, rect, callback, model)
		self.image = pygame.image.load (IMG+"/start_icon.png")
		self.clickbox = False   # all home screen buttons have a clickbox option
								# which shows up as blakc box to indicate selection

	def clicked (self, button_name):
		self.model.mode = MODE_GAME
		self.model.game = Game (self.model.game_select, self.model)

# HOME BUTTON
### Sets game_select mode to no timer
class NoTimeButton (Button):
	def __init__(self, name, rect, callback, model):
		Button.__init__ (self, name, rect, callback, model)
		self.image = pygame.image.load (IMG+"/notime_icon.png")
		self.clickbox = True

	def clicked (self, button_name):
		self.model.game_select = NOTIME
		for button in self.model.homebuttons:
			button.clickbox = False
		self.clickbox = True

# HOME BUTTON
### Sets game_select mode to easy
class EasyButton (Button):
	def __init__(self, name, rect, callback, model):
		Button.__init__ (self, name, rect, callback, model)
		self.image = pygame.image.load (IMG+"/easy_icon.png")
		self.clickbox = False

	def clicked (self, button_name):
		self.model.game_select = EASY
		for button in self.model.homebuttons:
			button.clickbox = False
		self.clickbox = True

# HOME BUTTON
### Sets game_select mode to medium
class MedButton (Button):
	def __init__(self, name, rect, callback, model):
		Button.__init__ (self, name, rect, callback, model)
		self.image = pygame.image.load (IMG+"/med_icon.png")
		self.clickbox = False

	def clicked (self, button_name):
		self.model.game_select = MEDIUM
		for button in self.model.homebuttons:
			button.clickbox = False
		self.clickbox = True

# HOME BUTTON
### Sets game_select mode to hard
class HardButton (Button):
	def __init__(self, name, rect, callback, model):
		Button.__init__ (self, name, rect, callback, model)
		self.image = pygame.image.load (IMG+"/hard_icon.png")
		self.clickbox = False

	def clicked (self, button_name):
		self.model.game_select = HARD
		for button in self.model.homebuttons:
			button.clickbox = False
		self.clickbox = True

# HOME BUTTON
### When clicked, display game statistics
### Number of games, best time, average time
class StatsButton (Button):
	def __init__(self, name, rect, callback, model):
		Button.__init__ (self, name, rect, callback, model)
		self.image = pygame.image.load (IMG+"/stats_icon.png")
		self.clickbox = False

	def clicked (self, button_name):
		if len (self.model.show_stats) > 0: # we are already showing stats, unshow
			self.model.show_stats = []
		else:
			num_games = str (len (self.model.times))
			best_time = "No Time Data Yet"
			avg_time = "No Time Data Yet"
			if len(self.model.times) > 0:
				best_time = format_secs (min (self.model.times))
				avg_time = format_secs (sum (self.model.times) / len (self.model.times))
			
			message_box = planes.Plane ('message_box',
					pygame.Rect (left_margin, top_margin, 13*WINDOW_WIDTH/16, (WINDOW_HEIGHT-300)))
			message_box.image.fill ((0,0,0))

			win_stats = "Game Stats \n" + "Number of Games: " + num_games + "\nBest time: " + best_time + "\nAverage time: " + avg_time

			message_texts = []
			lines = win_stats.split ("\n")
			box_width = 13*WINDOW_WIDTH/16
			for line in lines:
				message_texts.append (ScreenText (line, line, 
									  pygame.Rect(left_margin, top_margin + 60*(lines.index(line)+1) ,box_width, 45), FONT_BIG))

			#message_text.background_color = (255,0,0) #fixthis not transparent
			self.model.show_stats.append (message_box)
			self.model.show_stats += message_texts
  

'''
A Game is a single game that ends when won, lost or cancelled
'''      
class Game():
    def __init__(self, game_select, model,duration):
        ########################
        # GAME SCREEN ELEMENTS #
        ########################
        self.deck = []

        self.model = model
        self.game_select = game_select

        self.pause_time = 0
        self.paused_time_at = 0

        self.start_time = pygame.time.get_ticks()
        self.end_time = 0 # time game ended at

        self.duration = duration

        #make 81 unique cards, add to deck
        for color in colors:
            for shape in shapes:
                for number in numbers:
                    for shade in shades:
                        card_to_add = Card(color + shape + shade + str (number), color, shape, number, shade)
                        self.deck.append (card_to_add)
                        card_to_add.image = pygame.image.load (IMG+"/" + card_to_add.name + ".png")

        self.actors = []
        self.in_play_cards = []
        self.clicked_cards = []
        self.out_of_play_cards = []

        self.sets_found = 0
        self.sets_wrong = 0 # should we take off points for these?
        self.hints_left = NUM_HINTS

        # tells if we have already added the game time to the times []
        # prevents from adding the time on every update loop
        self.added_time = False

        #### Elements of a game ####
        self.sets_found_label = ScreenText ("sets_found_label","Sets: " + str (self.sets_found),pygame.Rect (3*WINDOW_WIDTH/4, 290, WINDOW_WIDTH/4, 50), FONT_BIG)
        
        self.time_label = ScreenText ("time_label", "Time: " + format_secs (self.duration / 1000), pygame.Rect (3*WINDOW_WIDTH/4, 220, WINDOW_WIDTH/4, 100), FONT_BIG)
        
        self.left_in_deck_label = ScreenText("left_in_deck_label", "Deck: " + str (len (self.deck) - (len (self.in_play_cards) + len (self.out_of_play_cards))), pygame.Rect (3*WINDOW_WIDTH/4, 505, WINDOW_WIDTH/4, 25), FONT_SMALL) 
        
        self.add3_button = AddThreeCardsButton ("add_three_cards_button", pygame.Rect (3*WINDOW_WIDTH/4 + (WINDOW_WIDTH/4 - 200)/2, 360, 100, 100), AddThreeCardsButton.clicked, self)
        
        self.hint_button = HintButton ("hint_button", pygame.Rect (3*WINDOW_WIDTH/4 + (WINDOW_WIDTH/4 - 200)/2 + 100, 360, 100, 100), HintButton.clicked, self)
        self.pause_button = PauseButton ("pause_button", pygame.Rect (3*WINDOW_WIDTH/4 + (WINDOW_WIDTH/4 - 200)/2 + 50, WINDOW_HEIGHT - 120, 100, 100), PauseButton.clicked, self)
        
        self.hints_left_label = ScreenText ("hints_left_label", "Hints Remaining: " + str (self.hints_left), pygame.Rect (3*WINDOW_WIDTH/4, 475, WINDOW_WIDTH/4, 25), FONT_SMALL)

        self.logo = planes.Plane ("setlogo", pygame.Rect (3*WINDOW_WIDTH/4, 50, 240, 162), False, False) 
        
        self.logo.image = pygame.image.load (IMG+"/set.jpg")
        
        self.time_box = TimeBox ("time_box", pygame.Rect (0, -WINDOW_HEIGHT, WINDOW_WIDTH, WINDOW_HEIGHT), game_select)
        
        #### PAUSE SCREEN BUTTONS ####
        message_width = 3*CARD_WIDTH + 2*space_horiz # width of playing field
        self.play_button = PlayButton ("play_button", pygame.Rect (2*message_width/5 - 50, WINDOW_HEIGHT - 300, 100, 100), PlayButton.clicked, self)
        
        self.restart_button = RestartButton ("restart_button", pygame.Rect (3*message_width/5 - 50, WINDOW_HEIGHT - 300, 100, 100), RestartButton.clicked, self) 
        self.back_button = BackButton ("back_button", pygame.Rect (4*message_width/5 - 50, WINDOW_HEIGHT - 300, 100, 100), BackButton.clicked, self)
        
        #### CATEGORIES ####
        self.gamebuttons = [self.add3_button, self.hint_button, self.pause_button, self.logo]
        self.gamelabels = [self.sets_found_label, self.time_label, self.hints_left_label, self.left_in_deck_label]
        self.pausebuttons = [self.play_button, self.restart_button, self.back_button]

        # start the game
        self.add_new_cards (12)

    # Add cards to the in-play cards
    # Number = number of cards to add
    # Index allows adding 1 card in the same position as a removed card
    # Does not check whether we SHOULD because assumes we have checked that before calling
    def add_new_cards (self, number, index=0):
        if not len (self.in_play_cards) + len (self.out_of_play_cards) == len (self.deck):
			i = 0
			while i < number:
				num = random.randint (0,len (self.deck)-1)
				card = self.deck[num]
				if card not in self.in_play_cards and card not in self.out_of_play_cards:
					self.in_play_cards.insert (index, card)
					i += 1

	# Checks if any sets on the board
    def check_if_any_sets (self):
		for card1 in self.in_play_cards:
			for card2 in self.in_play_cards:
				for card3 in self.in_play_cards:
					if card1 != card2 and card2 != card3 and card1 != card3:
						if check_set (card1, card2, card3):
							return True
		return False

    # Checks if game is won
    def check_if_won (self):
        return (not self.check_if_any_sets()) and (len (self.in_play_cards) + len (self.out_of_play_cards) == len (self.deck))

    # Game can only be lost if playing in time mode
    def check_if_lost (self):
        return self.time_box.rect.y >= 0

    # Game can only be lost if playing in time mode
    def check_in_play (self):
        return not self.check_if_won() and not self.check_if_lost() and self.paused_time_at == 0 

	# Called infinitely
    def update (self):
		# if game not in play, display messages, not cards
		if not self.check_in_play():
			self.actors = []
			self.actors += self.gamelabels + self.gamebuttons
			self.hints_left_label.update_text ("Hints Remaining: " + str (self.hints_left))
			self.left_in_deck_label.update_text ("Deck: " + str (len (self.deck) - (len (self.in_play_cards) + len (self.out_of_play_cards))))

			message_box = planes.Plane ('message_box',
										pygame.Rect (left_margin, 
													top_margin, 
													3*CARD_WIDTH + 2*space_horiz, 
													4*CARD_HEIGHT + 3*((WINDOW_HEIGHT - 4*CARD_HEIGHT - 2*top_margin) / 3)))
			message_box.image.fill ((0,0,0))
			message_texts = []

			# if game won or lost, note time game ended
			if self.check_if_won() or self.check_if_lost():
				if self.end_time == 0:
					self.end_time = pygame.time.get_ticks()

				total_time = self.end_time - self.start_time - self.pause_time

				if self.check_if_won() and not self.added_time:
					self.model.add_time((total_time+(self.sets_wrong*TIME_DEDUC))/ 1000)
					self.added_time = True

				best_time = ""
				if len(self.model.times) == 0:
					best_time = format_secs (total_time/ 1000)
				else:
					best_time = format_secs (min (self.model.times))

				win_stats = "Game Complete! \n" + \
							"Total time: " + format_secs ((self.end_time - self.start_time - self.pause_time)/ 1000) + "\n" +\
							"Best time: " + best_time

				win_stats_with_loss = "Game Complete! \n" + \
									  "Total time: " + format_secs (total_time/ 1000) + "\n" +\
									  "Incorrect Sets: " + str(self.sets_wrong) + "\n" +\
									  "Adjusted Time: " + format_secs ((total_time+(self.sets_wrong*TIME_DEDUC))/ 1000) + "\n" +\
									  "Best time: " + best_time

				lose_stats = "Game Over!"

				stats = win_stats_with_loss
				if self.check_if_lost():
					stats = lose_stats

				lines = stats.split ("\n")
				box_width = 3*CARD_WIDTH + 2*space_horiz
				for line in lines:
					message_texts.append (ScreenText (line, line, 
										pygame.Rect(left_margin, top_margin + 50*(lines.index(line)+1) ,box_width, 45), FONT_BIG))

			elif self.paused_time_at != 0: #game is paused
				message_texts.append (ScreenText ("message_text", "Game Paused",
										pygame.Rect (left_margin, 
													top_margin, 
													3*CARD_WIDTH + 2*space_horiz, 
													4*CARD_HEIGHT + 3*((WINDOW_HEIGHT - 4*CARD_HEIGHT - 2*top_margin) / 3)),
										FONT_BIG))
				
			self.actors.append (message_box)
			self.actors += message_texts
			self.actors += self.pausebuttons

		# game in play
		else:
			self.time_box.update()
			self.actors = [self.time_box]

			#check which cards are clicked
			self.clicked_cards = []
			for card in self.in_play_cards:
				self.actors.append (card)
				if card.been_clicked:
					self.clicked_cards.append (card)
				card.update()

			#add click boxes
			for card in self.clicked_cards:
				clicked_box = planes.Plane ("box" + card.name,
											pygame.Rect (card.rect.x-5,
														 card.rect.y-5,
														 card.rect.width + 10,
														 card.rect.height + 10),
											False, False)
				clicked_box.image = pygame.image.load (IMG+"/clickbox.png")
				self.actors.insert (1, clicked_box)

			#check for sets
			if len(self.clicked_cards) == 3:
				is_set = check_set (self.clicked_cards[0], 
									self.clicked_cards[1],
									self.clicked_cards[2])
				if is_set:
					self.sets_found += 1
					self.sets_found_label.update_text ("Sets: " + str (self.sets_found))

					# reset the time box
					self.time_box.rect.y = -WINDOW_HEIGHT

					#remove cards and add new ones
					for card in self.clicked_cards:
						self.out_of_play_cards.append (card)
						index = self.in_play_cards.index (card)
						self.in_play_cards.remove (card)
						if len (self.in_play_cards) < 12:
							self.add_new_cards (1, index)
				else:
					self.sets_wrong += 1
				for card in self.clicked_cards:
					card.been_clicked = False
                
                self.actors += self.gamelabels + self.gamebuttons
                self.time_label.update_text("Time: " + format_secs((self.duration - (pygame.time.get_ticks() - self.start_time - self.pause_time))/ 1000))
                self.hints_left_label.update_text ("Hints Remaining: " + str (self.hints_left))
                self.left_in_deck_label.update_text ("Deck: " + str (len (self.deck) - (len (self.in_play_cards) + len (self.out_of_play_cards))))

'''
The Model is the overall object in controlling the entire program
It instantiates Game objects as needed but also contains home screen
'''
class Model:
	def __init__ (self,dur):
		self.background = (0,0,0)
		self.mode = MODE_GAME
		#self.mode = MODE_HOME
		self.game_select = NOTIME

		self.game = Game(NOTIME, self,dur)
		#self.game = None
		self.actors = []
		#try:
		#	times_file = open("times_file.txt","r")
		#except:
		#	times_file = open("times_file.txt", "w+")
		#self.times = [int(score.strip()) for score in times_file.readlines()]
		#times_file.close()
		self.show_stats = [] # a list of things for stats screen

		########################
		# HOME SCREEN ELEMENTS #
		########################

		self.title = planes.Plane("title", pygame.Rect (left_margin, top_margin, 13*WINDOW_WIDTH/16, (WINDOW_HEIGHT-300)))

		self.start_button = StartButton ("start_button",
										pygame.Rect (3*WINDOW_WIDTH/4 + (WINDOW_WIDTH/4 - 200)/2 + 100, 50, 100, 100),
										StartButton.clicked,
										self)

		self.notime_button = NoTimeButton ("notime_button",
										pygame.Rect (WINDOW_WIDTH/5 - 50, WINDOW_HEIGHT - 200, 100, 100),
										NoTimeButton.clicked,
										self)
		self.easy_button = EasyButton ("easy_button",
										pygame.Rect (2*WINDOW_WIDTH/5 - 50, WINDOW_HEIGHT - 200, 100, 100),
										EasyButton.clicked,
										self)
		self.med_button = MedButton ("med_button",
										pygame.Rect (3*WINDOW_WIDTH/5 - 50, WINDOW_HEIGHT - 200, 100, 100),
										MedButton.clicked,
										self)
		self.hard_button = HardButton ("hard_button",
										pygame.Rect (4*WINDOW_WIDTH/5 - 50, WINDOW_HEIGHT - 200, 100, 100),
										HardButton.clicked,
										self)
		self.stats_button = StatsButton ("stats_button",
										pygame.Rect (3*WINDOW_WIDTH/4 + (WINDOW_WIDTH/4 - 200)/2 + 100, 200, 100, 100),
										StatsButton.clicked,
										self)

		self.homebuttons = [self.start_button, self.notime_button, self.easy_button, self.med_button, self.hard_button, self.stats_button]
	
	# Opens the times file and writes a new time score to the end
	def add_time(self, time):
		times_file = open("times_file.txt", "a")
		times_file.write(str(time)+"\n")
		self.times.append(time)
		times_file.close()

	# update model - either update homescreen or update game
	def update (self):
		if self.mode == MODE_HOME:
			self.actors = [self.title] + self.homebuttons[:]
			if self.show_stats != None:
				self.actors += self.show_stats
			clicked_button = None
			#add click box 
			for button in self.homebuttons:
				if button.clickbox:
					clicked_button = button

			clicked_box = planes.Plane ("box" + clicked_button.name,
										pygame.Rect (clicked_button.rect.x-5,
													 clicked_button.rect.y-5,
													 clicked_button.rect.width + 10,
													 clicked_button.rect.height + 10),
										False, False)

			self.actors.insert (1, clicked_box)
		
		else:
			self.game.update()
			self.actors = self.game.actors[:]

'''
Draw elements of Model actors onto screen
'''
class View:
    def __init__ (self, model, screen):
        self.model = model
        self.screen = screen

    def draw (self):
        self.screen.remove_all()
        if isinstance (self.model.background, str):
            self.screen.image = pygame.transform.scale (pygame.image.load (self.model.background),(WINDOWWIDTH,WINDOWHEIGHT))
        else:
            self.screen.image.fill (self.model.background)

        #put cards in play into a grid:
        if self.model.game != None:
            space_vert = 50
            # space_vert changes so that cards adjust themselves if more than 12
            # never more than 21, any collection of 20 cards must contain a Set
            if len (self.model.game.in_play_cards) == 12:
                space_vert = (WINDOW_HEIGHT - 4*CARD_HEIGHT - 2*top_margin) / 3
            elif len (self.model.game.in_play_cards) == 15:
                space_vert = (WINDOW_HEIGHT - 5*CARD_HEIGHT - 2*top_margin) / 4
            elif len (self.model.game.in_play_cards) == 18:
                space_vert = (WINDOW_HEIGHT - 6*CARD_HEIGHT - 2*top_margin) / 5
            elif len (self.model.game.in_play_cards) == 21:
                space_vert = (WINDOW_HEIGHT - 7*CARD_HEIGHT - 2*top_margin) / 6
            
            # create positions of cards
            positions = [(left_margin, top_margin), 
                (left_margin + CARD_WIDTH + space_horiz, top_margin), 
                (left_margin + 2*CARD_WIDTH + 2*space_horiz, top_margin),

                (left_margin, top_margin + CARD_HEIGHT + space_vert),
                (left_margin + CARD_WIDTH + space_horiz, top_margin + CARD_HEIGHT + space_vert),
                (left_margin + 2*CARD_WIDTH + 2*space_horiz, top_margin + CARD_HEIGHT + space_vert),

                (left_margin, top_margin + 2*CARD_HEIGHT + 2*space_vert),
                (left_margin + CARD_WIDTH + space_horiz, top_margin + 2*CARD_HEIGHT + 2*space_vert),
                (left_margin + 2*CARD_WIDTH + 2*space_horiz, top_margin + 2*CARD_HEIGHT + 2*space_vert),

                (left_margin, top_margin + 3*CARD_HEIGHT + 3*space_vert),
                (left_margin + CARD_WIDTH + space_horiz, top_margin + 3*CARD_HEIGHT + 3*space_vert),
                (left_margin + 2*CARD_WIDTH + 2*space_horiz, top_margin + 3*CARD_HEIGHT + 3*space_vert),

                (left_margin, top_margin + 4*CARD_HEIGHT + 4*space_vert),
                (left_margin + CARD_WIDTH + space_horiz, top_margin + 4*CARD_HEIGHT + 4*space_vert),
                (left_margin + 2*CARD_WIDTH + 2*space_horiz, top_margin + 4*CARD_HEIGHT + 4*space_vert),

                (left_margin, top_margin + 5*CARD_HEIGHT + 5*space_vert),
                (left_margin + CARD_WIDTH + space_horiz, top_margin + 5*CARD_HEIGHT + 5*space_vert),
                (left_margin + 2*CARD_WIDTH + 2*space_horiz, top_margin + 5*CARD_HEIGHT + 5*space_vert),

                (left_margin, top_margin + 6*CARD_HEIGHT + 6*space_vert),
                (left_margin + CARD_WIDTH + space_horiz, top_margin + 6*CARD_HEIGHT + 6*space_vert),
                (left_margin + 2*CARD_WIDTH + 2*space_horiz, top_margin + 6*CARD_HEIGHT + 6*space_vert) 
            ]

            # assign positions to cards in play
            for i in range (len (self.model.game.in_play_cards)):
                self.model.game.in_play_cards[i].rect.x = positions[i][0]
                self.model.game.in_play_cards[i].rect.y = positions[i][1]

		# add all actors to screen
		for actor in self.model.actors:
			self.screen.sub (actor)


class Practice:
    def __init__(self,screen,dur,lang):
        self.starttime = pygame.time.get_ticks()
        self.pagespecs = yaml.load(open(ROOT+'/pagespecs.yml'))
        self.lang = lang
        self.side = 'right' if lang == 'he' else 'left'
        self.font = pygame.font.SysFont ("Arial",26)
        langdir = os.path.join(ROOT,'lang')
        self.trans = gettext.translation('setgame',langdir,[self.lang])
        self.trans.install()
        self.current_page = 0
        self.currently_on_screen = list()
        self.text_lines = 1
        self.screen = screen
        self.pages = list()
        self.vert_space = 20
        self.compile_main()
        self.compile_pages()
        self.numpages = len(self.pages) + 1
        self.show_page(0)
        self.practice_duration = dur
        self.return_vars = {
            'practice_game_start': 0,
            'practice_sequence_end': 0,
            'practice_correct_speed': 0,
            'practice_wrong' : 0,
            'prev_press' : 0,
            'next_press' : 0
        }
   
    def compile_main(self):
        button_height = 50
        button_width = 100
        self.main_area = pygame.Rect(0,0,WINDOW_WIDTH,WINDOW_HEIGHT - button_height)
        nav_buttons_top = WINDOW_HEIGHT - button_height -  self.vert_space
        self.next_button = planes.gui.Button("Next",pygame.Rect(WINDOW_WIDTH/2 - button_width - 10, nav_buttons_top,button_width,button_height),self.next_page,(0,0,190),WHITE,'practice_next')
        self.prev_button = planes.gui.Button("Previous",pygame.Rect(WINDOW_WIDTH/2 + 10,nav_buttons_top,button_width,button_height),self.prev_page,(0,0,190),WHITE,'practice_prev')
        #self.screen.image.fill(GREEN,self.main_area)
        self.incor = planes.gui.Label('incorrect_feedback',"",pygame.Rect(0,(self.main_area.height/2) - 70,self.main_area.width,70),(0,0,0),RED,self.font)

        
    def compile_pages(self):
        self.pages = list()
        for pagename,specs in sorted(self.pagespecs.items()): 
            if not pagename.startswith('page'):
                continue
            page_elements = list()
            vert_position = self.vert_space
            for spec in specs: 
                if spec['type'] == 'text':
                    pos,elems = self.text_block(spec['lines'],vert_position) 
                elif spec['type'] == 'cardsrow':
                    pos,elems =  self.cards_row(spec['cards'],vert_position)
                page_elements += elems
                vert_position = pos
            self.pages.append(page_elements)

    def text_block(self,data,vertstart): 
        lineheight = 30
        linespacing = 10
        lines = list()
        vertpos = vertstart
        for line in data:
            lineid = "line"+str(line)
            vertpos += lineheight + linespacing
            lines.append(ScreenText(lineid,get_display(unicode(_(lineid),'utf-8')),pygame.Rect(0,vertpos,self.main_area.width,lineheight),self.font,self.side))
            self.text_lines += 1
        return (vertpos + self.vert_space,lines)
    
    def cards_row(self,data,vertstart):
        cards = list()
        positions = [
            (left_margin, vertstart), 
            (left_margin + CARD_WIDTH + space_horiz, vertstart), 
            (left_margin + 2*CARD_WIDTH + 2*space_horiz, vertstart),
        ]
        for i,spec in enumerate(data):
            spec = map(lambda x: str(x),spec)
            card = Card("".join(spec), spec[0],spec[1],int(spec[3]),spec[2])
            card.rect.x = positions[i][0]
            card.rect.y = positions[i][1]
            card.image = pygame.image.load(IMG+"/" + card.name + ".png")
            cards.append(card)
        vertend = vertstart + CARD_HEIGHT + self.vert_space
        return (vertend,cards)

    def next_page(self,button):
        self.current_page = (self.current_page + 1) % self.numpages
        self.show_page(self.current_page)
        self.return_vars['next_press'] += 1

    def prev_page(self,button):
        self.current_page = (self.current_page - 1) % self.numpages
        self.show_page(self.current_page)
        self.return_vars['prev_press'] += 1
    
    def show_page(self,pagenum):
        if pagenum == self.numpages - 1:
            self.practice_game()
        else:
            self.render(self.pages[self.current_page] + [self.next_button,self.prev_button])
                
    def render(self,elems):
        self.screen.remove_all()
        for elem in elems: 
            self.screen.sub(elem)
        self.screen.update()
        self.screen.render()
        pygame.display.flip()
        self.currently_on_screen = elems
    
    def refresh(self,**kwargs):
        remove = kwargs.get('remove') or list()
        add = kwargs.get('add') or list()
        elems = [ elem for elem in self.currently_on_screen if elem not in remove]
        elems += [ elem for elem in add if elem not in elems] 
        if self.currently_on_screen != elems:
            self.render(elems)
    
    def register(self,key,value):
        print "%s: %r" %(key,value)
        if key in self.return_vars.keys():
            self.return_vars[key] = value
        else:
            raise KeyError 

    def practice_game(self):
        self.register('practice_game_start',pygame.time.get_ticks() - self.starttime)
        pygame.time.set_timer(pygame.USEREVENT,self.practice_duration)
        time.sleep(0.1)
        self.screen.remove_all()
        cards = list()
        highlights = list()
        clicked_cards = list()
        vert_position = self.vert_space
        correct = [3,5,7]
        running = True
        foundit = False
        
        #collect the cards
        cindex = 0
        for rowname,cardspecs in self.pagespecs['practice_game'].iteritems():
            pos,threecards = self.cards_row(cardspecs,vert_position)
            for card in threecards:
                card.index = cindex
                cards.append(card)
                clicked_box = planes.Plane ("clickbox" + str(card.index), pygame.Rect(card.rect.x-5, card.rect.y-5, card.rect.width + 10, card.rect.height + 10), False, False)

                clicked_box.image = pygame.image.load (IMG+"/clickbox.png")
                clicked_box.index = cindex
                cindex += 1
                highlights.append(clicked_box)
            vert_position = pos
        self.render([self.prev_button,self.next_button] + cards) 

        #game loop
        while running:
            clicked_changed = False
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                    pygame.quit()
                if event.type == pygame.USEREVENT :
                    for card in clicked_cards:
                        self.refresh(remove=[highlights[card.index]])
                        card.been_clicked = False
                    clicked_cards = list()
                    for cindex in correct:
                        card = cards[cindex]
                        self.refresh(add=[highlights[cindex]],remove=[card])
                        self.refresh(add=[card])
                        pygame.time.wait(1000)
                        clicked_cards.append(card)
                    clicked_changed = True
            
            self.screen.process(events)
                         
            for card in cards:
                if card.been_clicked and card not in clicked_cards:
                    clicked_changed = True
                    self.refresh(remove=[self.incor])
                    clicked_cards.append(card)
                card.update()
            if clicked_changed: 
                for card in clicked_cards:
                    self.refresh(add=[highlights[card.index]],remove=[card])
                    self.refresh(add=[card])
                found = sorted([card.index for card in clicked_cards])
                if found == correct:
                    self.register('practice_correct_speed',pygame.time.get_ticks() - self.return_vars['practice_game_start'])
                    running = False
                    self.correct_feedback()
                elif len(clicked_cards) == 3:
                    self.incor.text = self.incorrect_feedback(clicked_cards)
                    self.refresh(add=[self.incor])
                    for card in clicked_cards:
                        self.refresh(remove=[highlights[card.index]])
                        card.been_clicked = False
                    clicked_cards = list()
        
    def correct_feedback(self):
        self.register('practice_sequence_end',pygame.time.get_ticks())
        cor = planes.gui.Label('correct_feedback',get_display(unicode(_('correct'),'utf-8')),pygame.Rect((self.main_area.width/2) - 250,(self.main_area.height/2) - 100,500,50),(0,0,0),GREEN,FONT_BIG)
        self.refresh(add=[cor])
        pygame.time.wait(2000)
        pygame.event.post(pygame.event.Event(pygame.QUIT)) 

    def incorrect_feedback(self,cards):
        self.return_vars['practice_wrong'] += 1
        message = ""
        props = {
            'color' : [card.color for card in cards],
            'shape' : [card.shape for card in cards],
            'shade' : [card.shade for card in cards],
            'number' : [card.number for card in cards]
        }
        for prop in props.keys():
            repeats = len(set(props[prop]))  
            if repeats == 2:
                message += get_display(unicode(_("the %s repeats twice" % prop),'utf-8'))
                message += unicode(" ,",'utf-8')

        return message.strip(" ,")
        


# THE MAIN LOOP
def play(frame,dur,lang,fullscreen):
    #if __name__ == "__main__":
    pygame.init()
    size = (WINDOW_WIDTH, WINDOW_HEIGHT)
    #screen = planes.Display(size)
    screen = planes.Display(frame,fullscreen)
    screen.grab = False
    screen.image.fill(BLACK)
    model = Model(dur)
    view = View(model,screen)
    running = True
    pygame.time.set_timer(pygame.QUIT,dur)
    ret = dict()
    while running:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                #raise SystemExit
                running = False
                ret =  {
                    "sets_found" : view.model.game.sets_found,
                    "sets_wrong" : view.model.game.sets_wrong
                }
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                ret = "keyboard interrupt"

        screen.process(events)
        model.update()
        screen.update()
        screen.render()
        view.draw()
        pygame.display.flip()
        time.sleep (.001)
    return ret

def practice(frame,dur,lang,fullscreen):
    pygame.init()
    size = (WINDOW_WIDTH, WINDOW_HEIGHT)
    screen = planes.Display(frame,fullscreen)
    screen.grab = False
    screen.image.fill(BLACK)
    view = Practice(screen,dur,lang)
    running = True
    while running:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
                ret =  view.return_vars            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                ret = "keyboard interrupt"
        screen.process(events)
    return ret


