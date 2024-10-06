import base64
import queue
import sys
import threading
import time

import cv2
import numpy as np
from base import RemdisModule, RemdisUpdateType
from feat import Detector

STREAMING_LIMIT = 240  # 4 minutes


class VideoProcess(RemdisModule):
    def __init__(self, pub_exchanges=["video_process"], sub_exchanges=["vin"]):
        super().__init__(pub_exchanges=pub_exchanges, sub_exchanges=sub_exchanges)

        self.buff_size = self.config["VideoProcess"]["buff_size"]
        self.video_buffer = queue.Queue()  # 受信用キュー

        self.streaming_config = None
        self.responses = []

        self.video_process_start_time = 0.0
        self.detector = Detector(face_model="faceboxes", emotion_model="resmasknet")
        self.video_init()

        self._is_running = True
        self.resume_video_process = False

        self.emotion_categories = [
            "怒り",
            "嫌悪",
            "恐怖",
            "幸福",
            "悲しみ",
            "驚き",
            "中立",
        ]
        self.RIGHT_LEFT_THRESHOLD = 30  # 左右の向きのしきい値
        self.NOD_THRESHOLD = 20  # うなずきのしきい値
        self.TILT_THRESHOLD = 15  # 首をかしげるしきい値

    def run(self):
        # メッセージ受信スレッド
        t1 = threading.Thread(target=self.listen_loop)
        # 動画像処理・メッセージ送信スレッド
        t2 = threading.Thread(target=self.produce_predictions_loop)

        # スレッド実行
        t1.start()
        t2.start()

    def listen_loop(self):
        self.subscribe("vin", self.callback)

    def produce_predictions_loop(self):
        while self._is_running:
            if self.resume_video_process:
                sys.stderr.write("Resume: VideoProcess\n")
                self.video_init()
            for content in self._generator():
                response = self.process(self.streaming_config, content)
                p = self._extract_results(response)
                if not p:
                    continue
                output_iu = self.createIU_Video(p)
                self.printIU(output_iu)
                self.publish(output_iu, "video_process")

    # 動画像処理モジュール用のIU作成関数
    def createIU_Video(self, video_process_result):
        iu = self.createIU(video_process_result, "video_process", RemdisUpdateType.ADD)
        return iu

    def process(self, streaming_config, content):
        # ここに動画像処理モデルを入れる想定
        content = np.frombuffer(content, dtype=np.uint8)
        content = cv2.imdecode(content, cv2.IMREAD_COLOR)
        detected_faces = self.detector.detect_faces(content)
        detected_landmarks = self.detector.detect_landmarks(content, detected_faces)
        detected_emotions = self.detector.detect_emotions(
            content, detected_faces, detected_landmarks
        )
        detected_faceposes = self.detector.detect_facepose(content, detected_landmarks)
        try:
            emotion = self.emotion_categories[np.argmax(detected_emotions[0])]
            facepose_values = detected_faceposes["poses"][0][0]
            if facepose_values[2] > self.RIGHT_LEFT_THRESHOLD:
                facepose = "右向き"
            elif facepose_values[2] < -self.RIGHT_LEFT_THRESHOLD:
                facepose = "左向き"
            elif facepose_values[0] < -self.NOD_THRESHOLD:
                facepose = "うなずき"
            elif abs(facepose_values[1]) > self.TILT_THRESHOLD:
                facepose = "首をかしげる"
            else:
                facepose = "正面"
            return [emotion, facepose]
        except Exception as e:  # No face detected
            print(f"[VIDEO_PROCESS] Error: {e}")
            return [None, None]

    # バッファに溜まった画像を結合し返却するgenerator
    def _generator(self):
        while self._is_running:
            # 処理がタイムアウトしそうな場合は再起動
            current_time = time.time()
            proc_time = current_time - self.video_process_start_time
            if proc_time >= STREAMING_LIMIT:
                self.resume_video_process = True
                break

            # 最初のデータの取得
            chunk = self.video_buffer.get()
            # 何も送られていなければ処理を終了
            if chunk is None:
                return
            data = chunk

            # データがバッファに残っていれば全て取得
            while True:
                try:
                    chunk = self.video_buffer.get(block=False)
                    if chunk is None:
                        return
                    data = chunk  # 最後の画像のみを抽出
                except queue.Empty:
                    break

            # キューに貯められた最新の画像のみを返す
            yield data

    # 処理結果のPostProcessing
    def _extract_results(self, response):
        return response

    def video_init(self):
        sys.stderr.write("Start: VideoProcess Module\n")
        self.video_process_start_time = time.time()
        self.resume_video_process = False
        self.detector = Detector(face_model="faceboxes", emotion_model="resmasknet")

    # メッセージ受信用コールバック関数
    def callback(self, ch, method, properties, in_msg):
        in_msg = self.parse_msg(in_msg)
        self.video_buffer.put(base64.b64decode(in_msg["body"].encode()))


def main():
    video_process = VideoProcess()
    video_process.run()


if __name__ == "__main__":
    main()
