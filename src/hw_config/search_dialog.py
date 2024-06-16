
from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtWidgets import QDialog, QApplication, QGridLayout, QLineEdit, QLabel, QPushButton, QTableView, \
	QTableWidget, QTableWidgetItem, QDialogButtonBox

__all__ = ['SearchDialog']


def _fetch_goods_from_registry(how_many):
	req_json = {
		'opt': {
			'sort': None,
			'requireTotalCount': True,
			'searchOperation': "contains",
			'searchValue': None,
			'skip': 0,
			'take': how_many,
			'userData': {}
		}
	}

	import requests
	resp = requests.post('https://gisp.gov.ru/pp719v2/pub/prod/rep/b/', json=req_json)
	return resp.json() if resp.ok else None


def _fetch_goods_from_file(file_name):
	import io
	import json
	with io.open(file_name, 'rt', encoding='utf-8') as file:
		data = json.load(file)
	# record_count = data['total_count']
	return data


class SearchDialog(QObject):
	def __init__(self, parent=None, **props):
		super().__init__(parent, **props)

		dialog = QDialog(parent, windowTitle="Поиск в РЭП")
		layout = QGridLayout()

		search_box = QLineEdit()
		search_box_label = QLabel("Искать:")
		search_box_label.setBuddy(search_box)
		search_button = QPushButton("Поиск", clicked=self._updateFilter)
		self._search_box = search_box
		layout.addWidget(search_box_label, 0, 0)
		layout.addWidget(search_box, 0, 1)
		layout.addWidget(search_button, 0, 2)

		columns = [
			# 'gisp_url',
			# 'product_gisp_url',
			# 'org_name',
			# 'org_ogrn',
			'product_reg_number',
			# 'product_reg_number_2022',
			# 'product_reg_number_2023',
			# 'product_writeout_url',
			'product_name',
			# 'product_okpd2',
			# 'product_tnved',
			# 'product_spec',
			# 'product_score_value',
			# 'product_score_desc',
			# 'product_electronic_product_level',
		]
		search_result_table = QTableWidget(columnCount=len(columns))
		search_result_table.setHorizontalHeaderLabels(columns)
		search_result_table.setSelectionBehavior(QTableView.SelectRows)
		search_result_table.setSelectionMode(QTableView.SingleSelection)
		self._fillResultTable(search_result_table, columns)
		self._search_result_table = search_result_table
		layout.addWidget(search_result_table, 1, 0, 1, 3)

		button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
			accepted=dialog.accept,
			rejected=dialog.reject,
		)
		layout.addWidget(button_box, 2, 0, 1, 3)

		dialog.setLayout(layout)
		self._dialog = dialog

	def _fillResultTable(self, table: QTableWidget, fields):
		data = _fetch_goods_from_file('goods.json')
		records = data['items']

		table.setRowCount(len(records))
		for i, record in enumerate(records):
			for k, field in enumerate(fields):
				item = record[field]
				if item is not None:
					table.setItem(i, k, QTableWidgetItem(str(item)))

	@pyqtSlot()
	def _updateFilter(self):
		null_item = QTableWidgetItem("")
		query = self._search_box.text().casefold()
		table = self._search_result_table
		for i in range(table.rowCount()):
			item = table.item(i, 1) or null_item
			table.setRowHidden(i, query not in item.text().casefold())

	def show(self):
		self._dialog.show()

	def exec(self) -> QDialog.DialogCode:
		return self._dialog.exec()


if __name__ == '__main__':
	import sys
	app = QApplication(sys.argv)
	wnd = SearchDialog()
	wnd.show()
	app.exec()
