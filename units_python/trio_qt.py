import traceback
import typing

import outcome
import trio.lowlevel
from PySide2.QtCore import QEvent, QObject
from PySide2.QtWidgets import QApplication


class TrioQt:
    TrioQtEventType = QEvent.Type(QEvent.registerEventType())  # noqa

    class TrioQtEvent(QEvent):
        def __init__(self, next_loop: typing.Callable):
            super().__init__(TrioQt.TrioQtEventType)
            self.__next_loop = next_loop

        @property
        def next_loop(self):
            return self.__next_loop

    class TrioQtObject(QObject):
        def event(self, event):
            if isinstance(event, TrioQt.TrioQtEvent):
                event.next_loop()
                return True
            return False

    def __init__(self, app: QApplication):
        self.__trio_qt_object = self.TrioQtObject()

        self.__app = app
        self.__app.setQuitOnLastWindowClosed(False)

    def run(self, entry: typing.Callable[[], typing.Awaitable]):
        trio.lowlevel.start_guest_run(
            entry,
            run_sync_soon_threadsafe=self.__next_loop,
            done_callback=self.__done_callback,
        )
        return self.__app.exec_()

    def __next_loop(self, next_loop: typing.Callable):
        self.__app.postEvent(self.__trio_qt_object, self.TrioQtEvent(next_loop))

    def __done_callback(self, oc: typing.Optional[outcome.Error]):
        self.__app.quit()
        if isinstance(oc, outcome.Error):
            error = oc.error
            traceback.print_exception(type(error), error, error.__traceback__)


_FnType = typing.Callable[[trio.Nursery], typing.Any]

__all__ = [
    "TrioQt",
]
