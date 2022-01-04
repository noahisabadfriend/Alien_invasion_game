import sys
import json

import pygame

import sound_effects as se
from time import sleep

from settings import Settings
from game_stats import GameStats
from scoreboard import Scoreboard
from button import Button
from ship import Ship
from bullet import Bullet
from alien import Alien


# I was trying to save the all time high_score
# I had to create a method close_game so that it execute a function
# before closing the game, once made i had to get rid of the sys.exit()
# function because i needed to call my method to save the score first before
# closing the game down 

class AlienInvasion:
	"""Overall class to manage game assets and behavior"""
	def __init__(self):
		"""Initialize the game and create game resources"""
		pygame.init()
		self.settings = Settings()

		self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
		self.settings.screen_width = self.screen.get_rect().width
		self.settings.screen_height = self.screen.get_rect().height
		pygame.display.set_caption("Alien Invasion")

		# Create an instance to store game stats
		# and create a scoreboard
		self.stats = GameStats(self)
		self.sb = Scoreboard(self)

		self.ship = Ship(self)
		self.bullets = pygame.sprite.Group()
		self.aliens  = pygame.sprite.Group()

		self._create_fleet()

		#Make the play button
		self.play_button = Button(self, "Play")

	def run_game(self):
		"""Start the main loop for the game"""
		while True:
			self._check_events()
			if self.stats.game_active:
				self.ship.update()
				self._update_bullets()
				self._update_aliens()

			self._update_screen()

	def _check_events(self):
		# Watch for keyboard and mouse movements 
		for event in pygame.event.get():
		 	if event.type == pygame.QUIT:
		 		self._close_game()
		 	elif event.type == pygame.KEYDOWN:
		 		self._check_keydown_events(event)
		 	elif event.type == pygame.KEYUP:
		 		self._check_keyup_events(event)

		 	elif event.type == pygame.MOUSEBUTTONDOWN:
		 		mouse_pos = pygame.mouse.get_pos()
		 		self._check_play_button(mouse_pos)

	def _check_play_button(self, mouse_pos):
		""" start a new game when the player clicks play"""
		button_clicked = self.play_button.rect.collidepoint(mouse_pos)
		if button_clicked and not self.stats.game_active:
			# Reset the game settings
			self.settings.initialize_dynamic_settings()
			# Reset the game statistics
			self.stats.reset_stats()
			self.stats.game_active = True
			self.sb.prep_score()
			self.sb.prep_level()
			self.sb.prep_ships()

			# Get rid of any remaining aliens and bullets
			self.aliens.empty()
			self.bullets.empty()

			# Create a new fleet
			self._create_fleet()
			self.ship.center_ship()

			# Hide the mouse cursor
			pygame.mouse.set_visible(False)

	def _start_game(self):
		"""Create a button to start the game"""
		self.stats.game_active = True

	def _check_keydown_events(self, event):
		""" Respond to the keypresses"""
		if event.key == pygame.K_RIGHT:
		 	self.ship.moving_right = True
		elif event.key == pygame.K_LEFT:
			self.ship.moving_left = True
		elif event.key == pygame.K_q:
			self._close_game()
		elif event.key == pygame.K_SPACE:
			self._fire_bullet()
		elif event.key == pygame.K_p:
			self._start_game()

	def _check_keyup_events(self, event):
		"""Respond to the keypresses"""
		if event.key == pygame.K_RIGHT:
		 	self.ship.moving_right = False
		elif event.key == pygame.K_LEFT:
		 	self.ship.moving_left = False

	def _fire_bullet(self):
		"""Create a new bullet and add it to the bullets group"""
		if len(self.bullets) < self.settings.bullets_allowed:
			new_bullet = Bullet(self)
			self.bullets.add(new_bullet)
			se.bullet_sound.play()

	def _update_bullets(self):
		"""Update the position of bullets and get rid of the old ones"""
		#Update the bullet position
		self.bullets.update()

		#get rid of bullets that have disappeared
		for bullet in self.bullets.copy():
			if bullet.rect.bottom <= 0:
				self.bullets.remove(bullet)

		self._check_bullet_alien_collisions()

	def _check_bullet_alien_collisions(self):
		"""""Respond to bullet-alien collisions"""
		# Check for any bullets that have hit aliens
		# if so get rid of the bullet and the alien

		collisions = pygame.sprite.groupcollide(
				self.bullets, self.aliens, False, True)

		if collisions:
			for aliens in collisions.values():
				self.stats.score += self.settings.alien_points * len(aliens)
			self.sb.prep_score()
			self.sb.check_high_score()
			se.alien_sound.play()

		if not self.aliens:
			# Destroy existing bullets and create a new fleet
			self.bullets.empty()
			self._create_fleet()
			self.settings.increase_speed()

			# Increase the level
			self.stats.level += 1
			self.sb.prep_level()


	def _ship_hit(self):
		"""Respond to the ship being hit by an alien"""
		# Decrement ships left
		if self.stats.ships_left > 0:
			# Decrement ships left adn update the scoreboard
			self.stats.ships_left -= 1
			self.sb.prep_ships()

			# Get rid of any remianing aliens and bullets 
			self.aliens.empty()
			self.bullets.empty()

			# Create a new fleet and center the ship
			self._create_fleet()
			self.ship.center_ship()

			# Pause
			sleep(1.0)
		else:
			self.stats.game_active = False
			pygame.mouse.set_visible(True)

	def _create_fleet(self):
		"""Create the fleet of aliens"""
		# Make an alien
		alien = Alien(self)
		alien_width, alien_height = alien.rect.size
		available_space_x = self.settings.screen_width - (2 * alien_width)
		number_aliens_x = available_space_x // (3 * alien_width)

		# Determine the number of rows of aliens to fit in the screen
		ship_height = self.ship.rect.height
		available_space_y = (self.settings.screen_height -
								(3 * alien_height) - ship_height)
		number_rows = available_space_y // (2 * alien_height)

		#Create the full fleet of aliens
		for row_number in range(number_rows):
			for alien_number in range(number_aliens_x):
				self._create_alien(alien_number, row_number)

	def _create_alien(self, alien_number, row_number):
		"""Create an alien and place it in the row"""
		#Create an alien and place it in the row
		alien = Alien(self)
		alien_width, alien_height = alien.rect.size
		alien.x = alien_width + 2 * alien_width * alien_number
		alien.rect.x = alien.x
		alien.rect.y = alien.rect.height + 2 * alien.rect.height * row_number
		self.aliens.add(alien)

	def _check_aliens_bottom(self):
		""" Check if any aliens have reached the bottom of the screen"""
		screen_rect = self.screen.get_rect()
		for alien in self.aliens.sprites():
			if alien.rect.bottom >= screen_rect.bottom:
				# Treat this teh same as if the ship got hit
				self._ship_hit()
				break

	def _check_fleet_edges(self):
		""" Respond appropriately if any aliens have reached an edge"""
		for alien in self.aliens.sprites():
			if alien.check_edges():
				self._change_fleet_direction()
				break

	def _change_fleet_direction(self):
		""" Drop the entire fleet and chnage the fleets direction"""
		for alien in self.aliens.sprites():
			alien.rect.y += self.settings.fleet_drop_speed
		self.settings.fleet_direction *= -1

	def _update_aliens(self):
		"""
		Check if the fleet is at an edge,
		then update the positions of all aliens in the fleet
		"""
		self._check_fleet_edges()
		self.aliens.update()

		# Look for alien-ship collisions
		if pygame.sprite.spritecollideany(self.ship, self.aliens):
			self._ship_hit()

		# Look for aliens hitting the bottom of the screen
		self._check_aliens_bottom()

	def _update_screen(self):
		# Update the bullet position and get rid of old bullets
		self.screen.fill(self.settings.bg_color)
		self.ship.blitme()
		for bullet in self.bullets.sprites():
			bullet.draw_bullet()
		self.aliens.draw(self.screen)

		# Draw the score information
		self.sb.show_score()
		self.stats.get_saved_high_score()

		# Draw the play button if the game is active
		if not self.stats.game_active:
			self.play_button.draw_button()

		pygame.display.flip()

	def _close_game(self):
		"""Save high score and exit"""
		saved_high_score = self.stats.get_saved_high_score()
		if self.stats.high_score > saved_high_score:
			with open('high_score.json', 'w') as f:
				json.dump(self.stats.high_score, f)

		sys.exit()

  
if __name__ == '__main__':
	# make the game instance and run the game
	ai = AlienInvasion()	
	ai.run_game()