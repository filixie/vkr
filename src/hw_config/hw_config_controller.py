import traceback
from contextlib import contextmanager
from dataclasses import dataclass

from PyQt5.QtCore import pyqtSlot, QObject
from PyQt5.QtGui import QKeySequence, QCloseEvent
from PyQt5.QtWidgets import QMainWindow, QAction, QMessageBox, QMenuBar, qApp, QFileDialog, QWidget, \
	QComboBox, QVBoxLayout, QLabel

from common import ActionSet
from hw_config_file import PlainTextFormat, JsonFormat, HtmlFormat
from refresh_database_dialog import RefreshDatabaseDialog
from hw_config_model import HardwareConfigModel, ComponentCategory


class AbstractHardwareConfigController:
	newConfig = pyqtSlot()
	openConfig = pyqtSlot()
	saveConfig = pyqtSlot()
	saveConfigAs = pyqtSlot()
	refreshDatabase = pyqtSlot()
	displayAboutQt = pyqtSlot()
	displayAbout = pyqtSlot()
	close = pyqtSlot()

	def model(self) -> HardwareConfigModel: pass


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
		about: QAction
		about_qt: QAction

	def __init__(self, parent=None, model=None, **props):
		super().__init__(parent, **props)

		actions = self.Actions.fresh_(self)
		self._initActions(actions, self)
		self.addActions(actions)

		menu_bar = self.menuBar()
		self._initMenuBar(menu_bar, actions)

		self.setCentralWidget(self._createMainForm(self))

		self._file_formats = self._createFileFormatList()

		self._model = None
		self.setModel(model or self._createModel())

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
		actions.about.pyqtConfigure(text="&О программе")
		actions.about_qt.pyqtConfigure(text="&О Qt")

		connections = {
			actions.new:      receiver.newConfig,
			actions.open:     receiver.openConfig,
			actions.save:     receiver.saveConfig,
			actions.save_as:  receiver.saveConfigAs,
			actions.exit:     receiver.close,
			actions.refresh:  receiver.refreshDatabase,
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

		help_menu = menu_bar.addMenu("&Справка")
		help_menu.addAction(actions.about)
		help_menu.addAction(actions.about_qt)

	@classmethod
	def _createMainForm(cls, receiver: AbstractHardwareConfigController):
		layout = QVBoxLayout()

		from hw_config.dummy_data import dummy_data
		component_categories = {
			ComponentCategory.SYSTEM_UNIT: "Системный блок",
			ComponentCategory.MONITOR:     "Монитор",
			ComponentCategory.KEYBOARD:    "Клавиатура",
			ComponentCategory.MOUSE:       "Мышь",
		}
		for category, label in component_categories.items():
			widget = QComboBox()
			widget.addItems(dummy_data[category])
			widget.setPlaceholderText("(не выбрано)")
			widget.setCurrentIndex(-1)
			widget.currentTextChanged.connect(lambda value, cat=category:
				receiver.model() and receiver.model().setComponent(cat, value))
			layout.addStretch()
			layout.addWidget(QLabel(label))
			layout.addWidget(widget)
			layout.addStretch()

		form = QWidget()
		form.setLayout(layout)
		return form

	@classmethod
	def _createModel(cls, file_format=None, file_path=None):
		if file_format:
			model = HardwareConfigModel.load(file_path, file_format)
		else:
			model = HardwareConfigModel()
		return model

	def model(self):
		return self._model

	def setModel(self, new_model):
		old_model = self._model
		if new_model is not old_model:
			if old_model:
				for conn in self._model_connections:
					QObject.disconnect(conn)
				if old_model.parent() is self:
					old_model.setParent(None)
			self._model = new_model
			self._refreshWindowTitle()
			if new_model:
				self._model_connections = [
					new_model.coherenceGained.connect(self._refreshWindowTitle),
					new_model.coherenceLost.connect(self._refreshWindowTitle),
				]
				if new_model.parent() is None:
					new_model.setParent(self)

	def _refreshWindowTitle(self):
		model = self._model
		if model:
			self.setWindowFilePath(model.fileName() or "(без имени)")
			self.setWindowModified(not model.isCoherent())

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
		model = self._model
		if not model or model.isCoherent():
			return True

		question = "Конфигурация была изменена. Хотите сохранить изменения?"
		answer = QMessageBox.question(self, qApp.applicationDisplayName(), question,
			QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
		if answer == QMessageBox.Save:
			return self.saveConfig()
		if answer == QMessageBox.Discard:
			self.setModel(None)     # FIXME: `Discard -> Cancel opening` sets a null model to non-trivial document
			return True
		if answer == QMessageBox.Cancel:
			return False

	@pyqtSlot()
	def newConfig(self):
		if not self.ensureCoherent():
			return False
		self.setModel(self._createModel())
		return True

	@pyqtSlot()
	def openConfig(self):
		model = self._model
		if not model:
			return True
		if not self.ensureCoherent():
			return False

		file_formats = {
			'{name} ({mask})'.format(name=ff.name(), mask=' '.join(f'*.{suf}' for suf in ff.fileSuffixes())): ff
			for ff in self._file_formats if ff.readable()
		}

		file_path, ff_key = QFileDialog.getOpenFileName(self, None, model.filePath(), ";;".join(file_formats.keys()))
		if not file_path:
			return False
		with self._guardExceptions() as errors:
			QMessageBox.critical(self, "Сорри!", "Пока не доделано")    # TODO
			# file_format = file_formats[ff_key]
			# model = self._createModel(file_format, file_path)
			# self.setModel(model)
		return not errors

	@pyqtSlot()
	def saveConfig(self):
		model = self._model
		if not model:
			return True
		if not model.fileName():
			return self.saveConfigAs()
		with self._guardExceptions() as errors:
			model.save()
		return not errors

	@pyqtSlot()
	def saveConfigAs(self):
		model = self._model
		if not model:
			return True

		file_formats = {
			'{name} ({mask})'.format(name=ff.name(), mask=' '.join(f'*.{suf}' for suf in ff.fileSuffixes())): ff
			for ff in self._file_formats if ff.writable()
		}

		file_path, ff_key = QFileDialog.getSaveFileName(self, None, model.filePath(), ';;'.join(file_formats.keys()))
		if not file_path:
			return False
		with self._guardExceptions() as errors:
			file_format = file_formats[ff_key]
			model.setFile(file_path, file_format)
			model.save()
		return not errors

	@pyqtSlot()
	def refreshDatabase(self):
		dialog = RefreshDatabaseDialog(self)
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
