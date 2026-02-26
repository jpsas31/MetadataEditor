from queue import Queue

from src.youtube import YoutubeLogger


class TestYoutubeLogger:
    def test_initialization(self):
        msg_queue = Queue()
        logger = YoutubeLogger(msg_queue)
        assert logger.message_queue is msg_queue

    def test_debug_puts_message_in_queue(self):
        msg_queue = Queue()
        logger = YoutubeLogger(msg_queue)
        logger.debug("test debug message")
        assert msg_queue.get() == "test debug message"

    def test_warning_puts_message_in_queue(self):
        msg_queue = Queue()
        logger = YoutubeLogger(msg_queue)
        logger.warning("test warning message")
        assert msg_queue.get() == "test warning message"

    def test_error_puts_message_in_queue(self):
        msg_queue = Queue()
        logger = YoutubeLogger(msg_queue)
        logger.error("test error message")
        assert msg_queue.get() == "test error message"

    def test_multiple_messages(self):
        msg_queue = Queue()
        logger = YoutubeLogger(msg_queue)
        logger.debug("msg1")
        logger.warning("msg2")
        logger.error("msg3")
        assert msg_queue.get() == "msg1"
        assert msg_queue.get() == "msg2"
        assert msg_queue.get() == "msg3"
