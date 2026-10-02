"""Run scheduled email notifications as one standalone production process."""

import os
import signal
import threading

os.environ.setdefault('FLASK_ENV', 'production')

from app import create_app
from app.scheduler import scheduler


def main():
    app = create_app()
    stopped = threading.Event()

    def shutdown(_signum, _frame):
        scheduler.stop()
        stopped.set()

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    scheduler.start()
    stopped.wait()


if __name__ == '__main__':
    main()
