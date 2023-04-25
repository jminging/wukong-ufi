import signal
import threading
import time
from multiprocessing import Process

from snowboy import snowboydecoder
from robot import config, logging, utils, constants

logger = logging.getLogger(__name__)

detector = None
recorder = None
porcupine = None


def pipeThread():
    print("watcher")


def detectorThread():
    print("detectorThread")


class DetectorProcess(Process):
    def __init__(self, wukong, config):
        Process.__init__(self)
        self.name = 'detectorProcess'
        self.is_stop = False
        self._reload(config)
        self.wukong = wukong
        self.detector = None
    
    def _reload(self, config):
        self.hotword = config.get("hotword", "wukong.pmdl")
        self.sensitivity = config.get("sensitivity", 0.5)
        self.silent_count_threshold=config.get("silent_threshold", 15)
        self.recording_timeout=config.get("recording_timeout", 5) * 4
        logger.info("离线唤醒配置加载成功")
    
    def run(self):
        # thread1 = threading.Thread(target=pipeThread)
        # thread2 = threading.Thread(target=detectorThread)
        # thread1.start()
        # thread2.start()
        signal.signal(signal.SIGTERM, self.signal_handler)

        """
            初始化离线唤醒热词监听器，支持 snowboy 和 porcupine 两大引擎
            """
        # global porcupine, recorder, detector

        logger.info("使用 snowboy 进行离线唤醒")
        self.detector and self.detector.terminate()
        models = constants.getHotwordModel(config.get("hotword", "wukong.pmdl"))
        self.detector = snowboydecoder.HotwordDetector(
            models, sensitivity=config.get("sensitivity", 0.5)
        )
        # main loop
        try:
            callbacks = self.wukong.detected_callback
            self.detector.start(
                detected_callback = callbacks,
                audio_recorder_callback = self._wukong.conversation.converse,
                interrupt_check = self._wukong.interrupt_callback,
                silent_count_threshold = self.silent_count_threshold,
                recording_timeout = self.recording_timeout,
                sleep_time=0.03,
            )
            self.detector.terminate()
        except Exception as e:
            logger.critical(f"离线唤醒机制初始化失败：{e}", stack_info=True)

    def signal_handler(self):
        self.detector and self.detector.terminate()

