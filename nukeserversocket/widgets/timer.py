"""Timer class that deals with the connection timeouts."""
# coding: utf-8

from PySide2.QtCore import QTimer, Signal, QObject


class Timer(QObject):
    """A timer class to deal with the timeout connections time.

    The class will create 2 QTimer objects; one that will deal with the
    "after the timeout" code and one that will send a signal every second to
    update the UI.
    """

    time = Signal(str)

    def __init__(self, timeout, parent=None):
        """Initiate the timer class.

        Args:
            timeout (int): value for the timeout in msec.
        """
        QObject.__init__(self, parent)

        self._initial_timeout = timeout
        self._timeout = timeout

        self._ui_timer = QTimer()
        self._ui_timer.setInterval(1000)
        self._ui_timer.timeout.connect(self._ui_countdown)

        self._timer = QTimer()
        self._timer.setInterval(timeout * 1000)
        self._timer.setSingleShot(True)

    def reset(self):
        """Reset timeout time."""
        self._timeout = self._initial_timeout

    def start(self):
        """Start both timers."""
        self._timer.start()
        self._ui_timer.start()

    def stop(self):
        """Stop both timers and clear the timeout label text."""
        self._timer.stop()
        self._ui_timer.stop()
        self.time.emit('')

    def _ui_countdown(self):
        """Start the countdown for the timeout UI label."""
        self._timeout -= 1

        if self._timeout == 0:
            self.time.emit('')
            self._ui_timer.stop()
            return

        self.time.emit(str(self._timeout))
