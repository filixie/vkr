import dataclasses
import functools
from typing import Callable
from dataclasses import dataclass

from PyQt5.QtWidgets import QAction

__all__ = ['finalize', 'ActionSet']


@dataclass(frozen=True)
class finalize:
	reducer: Callable

	def __call__(self, f):
		return functools.wraps(f)(
			lambda *args, **kwargs: self.reducer(f(*args, **kwargs))
		)


def _get_action_fields(obj):
	for f in dataclasses.fields(obj):
		if issubclass(f.type, QAction):
			yield f


@dataclass(frozen=True)
class ActionSet:

	@classmethod
	def fresh_(cls, owner=None):
		actions = {f.name: f.type(parent=owner) for f in _get_action_fields(cls)}
		return cls(**actions)

	def __iter__(self):
		yield from (getattr(self, f.name) for f in _get_action_fields(self))
