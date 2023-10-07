def test():
    import asyncio

    from PySide2.QtCore import QTimer
    from PySide2.QtWidgets import QApplication

    from units_python.qt_asyncio import QtAsyncio

    app = QApplication()
    timer = QTimer()
    _run_num = [0, 0]

    def _timeout():
        _run_num[0] += 1

    async def _update_label():
        for _ in range(1 << 10):
            await asyncio.sleep(0)
            _run_num[1] += 1
        app.exit(0)

    timer.timeout.connect(_timeout)  # noqa
    loop = asyncio.new_event_loop()
    qt_asyncio = QtAsyncio(loop)
    qt_asyncio.create_task(_update_label())
    timer.start(0)
    app.exec_()

    assert _run_num[0] != 0
    assert _run_num[1] != 0
