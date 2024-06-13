import sys
from typing import Dict

from frozendict import frozendict

from PyQt5.Qt import QApplication
from PyQt5.QtCore import QTranslator, QLibraryInfo, QLocale

from common import finalize
from hw_config_controller import HardwareConfigController

__all__ = ['main', 'manifest', 'HardwareConfigController']


qt_translation_dir = QLibraryInfo.location(QLibraryInfo.TranslationsPath)

manifest = frozendict(
	applicationName="Конфигуратор АРМ",
	applicationVersion="1.0",
	organizationName="Александра Хетцер",
	# organizationDomain="",
)


@finalize(dict)
def loadTranslations(directory, *files) -> Dict[str, QTranslator]:
	locale = QLocale('ru')
	for file in files:
		tran = QTranslator()
		if tran.load(locale, file, '_', directory):
			yield file, tran


def main():
	app = QApplication(sys.argv, **manifest)
	app.setApplicationDisplayName(manifest['applicationName'])
	trans = loadTranslations(qt_translation_dir, 'qtbase')
	for tran in trans.values():
		app.installTranslator(tran)
		tran.setParent(app)
	wnd = HardwareConfigController()
	wnd.show()
	app.exec()


if __name__ == '__main__':
	main()
