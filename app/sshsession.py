from config import x6_username, x6_password
import paramiko
import threading
import time

def secs2str(secs):
	return time.strftime("%H:%M:%S", time.gmtime(secs))

class SSHSession:
	connected = False
	downloaded = False
	filename = None
	filesize = 0
	progress = 0.0
	timestamp = 0
	wget_thread = None
	update_thread = None

	def __init__(self, ip, port=22):
		self.stop_event = threading.Event()
		self.credentials = {
			'host' : ip,
			'username' : x6_username,
			'password' : x6_password,
			'port' : port
		}
		self.ssh = paramiko.SSHClient()
		self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		self.connect()
		if not self.connected:
			raise OSError('Cannot connect to host')
		self.stop_application()

	def __del__(self):
		if self.connected:
			self.disconnect()

	def stop_application(self):
		try:
			self.command('VBoxManage controlvm TestApp poweroff')
		except RuntimeError:
			pass

	def start_application(self):
		try:
			self.command('VBoxManage startvm TestApp type --headless')
		except RuntimeError:
			pass

	def delete_file(self, filename):
		try:
			self.command('rm -f ' + filename)		
		except RuntimeError:
			raise OSError

	def download_file(self, source_url, destintation_directory, size):
		self.filename = destintation_directory + '/' + source_url.split('/')[-1]
		remote_command = 'busybox wget -qc ' + source_url + ' -O ' + self.filename
		self.delete_file(self.filename)
		self.filesize = size
		self.wget_thread = threading.Thread(target=self.command, args=(remote_command, ))
		self.update_thread = threading.Thread(target=self.update_progress)
		self.wget_thread.daemon = True
		self.update_thread.daemon = True
		self.wget_thread.start()
		self.update_thread.start()
		self.timestamp = time.time()
		return True

	def update_progress(self):
		while True:
			if self.stop_event.isSet():
				break
			try:
				downloaded_bytes = int(self.command('du -b ' + self.filename + ' | cut -f 1').read())
			except:
				downloaded_bytes = 0
				pass
			if downloaded_bytes == self.filesize:
				self.progress = 100.0
				self.downloaded = True
				self.stop_application()
				self.start_application()
				break					
			else:
				self.progress = downloaded_bytes / float(self.filesize) * 100.0
			time.sleep(0.5)

	def connect(self):
		if not self.connected:
			try:
				self.ssh.connect(hostname = self.credentials['host'], username = self.credentials['username'],
					  			password = self.credentials['password'], port = self.credentials['port'], timeout = 3)
				self.connected = True
			except:
				pass

	def disconnect(self):
		self.ssh.close()
		self.connected = False

	def command(self, command):
		stdin, stdout, stderr = self.ssh.exec_command(command)
		errors = stderr.read()[:-1]
		if errors:
			raise RuntimeError(errors)
		return stdout

	@property
	def elapsed(self):
		timestamp = time.time()
		return timestamp - self.timestamp

	@property
	def estimated(self):
		elapsed = self.elapsed
		try:
			result = elapsed / self.progress * 100.0 - elapsed + 0.5
		except ZeroDivisionError:
			result = 0.0
			pass
		return secs2str(result)