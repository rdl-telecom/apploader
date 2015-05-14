from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.filesystems import AbstractedFS
from pyftpdlib.handlers import FTPHandler, DTPHandler
from pyftpdlib.servers import FTPServer
from os.path import dirname, basename, isfile
import os
import threading

class MyAuthorizer(DummyAuthorizer):
	def add_anonymous(self, filename, **kwargs):
		self._filename = filename
		DummyAuthorizer.add_anonymous(self, dirname(filename))

	def get_file_name(self):
		return unicode(basename(self._filename))

class FileFS(AbstractedFS):
	def add_filename(self, filename):
		self._filename = filename

	def listdir(self, path):
		return [ self._filename ]

class MyDTPHandler(DTPHandler):
	ac_out_buffer_size = 1048576
	def send(self, data):
		tot_bytes_sent = DTPHandler.send(self, data)
		return tot_bytes_sent

class MyFTPHandler(FTPHandler):
	dtp_handler = MyDTPHandler
	def ftp_PASS(self, line):
		FTPHandler.ftp_PASS(self, line)
		if isinstance(self.fs, FileFS):
			self.fs.add_filename(self.authorizer.get_file_name())

class Distributor(FTPServer, threading.Thread):
	def __init__(self, ip, filename):
		threading.Thread.__init__(self)
		assert isfile(filename)

		authorizer = MyAuthorizer()
		authorizer.add_anonymous(filename)
		self._filename = basename(filename)
		self._filesize = os.stat(filename).st_size

		handler = MyFTPHandler
		handler.authorizer = authorizer
		handler.on_file_sent = self.on_file_sent
		handler.abstracted_fs = FileFS
		address = (ip, 21)
		self._url = 'ftp://' + ip + '/' + self._filename

		FTPServer.__init__(self, address, handler)
		self.start()

	def get_filename(self):
		return self._filename

	def get_filesize(self):
		return self._filesize

	def get_url(self):
		return self._url

	def run(self, *args, **kwargs):
		self.serve_forever()

	def stop(self):
		self.close_all()

	def on_file_sent(self, filename):
		self.stop()

	def on_disconnect(self, filename):
		self.stop()