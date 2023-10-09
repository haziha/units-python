"""
Example: https://doc.qt.io/qtforpython-6/examples/example_async_minimal.html
"""

import asyncio
import typing

from PySide2.QtCore import QEvent, QObject, QCoreApplication

AsyncEventType = QEvent.Type(QEvent.Type.User + 1)  # noqa


class QtAsyncioEvent(QEvent):
    def __init__(self, continue_loop: typing.Callable):
        super().__init__(AsyncEventType)
        self.__continue_loop = continue_loop

    @property
    def continue_loop(self):
        return self.__continue_loop


class QtAsyncioObject(QObject):
    def event(self, event):
        if isinstance(event, QtAsyncioEvent):
            event.continue_loop()
            return True
        return False


class QtAsyncio:
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.__loop = loop
        self.__async_object = QtAsyncioObject()
        self.__sem = 0

    def create_task(self, async_fn: typing.Coroutine):
        self.__sem += 1
        task = self.__loop.create_task(self.__run_async_fn(async_fn))
        self.__next_guest_run_schedule()
        return task

    async def __run_async_fn(self, async_fn: typing.Coroutine):
        try:
            return await async_fn
        finally:
            self.__sem -= 1

    @property
    def loop(self):
        return self.__loop

    def __continue_loop(self):
        self.__loop.call_soon(self.__next_guest_run_schedule)
        self.__loop.run_forever()

    def __next_guest_run_schedule(self):
        self.__loop.stop()
        if self.__sem != 0:
            QCoreApplication.postEvent(self.__async_object, QtAsyncioEvent(self.__continue_loop))


__all__ = [
    "QtAsyncio",
]
