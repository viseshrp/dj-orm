from djorm.contrib.staticfiles.handlers import StaticFilesHandler
from djorm.test import LiveServerTestCase


class StaticLiveServerTestCase(LiveServerTestCase):
    "\n    Extend djorm.test.LiveServerTestCase to transparently overlay at test\n    execution-time the assets provided by the staticfiles app finders. This\n    means you don't need to run collectstatic before or as a part of your tests\n    setup.\n    "

    static_handler = StaticFilesHandler
