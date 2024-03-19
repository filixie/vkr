import os
import os.path

from PyQt5.QtCore import QObject, pyqtSignal


class HardwareConfigModel(QObject):
	coherenceGained = pyqtSignal()
	coherenceLost = pyqtSignal()

	def __init__(self, parent=None, file_path=None, **props):
		super().__init__(parent, **props)

		self._coherent = True
		self._working_dir = os.path.dirname(file_path) if file_path else os.getcwd()
		self._file_name = os.path.basename(file_path) if file_path else ''

	def isCoherent(self):
		return self._coherent

	def fileName(self):
		return self._file_name

	# TODO (minor): Transform to `pyqtProperty`
	def filePath(self):
		return os.path.join(self._working_dir, self._file_name)

	def setFilePath(self, file_path):
		assert os.path.isabs(file_path)
		working_dir, file_name = os.path.split(file_path)
		if working_dir != self._working_dir or file_name != self._file_name:
			self._working_dir = working_dir
			self._file_name = file_name
			self.touch()

	def touch(self):
		if self._coherent:
			self._coherent = False
			self.coherenceLost.emit()

	def save(self):
		print("SAVE")
		if not self._coherent:
			self._coherent = True
			self.coherenceGained.emit()

	@classmethod
	def load(cls, file_path):
		if not os.path.exists(file_path):
			raise IOError(f"'{file_path}' does not exist")
		print("LOAD")
		return cls(None, file_path)
