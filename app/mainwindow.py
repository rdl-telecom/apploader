from Tkinter import *
import tkFileDialog, tkMessageBox
import ttk
from networking import Networking
from distributor import Distributor
from sshsession import SSHSession
from os.path import dirname, basename
from configfile import ConfigFile
import re
import time
import platform

ip_re = re.compile(r'^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
filename_filler = 'Choose a file...'

class MainWindow:
	row_number = 0
	source_url = ''
	progress_bar = None
	controls = []
	start_button = None
	estimated_label = None
	distributor = None
	ssh_session = None

	def __init__(self, title):
		config_file = ConfigFile()
		self.destination_dir = config_file['icomera__destination_dir']
		self.networking = Networking()
		self.create_root(title)
		self.source_string = StringVar()
		self.destination_string = StringVar()
		self.filename_string = StringVar()
		self.command_string = StringVar()
		self.estimated_string = StringVar()
		self.create_source_widgets(self.networking.source)
		self.create_destination_widgets(self.networking.destination)
		self.create_delimiter()
		self.create_filename_widgets()
		self.create_delimiter()
#		self.create_commandline()
		self.create_progressbar()
		self.create_delimiter()
		self.create_start_button()

	def create_root(self, title):
		self.root = Tk()
		self.root.title(title)
		self.root.columnconfigure(0, minsize=100)
		self.root.columnconfigure(1, minsize=360)
		self.root.columnconfigure(2, minsize=40)
		self.root.protocol("WM_DELETE_WINDOW", self.on_close)

	def finish_row(self):
		self.row_number += 1

	def create_source_widgets(self, source):
		Label(self.root, text='Source', justify=LEFT).grid(row=self.row_number, sticky=W)
		value = source
		if not value:
			value = self.networking.ip_list[0]
		self.source_string.set(value)
		self.source_string.trace('w', self.source_changed)
		listbox_src = OptionMenu(self.root, self.source_string, *self.networking.ip_list)
		listbox_src.grid(row=self.row_number, column=1, columnspan=2, sticky=EW)
		self.controls.append(listbox_src)
		self.finish_row()

	def create_destination_widgets(self, destination):
		Label(self.root, text='Destination', justify=LEFT).grid(row=self.row_number, sticky=W)
		text_dst = Entry(self.root, textvariable=self.destination_string, justify=CENTER)
		self.destination_string.set(destination)
		self.destination_string.trace('w', self.destination_changed)
		text_dst.grid(row=self.row_number, column=1, columnspan=2, sticky=EW)
		self.controls.append(text_dst)
		self.finish_row()

	def create_delimiter(self):
		self.root.rowconfigure(self.row_number, minsize=10)
		ttk.Separator(self.root,orient=HORIZONTAL).grid(row=self.row_number, columnspan=3, sticky=EW)
		self.finish_row()

	def create_filename_widgets(self):
		self.filename_string.set(filename_filler)
		Label(self.root, text='File', justify=LEFT).grid(row=self.row_number, sticky=W)
		Label(self.root, textvariable=self.filename_string, justify=RIGHT).grid(row=self.row_number, column=1, sticky=EW)
		choose = Button(self.root, text='...', command=self.file_dialog, font='tahoma 10')
		choose.grid(row=self.row_number, column=2, sticky=EW)
		self.controls.append(choose)
		self.finish_row()

	def create_commandline(self):
		Label(self.root, textvariable=self.command_string, justify=CENTER).grid(columnspan=3, sticky=EW)
		self.finish_row()

	def create_progressbar(self):
		self.progress_bar = ttk.Progressbar(self.root, orient=HORIZONTAL)
		self.progress_bar.grid(row=self.row_number, columnspan=2, sticky=EW)
		self.progress_bar['maximum'] = 100.0
		self.estimated_label = Label(self.root, textvariable=self.estimated_string, justify=RIGHT)
		self.estimated_label.grid(row=self.row_number, column=2, sticky=EW)
		self.zero_progress()
		self.finish_row()

	def create_start_button(self):
		choose = Button(self.root, text='Start', width=10, command=self.main_function, font='tahoma 10')
		choose.grid(row=self.row_number, columnspan=3)
		self.start_button = choose
		self.controls.append(choose)
		choose['state'] = DISABLED
		self.finish_row()

	def source_changed(self, *args):
		self.update_commandline()
		dst = ''
		if self.source_string.get() == self.networking.source:
			dst = self.networking.destination
		self.destination_string.set(dst)
		self.update_start_button_state()

	def destination_changed(self, *args):
		self.update_start_button_state()

	def file_dialog(self):
		config_file = ConfigFile()
		initial_dir = config_file['apploader__initial_dir']
		filename = self.filename_string.get()
		options = {}
		options['parent'] = self.root
		options['title'] = filename_filler
		options['filetypes'] = [('VirtualBox drive files', '.vdi')]
		options['initialdir'] = initial_dir
		if filename and filename != filename_filler:
			options['initialdir'] = dirname(filename)
			options['initialfile'] = basename(filename)
		result = tkFileDialog.askopenfilename(**options)
		if result:
			self.filename_string.set(result)
			newdir = dirname(result)
			if platform.system().lower() == 'windows':
				newdir = newdir.replace('/', '\\')
			config_file['apploader__initial_dir'] = newdir
			self.update_commandline()
		self.update_start_button_state()

	def update_commandline(self):
		filename = basename(self.filename_string.get())
		allright = True
		if not filename or filename == filename_filler:
			filename='<FILENAME>'
			allright = False
		source = self.source_string.get()
		command_line = ''
		if allright:
			command_line = 'busybox wget ftp://' + source + '/' + filename + ' -O ' + self.destination_dir + '/' + filename
		self.command_string.set(command_line)

	def set_controls_state(self, state):
		for control in self.controls:
			control['state'] = state
			control.update()

	def update_start_button_state(self):
		if self.command_string.get() and ip_re.match(self.source_string.get()) and ip_re.match(self.destination_string.get()):
			self.start_button['state'] = NORMAL
		else:
			self.start_button['state'] = DISABLED
		self.start_button.update()

	def main_function(self):
		self.set_controls_state(DISABLED)
		distr = Distributor(self.source_string.get(), self.filename_string.get())
		try:
			ssh = SSHSession(self.destination_string.get())
		except OSError:
			tkMessageBox.showerror('Error', 'Can\'t connect to ' + self.destination_string.get())
			distr.stop()
			self.set_controls_state(NORMAL)
			return
		self.distributor = distr
		self.ssh_session = ssh
		result = self.start_loop()
		if result != 'ok':
			tkMessageBox.showerror('Error', result)			
			self.distributor.stop()

	def start_loop(self):
		try:
			if self.ssh_session.download_file(self.distributor.get_url(), self.destination_dir, self.distributor.get_filesize()):
				while not self.ssh_session.downloaded and self.ssh_session.connected and self.distributor:
					self.progress_bar['value'] = self.ssh_session.progress
					self.progress_bar.update()
					self.estimated_string.set(self.ssh_session.estimated)
					self.estimated_label.update()
					time.sleep(1)
				self.progress_bar['value'] = self.ssh_session.progress
				self.estimated_string.set(self.ssh_session.estimated)
				self.progress_bar.update()
				self.estimated_label.update()
				tkMessageBox.showinfo('Success', 'File ' + self.filename_string.get() + ' successfully uploaded to ' + self.destination_string.get())
				self.zero_progress()
			else:
				raise OSError
		except Exception as e:
			return e
		finally:
			self.set_controls_state(NORMAL)
		return 'ok'

	def zero_progress(self):
		self.progress_bar['value'] = 0.0
		self.estimated_string.set('00:00:00')		

	def run(self):
		self.root.mainloop()

	def on_close(self):
		if self.ssh_session:
			self.ssh_session.stop_event.set()
		if self.distributor:
			self.distributor.stop()
		self.root.destroy()