import os.path
import traceback
from contextlib import contextmanager
from dataclasses import dataclass
from frozendict import frozendict

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QKeySequence, QCloseEvent
from PyQt5.QtWidgets import QMainWindow, QAction, QMessageBox, QMenuBar, qApp, QFileDialog, QWidget, \
	QComboBox, QVBoxLayout, QLabel

from common import ActionSet
from search_dialog import SearchDialog
from hw_config_file import PlainTextFormat, JsonFormat, HtmlFormat
from refresh_database_dialog import RefreshDatabaseDialog
from hw_config_model import ComponentCategory


class AbstractHardwareConfigController:
	touch = pyqtSlot()
	newConfig = pyqtSlot()
	openConfig = pyqtSlot()
	saveConfig = pyqtSlot()
	saveConfigAs = pyqtSlot()
	refreshDatabase = pyqtSlot()
	findInRegistry = pyqtSlot()
	displayAboutQt = pyqtSlot()
	displayAbout = pyqtSlot()
	close = pyqtSlot()


# TODO: Separate view (`QMainWindow`) from the controller
class HardwareConfigController(QMainWindow, AbstractHardwareConfigController):

	@dataclass(frozen=True)
	class Actions(ActionSet):
		new: QAction
		open: QAction
		save: QAction
		save_as: QAction
		print: QAction
		exit: QAction
		refresh: QAction
		find: QAction
		about: QAction
		about_qt: QAction

	def __init__(self, parent=None, **props):
		super().__init__(parent, **props)


		actions = self.Actions._fresh(self)
		self._initActions(actions, self)
		self.addActions(actions)

		menu_bar = self.menuBar()
		self._initMenuBar(menu_bar, actions)

		self._component_widgets = self._createComponentSelectors(self)
		self.setCentralWidget(self._createMainForm(self._component_widgets))

		self._file_formats = self._createFileFormatList()
		self._file_format = self._file_formats[0]
		self._file_path = None
		self._coherent = None
		self._claimCoherent('')

	@classmethod
	def _createFileFormatList(cls):
		return [
			HtmlFormat("HTML"),
			JsonFormat("JSON"),
			PlainTextFormat("Обычный текст"),
		]

	@classmethod
	def _initActions(cls, actions: Actions, receiver: AbstractHardwareConfigController):
		# TODO (minor): Add icons
		actions.new.pyqtConfigure(text="Созд&ать", shortcut=QKeySequence.New)
		actions.open.pyqtConfigure(text="&Открыть...", shortcut=QKeySequence.Open)
		actions.save.pyqtConfigure(text="&Сохранить", shortcut=QKeySequence.Save)
		actions.save_as.pyqtConfigure(text="&Сохранить как...", shortcut=QKeySequence.SaveAs)
		actions.print.pyqtConfigure(text="&Печать...", shortcut=QKeySequence.Print)
		actions.exit.pyqtConfigure(text="В&ыход")
		actions.refresh.pyqtConfigure(text="Об&новить БД...", shortcut=QKeySequence.Refresh)
		actions.find.pyqtConfigure(text="Найти в &РЭП...")
		actions.about.pyqtConfigure(text="&О программе")
		actions.about_qt.pyqtConfigure(text="&О Qt")

		connections = {
			actions.new:      receiver.newConfig,
			actions.open:     receiver.openConfig,
			actions.save:     receiver.saveConfig,
			actions.save_as:  receiver.saveConfigAs,
			actions.exit:     receiver.close,
			actions.refresh:  receiver.refreshDatabase,
			actions.find:     receiver.findInRegistry,
			actions.about:    receiver.displayAbout,
			actions.about_qt: receiver.displayAboutQt,
		}
		for action, slot in connections.items():
			action.triggered.connect(slot)

	@classmethod
	def _initMenuBar(cls, menu_bar: QMenuBar, actions: Actions):
		file_menu = menu_bar.addMenu("&Файл")
		file_menu.addAction(actions.new)
		file_menu.addAction(actions.open)
		file_menu.addAction(actions.save)
		file_menu.addAction(actions.save_as)
		file_menu.addSeparator()
		file_menu.addAction(actions.print)
		file_menu.addSeparator()
		file_menu.addAction(actions.exit)

		datum_menu = menu_bar.addMenu("&Данные")
		datum_menu.addAction(actions.refresh)
		datum_menu.addAction(actions.find)

		help_menu = menu_bar.addMenu("&Справка")
		help_menu.addAction(actions.about)
		help_menu.addAction(actions.about_qt)

	@classmethod
	def _createComponentSelectors(cls, receiver: AbstractHardwareConfigController):
		from dummy_data import dummy_data

		categories = [
			ComponentCategory.SYSTEM_UNIT,
			ComponentCategory.MONITOR,
			ComponentCategory.KEYBOARD,
			ComponentCategory.MOUSE,
		]
		widgets = list()
		for key in categories:
			combo_box = QComboBox(placeholderText="(не выбрано)")
			combo_box.addItems(dummy_data[key])
			combo_box.currentTextChanged.connect(receiver.touch)
			widgets.append(combo_box)

		return frozendict(zip(categories, widgets))

	@classmethod
	def _createMainForm(cls, component_selectors):
		layout = QVBoxLayout()

		component_names = {
			ComponentCategory.SYSTEM_UNIT: "Системный блок",
			ComponentCategory.MONITOR:     "Монитор",
			ComponentCategory.KEYBOARD:    "Клавиатура",
			ComponentCategory.MOUSE:       "Мышь",
		}
		for key, widget in component_selectors.items():
			layout.addStretch()
			layout.addWidget(QLabel(component_names.get(key) or key))
			layout.addWidget(widget)
			layout.addStretch()

		form = QWidget()
		form.setLayout(layout)
		return form

	@contextmanager
	def _guardExceptions(self):
		errors = list()
		try:
			yield errors
		except Exception as ex:
			errors.append(ex)
			ex_trace = traceback.format_exception(type(ex), ex, ex.__traceback__)
			message_box = QMessageBox(self,
				icon=QMessageBox.Warning,
				text="Произошла чудовищная ошибка!",
				informativeText=str(ex),
				detailedText="".join(ex_trace),
				# windowFlags=Qt.Dialog,  # This should enable resize, but for a bunch of reasons, it doesn't.
			)
			message_box.exec()

	def ensureCoherent(self):
		if self._coherent:
			return True

		question = "Конфигурация была изменена. Хотите сохранить изменения?"
		answer = QMessageBox.question(self, qApp.applicationDisplayName(), question,
			QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
		if answer == QMessageBox.Save:
			return self.saveConfig()
		if answer == QMessageBox.Discard:
			return True
		if answer == QMessageBox.Cancel:
			return False

	def _claimCoherent(self, file_path, file_format=None):
		if file_format:
			self._file_format = file_format
		self._file_path = file_path
		self._coherent = True
		self.setWindowFilePath(os.path.basename(file_path) or "(без имени)")
		self.setWindowModified(False)

	@pyqtSlot()
	def touch(self):
		self._coherent = False
		self.setWindowModified(True)

	@pyqtSlot()
	def newConfig(self):
		if not self.ensureCoherent():
			return False

		self._doLoad('', self._file_format)
		self._claimCoherent('')
		return True

	@pyqtSlot()
	def openConfig(self):
		if not self.ensureCoherent():
			return False

		file_formats = {
			'{name} ({mask})'.format(name=ff.name(), mask=' '.join(f'*.{suf}' for suf in ff.fileSuffixes())): ff
			for ff in self._file_formats if ff.readable()
		}
		file_path, ff_key = QFileDialog.getOpenFileName(self, None, self._file_path, ";;".join(file_formats.keys()))
		file_format = file_formats.get(ff_key)
		if not file_path:
			return False
		with self._guardExceptions() as errors:
			self._doLoad(file_path, file_format)
			self._claimCoherent(file_path, file_format)
		return not errors

	@pyqtSlot()
	def saveConfig(self):
		if not self._file_path:
			return self.saveConfigAs()

		with self._guardExceptions() as errors:
			self._doSave(self._file_path, self._file_format)
			self._claimCoherent()
		return not errors

	@pyqtSlot()
	def saveConfigAs(self):
		file_formats = {
			'{name} ({mask})'.format(name=ff.name(), mask=' '.join(f'*.{suf}' for suf in ff.fileSuffixes())): ff
			for ff in self._file_formats if ff.writable()
		}

		file_path, ff_key = QFileDialog.getSaveFileName(self, None, self._file_path, ';;'.join(file_formats.keys()))
		file_format = file_formats.get(ff_key)
		if not file_path:
			return False

		with self._guardExceptions() as errors:
			self._doSave(file_path, file_format)
			self._claimCoherent(file_path, file_format)
		return not errors

	def _doSave(self, file_path, file_format):
		config = {
			key: widget.currentText()
			for key, widget in self._component_widgets.items()
			if widget.currentIndex() != -1
		}
		file_format.write(file_path, config)

	def _doLoad(self, file_path, file_format):
		config = file_format.read(file_path) if file_path else {}
		for key, widget in self._component_widgets.items():
			if key in config:
				widget.setCurrentText(config[key])
			else:
				widget.setCurrentIndex(-1)

	@pyqtSlot()
	def refreshDatabase(self):
		dialog = RefreshDatabaseDialog(self)
		dialog.exec()

	@pyqtSlot()
	def findInRegistry(self):
		dialog = SearchDialog(self)
		dialog.exec()

	@pyqtSlot()
	def displayAbout(self):
		text = [
			"Система подготовки конфигураций оборудования.",
			"",
			"© {author}, {year}".format(author=qApp.organizationName(), year=2024),
		]
		QMessageBox.about(self, qApp.applicationDisplayName(), "\n".join(text))

	@pyqtSlot()
	def displayAboutQt(self):
		QMessageBox.aboutQt(self)

	def closeEvent(self, ev: QCloseEvent):
		if not self.ensureCoherent():
			ev.ignore()
