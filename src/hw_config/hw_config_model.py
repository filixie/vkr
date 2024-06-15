import os
import os.path

from PyQt5.QtCore import QObject, pyqtSignal


class ComponentCategory:
	SYSTEM_UNIT = 'systemUnit'
	MONITOR = 'monitor'
	KEYBOARD = 'keyboard'
	MOUSE = 'mouse'

	def __new__(cls, *args, **kwargs):
		raise TypeError(f"Non-instantiable type '{cls}'")


class HardwareConfigModel(QObject):
	coherenceGained = pyqtSignal()
	coherenceLost = pyqtSignal()

	def __init__(self, parent=None, file_path=None, file_format=None, components=None, **props):
		super().__init__(parent, **props)

		self._coherent = True
		self._file_format = file_format
		self._working_dir = os.path.dirname(file_path) if file_path else os.getcwd()
		self._file_name = os.path.basename(file_path) if file_path else ''
		self._components = components or dict()

	def isCoherent(self):
		return self._coherent

	def fileFormat(self):
		return self._file_format

	def fileName(self):
		return self._file_name

	def filePath(self):
		return os.path.join(self._working_dir, self._file_name)

	def setFile(self, file_path, file_format=None):
		assert os.path.isabs(file_path)
		file_format = file_format or self._file_format
		working_dir, file_name = os.path.split(file_path)
		if file_format != self._file_format or working_dir != self._working_dir or file_name != self._file_name:
			self._file_format = file_format
			self._working_dir = working_dir
			self._file_name = file_name
			self.touch()

	def component(self, category):
		return self._components.get(category)

	def setComponent(self, category, component):
		if component != self._components.get(category):
			if component:
				self._components[category] = component
			else:
				del self._components[category]
			self.touch()

	def touch(self):
		if self._coherent:
			self._coherent = False
			self.coherenceLost.emit()

	def save(self):
		self._file_format.write(self.filePath(), self._components)
		if not self._coherent:
			self._coherent = True
			self.coherenceGained.emit()

	# TODO: Add `file_format` parameter
	@classmethod
	def load(cls, file_path, file_format):
		if not os.path.exists(file_path):
			raise IOError(f"'{file_path}' does not exist")
		components = file_format.read(file_path)
		return cls(None, file_path, file_format, components)
