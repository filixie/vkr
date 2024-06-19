class ComponentCategory:
	SYSTEM_UNIT = 'systemUnit'
	MONITOR = 'monitor'
	KEYBOARD = 'keyboard'
	MOUSE = 'mouse'

	def __new__(cls, *args, **kwargs):
		raise TypeError(f"Non-instantiable type '{cls}'")
