import time

import trio
from PySide2.QtWidgets import QMainWindow, QPushButton, QApplication

from units_python.trio_qt import TrioQt


class MainWindow(QMainWindow):
    def __init__(self, nursery: trio.Nursery):
        super().__init__()

        self.nursery = nursery

        self.btn = QPushButton(self, text="test")
        self.btn.clicked.connect(lambda: self.nursery.start_soon(self.__btn_clicked))  # noqa

    async def __btn_clicked(self):
        async def __open_main_window():
            async with trio.open_nursery() as nursery:
                mw = MainWindow(nursery)
                mw.show()
                await trio.sleep_forever()

        self.nursery.start_soon(__open_main_window)

        while True:
            self.btn.setText(str(time.time()))
            await trio.sleep(0)

    def closeEvent(self, event):
        self.nursery.cancel_scope.cancel()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication()
    trio_qt = TrioQt(app)


    async def show():
        async with trio.open_nursery() as nursery:
            main_window = MainWindow(nursery)
            main_window.show()
            await trio.sleep_forever()


    trio_qt.run(show)
