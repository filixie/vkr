import sys

from PyQt5.QtWidgets import QDialog, QApplication, QVBoxLayout, QGridLayout, QLineEdit, QLabel, QProgressBar, \
	QDialogButtonBox


class RefreshDatabaseDialog(QDialog):
	def __init__(self, parent=None, **props):
		super().__init__(parent, windowTitle="Обновление данных", **props)

		self.setLayout(self._createMainForm(self))

	@classmethod
	def _createMainForm(cls, receiver: QDialog):
		layout = QGridLayout()

		editLogin = QLineEdit()
		label = QLabel("Логин:")
		label.setBuddy(editLogin)
		layout.addWidget(label, 0, 0)
		layout.addWidget(editLogin, 0, 1)

		editPassword = QLineEdit(echoMode=QLineEdit.Password)
		label = QLabel("Пароль:")
		label.setBuddy(editPassword)
		layout.addWidget(label, 1, 0)
		layout.addWidget(editPassword, 1, 1)

		progressBar = QProgressBar(minimum=0, maximum=0, textVisible=False)
		progressBar.setToolTip("Идёт обновление")
		layout.addWidget(progressBar, 2, 0, 1, 2)

		buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
		buttonBox.accepted.connect(receiver.accept)
		buttonBox.rejected.connect(receiver.reject)
		layout.addWidget(buttonBox, 3, 0, 1, 2)

		return layout

if __name__ == '__main__':
	app = QApplication(sys.argv)
	wnd = RefreshDatabaseDialog()
	wnd.show()
	app.exec()
