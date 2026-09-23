# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright 2025 Zoey Ahmed

import logging
import sys

from gi.events import GLibEventLoopPolicy

from .application import Application
from .config import APP_ID

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(name)s/%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

app = Application(application_id=APP_ID)
with GLibEventLoopPolicy():
    raise SystemExit(app.run(sys.argv))
