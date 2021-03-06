import kivy
import socket
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.clock import Clock

from functools import partial

from manager import Menu
from defaults_menu import DefaultsMenu
from settings import MenuScreen, SettingsScreen, NetworksScreen, s

class InstructionMenu(Menu):

	@property
	def cook_time(self):
		return self._cook_time
	@cook_time.setter
	def cook_time(self, value):
		self.time_input.text = self.to_minsec(value)
		self.chosen_settings.text = '\n'.join((self.time_input.text, self.chosen_settings.text.split('\n')[1]))
		self._cook_time = int(value)
	@property
	def cook_temp(self):
		return self._cook_temp
	@cook_temp.setter
	def cook_temp(self, value):
		self.temp_input.text = str(value)
		self.chosen_settings.text = '\n'.join((self.chosen_settings.text.split('\n')[0], self.temp_input.text))
		self._cook_temp = int(value)

	def __init__(self, **kwargs):
		super().__init__(**kwargs)

		''' Cook settings (integers) '''
		self._cook_time = 0
		self._cook_temp = 0

		self.add_child(DefaultsMenu(name='Defaults'))
		self.add_child(MenuScreen(name='menu'))
		self.add_child(SettingsScreen(name='settings'))
		self.add_child(NetworksScreen(name='networks'))

		''' Containing widget for this menu '''
		self.base_layout = FloatLayout(size=self.size)
		self.add_widget(self.base_layout)

		''' Containing widget for this menu '''
		self.entry_layout = FloatLayout(size_hint=(1, .9), pos_hint={'x': 0, 'y': .1})
		self.base_layout.add_widget(self.entry_layout)

		self.entry_layout.add_widget(
			Label(text='Timer:', size_hint=(.5, None), height=self.size[1] // 30, pos_hint={'x': 0, 'y': .8}))
		self.time_input = TextInput(text='', hint_text='00:00', multiline=False, size_hint=(.5, None),
									height=self.size[1] // 30, pos_hint={'x': .5, 'y': .8})
		self.entry_layout.add_widget(self.time_input)
		self.time_input_error = Label(text='', markup=True, size_hint=(.5, None), height=self.size[1] // 30,
									  pos_hint={'x': .25, 'y': .7})
		self.entry_layout.add_widget(self.time_input_error)

		self.entry_layout.add_widget(
			Label(text='Temperature:', size_hint=(.5, None), height=self.size[1] // 30, pos_hint={'x': 0, 'y': .6}))
		self.temp_input = TextInput(text='', hint_text='', multiline=False, size_hint=(.5, None),
									height=self.size[1] // 30, pos_hint={'x': .5, 'y': .6})
		self.entry_layout.add_widget(self.temp_input)
		self.temp_input_error = Label(text='', markup=True, size_hint=(.5, None), height=self.size[1] // 30,
									  pos_hint={'x': .25, 'y': .5})
		self.entry_layout.add_widget(self.temp_input_error)

		self.entry_layout.add_widget(
			Label(text='Time Remaining:', size_hint=(.5, None), height=self.size[1] // 30, pos_hint={'x': 0, 'y': .4}))
		self.time_output = Label(text='', markup=True, size_hint=(.5, None), height=self.size[1] // 30,
								 pos_hint={'x': .5, 'y': .4})
		self.entry_layout.add_widget(self.time_output)

		self.entry_layout.add_widget(Label(text='Toaster Temperature:', size_hint=(.5, None), height=self.size[1] // 30,
										   pos_hint={'x': 0, 'y': .2}))
		self.temp_output = Label(text='', markup=True, size_hint=(.5, None), height=self.size[1] // 30,
								 pos_hint={'x': .5, 'y': .2})
		self.entry_layout.add_widget(self.temp_output)

		self.time_input.bind(text=self.on_text_time)
		self.time_input.bind(on_text_validate=self.on_enter_time)
		self.temp_input.bind(text=self.on_text_temp)
		self.temp_input.bind(on_text_validate=self.on_enter_temp)

		''' Containing widget for user navigation '''
		self.navigation_layout = BoxLayout(orientation='horizontal', spacing=0, size_hint=(1, .1))
		self.base_layout.add_widget(self.navigation_layout)

		self.back_button = Button(text='<- Back')
		self.back_button.bind(on_press=self.on_back)
		self.chosen_settings = Label(text='\n')

		self.settings_button = Button(text='Settings')
		self.settings_button.bind(on_press=self.on_settings)
		self.defaults_button = Button(text='Defaults')
		self.defaults_button.bind(on_press=self.on_defaults)
		self.confirm_button = Button(text='Confirm')
		self.confirm_button.bind(on_press=self.on_confirm)
		self.stop_button = Button(text='Cancel')
		self.stop_button.bind(on_press=self.stop_cooking)

		self.navigation_layout.add_widget(self.back_button)
		self.navigation_layout.add_widget(self.settings_button)
		self.navigation_layout.add_widget(self.stop_button)
		self.navigation_layout.add_widget(self.chosen_settings)
		self.navigation_layout.add_widget(self.confirm_button)
		self.navigation_layout.add_widget(self.defaults_button)

		self.time_capped = False
		self.get_default()

	def get_default(self):
		default_preset = None
		with open('presets.txt', mode='r') as f:
			for line in f:
				if 'Default' in line:
					default_preset = line.strip().split(self.child_menus['Defaults'].delimeter)
					break
		if default_preset is not None:
			self.cook_time = int(default_preset[1])
			self.cook_temp = int(default_preset[2])


	''' Button Callbacks '''

	def on_defaults(self, instance):
		self.switch_to_child('Defaults')

	def on_settings(self, instance):
		self.switch_to_child('menu')


	def on_confirm(self, instance):
		self.temp_input_error.text = ''
		print(repr(self.time_input.text))
		print(repr(self.temp_input.text))
		if not self.time_input.text:
			self.temp_input_error.text = 'Undefined cooking time'
			return
		if not self.temp_input.text:
			self.temp_input_error.text = 'Undefined cooking temperature'
			return
		code = 'Confirm' + ' '
		placeholder = '0'
		confirm_info = code + placeholder
		Menu.send(self, s, confirm_info)
		self.start_cook()
		''' Send chosen parameters to microcontroller'''

	def start_cook(self):
		event = Clock.schedule_interval(lambda dt: self.recv_clock(s, event), 1)

	def recv_clock(self, c, event2):
		''' Receive data from pi (such as remaining time or current temperature '''
		data = 0
		try:
			data = c.recv(12345).decode()
			self.update_event(data, event2)
		except socket.error:
			print("An error has occurred... couldn't send data")

	def update_event(self, data, event2):

		cancel_data = data.split(' ', 6)
		if data == 'Raised':
			self.time_output.text = 'Done!'
			self.temp_output.text = ' '
			event2.cancel()
		elif data == 'Lowering food...' or data == 'Raising food...':
			self.time_output.text = data
			self.temp_output.text = ' '
		elif cancel_data[2] == 'Code':
			self.time_output.text = Menu.to_minsec(self, cancel_data[0])
			self.temp_output.text = cancel_data[1]

	''' Text Field Callbacks '''

	def cursor_update_insert(self, instance, old_cursor, capped, dt):
		''' Move cursor position when colon added to input '''
		old = old_cursor[0]
		new = instance.cursor[0]

		text = instance.text

		if len(text) == 2 and old == 3 and new == 2:
			instance.cursor = new - 1, 0
		elif len(text) == 4 and old == 2 and new == 3:
			instance.cursor = new + 1, 0
		elif len(text) == 5:
			instance.cursor = old if capped else new, 0


	def on_text_time(self, instance, text):
		if not self.time_capped:
			self.time_capped = len(text) > 5
		text = self.just_digits(text, False)[-4:]
		if len(text) > 2:
			text = ':'.join((text[:-2], text[-2:]))
		Clock.schedule_once(partial(self.cursor_update_insert, instance, instance.cursor, self.time_capped))
		instance.text = text

	def on_enter_time(self, instance):
		if ':' in instance.text:
			time = self.to_sec(instance.text)
		else:
			time = int(instance.text)
		self.cook_time = time
		code = 'Time' + ' '
		c_time = str(self.cook_time)
		time_info = code + c_time
		Menu.send(self, s, time_info)

	def on_text_temp(self, instance, text):
		instance.text = self.just_digits(text, False)[-3:]

	def on_enter_temp(self, instance):
		self.cook_temp = int(instance.text)
		code = 'Temp' + ' '
		c_temp = str(self.cook_temp)
		temp_info = code + c_temp
		Menu.send(self, s, temp_info)

	def stop_cooking(self, instance):
		Menu.send(self, s, 'Stop')
