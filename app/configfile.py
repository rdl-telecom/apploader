from ConfigParser import RawConfigParser, NoOptionError
from config import x6_dst_dir, initial_dir, config_file

class ConfigFile:
	_values = {
		'apploader__initial_dir' : initial_dir,
		'icomera__destination_dir' : x6_dst_dir
	}
	def __init__(self, filename=config_file):
		self._filename = filename
		_parser = RawConfigParser()
		if self.read(_parser):
			for section in _parser.sections():
				for option in _parser.options(section):
					self._values['__'.join((section, option))] = _parser.get(section, option)

	def __del__(self):
		_parser = RawConfigParser()
		self.fill_parser(_parser)
		_parser.write(open(self._filename, 'w'))

	def read(self, parser):
		try:
			parser.readfp(open(self._filename))
		except:
			return False
		return True

	def fill_parser(self, parser):
		for key in self._values.keys():
			[ section, option ] = key.split('__')
			value = self._values[key]
			if section not in parser.sections():
				parser.add_section(section)
			parser.set(section, option, value)

	def __getitem__(self, item):
		return self._values[item]

	def __setitem__(self, item, value):
		self._values[item] = value

if __name__ == '__main__':
	cf = ConfigFile('apploader1.cfg')