import io
import json

from hw_config_model import ComponentCategory


class AbstractFileFormat:
	def __init__(self, name):
		self._name = name

	# @property
	def name(self):
		return self._name

	# @name.setter
	def setName(self, name):
		self._name = name

	def fileSuffixes(self):
		pass

	def readable(self):
		return hasattr(self, 'read')

	def writable(self):
		return hasattr(self, 'write')


class PlainTextFormat(AbstractFileFormat):

	def __init__(self, name=None):
		super().__init__(name or "Plain text")

	def fileSuffixes(self):
		return 'txt',

	def write(self, file_name, data):
		with io.open(file_name, 'wt') as file:
			for category, component in data.items():
				file.write(f"{category}: \"{component}\"")


class JsonFormat(AbstractFileFormat):

	def __init__(self, name=None):
		super().__init__(name or "JSON")

	def fileSuffixes(self):
		return 'json',

	def read(self, file_name):
		with io.open(file_name, 'rt', encoding='utf-8') as file:
			return json.load(file)

	def write(self, file_name, data):
		with io.open(file_name, 'wt', encoding='utf-8') as file:
			json.dump(data, file, ensure_ascii=False, indent=4)


class HtmlFormat(AbstractFileFormat):

	# TODO: Refactor with Airium or Yattag
	template = '''
		<!DOCTYPE html>
		<html>
		<head><title>Конфигурация АРМ</title></head>
		<body>
			<h1>Конфигурация АРМ</h1>
			<p>
				<table>
					<tr>
						<th>Компонент</th>
						<th>Наименование</th>
					</tr>
					<tr>
						<td>Системный блок</td>
						<td>{{systemUnit}}</td>
					</tr>
					<tr>
						<td>Монитор</td>
						<td>{{monitor}}</td>
					</tr>
					<tr>
						<td>Клавиатура</td>
						<td>{{keyboard}}</td>
					</tr>
					<tr>
						<td>Мышь</td>
						<td>{{mouse}}</td>
					</tr>
				</table>
			<p>
		</body>
		</html>
	'''

	def __init__(self, name=None):
		super().__init__(name or "HTML")

	def fileSuffixes(self):
		return 'html', 'htm'

	def write(self, file_name, data):
		html = HtmlFormat.template \
			.replace('{{systemUnit}}', data.get(ComponentCategory.SYSTEM_UNIT, "(не выбрано)")) \
			.replace('{{monitor}}', data.get(ComponentCategory.MONITOR, "(не выбрано)")) \
			.replace('{{keyboard}}', data.get(ComponentCategory.KEYBOARD, "(не выбрано)")) \
			.replace('{{mouse}}', data.get(ComponentCategory.MOUSE, "(не выбрано)"))
		with io.open(file_name, 'wt') as file:
			file.write(html)
