import sys, os
import numpy
import queue
import tempfile

import time

import threading
import base64
import librosa

from ttslearn.pretrained import create_tts_engine
import pyopenjtalk
import azure.cognitiveservices.speech as speechsdk
from base import RemdisModule, RemdisUpdateType

import torch
device = torch.device("cpu")

class TTS(RemdisModule):
    def __init__(self, 
                 pub_exchanges=['tts'],
                 sub_exchanges=['dialogue']):
        super().__init__(pub_exchanges=pub_exchanges,
                         sub_exchanges=sub_exchanges)
        
        self.rate = self.config['TTS']['sample_rate']
        self.frame_length = self.config['TTS']['frame_length']
        self.send_interval = self.config['TTS']['send_interval']
        self.sample_width = self.config['TTS']['sample_width']
        self.chunk_size = round(self.frame_length * self.rate)

        self.input_iu_buffer = queue.Queue()
        self.output_iu_buffer = queue.Queue()
        self.engine_name = self.config['TTS']['engine_name']
        self.model_name = self.config['TTS']['model_name']
        if self.engine_name == 'ttslearn':
            self.engine = create_tts_engine(self.model_name,
                                            device=device)
        elif self.engine_name == 'azure':
            self.speech_config = speechsdk.SpeechConfig(
                subscription=self.config['TTS']['azure']['api_key'],
                region=self.config['TTS']['azure']['region'],
            )
        self.is_revoked = False
        self._is_running = True

    def run(self):
        # 音声合成処理スレッド
        t2 = threading.Thread(target=self.synthesis_loop)
        # メッセージ送信スレッド
        t3 = threading.Thread(target=self.send_loop)
        
        t2.start()
        t3.start()

        t2.join()
        t3.join()

    def send_loop(self):
        # 音声データをチャンクごとに送信
        while True:
            # REVOKEされた場合は送信を停止 (= ユーザ割り込み時の処理)
            if self.is_revoked:
                self.output_iu_buffer = queue.Queue()
                self.send_commitIU('tts')
                
            snd_iu = self.output_iu_buffer.get(block=True)
            self.publish(snd_iu, 'tts')

            # チャンクの間隔ごとに送信を実行(音が切れるので少し早い間隔で送信)
            time.sleep(self.send_interval)

            # システム発話終端まで送信した場合の処理
            if snd_iu['update_type'] == RemdisUpdateType.COMMIT:
                self.send_commitIU('tts')

    def synthesis_loop(self):
        while True:
            output_text = input('>>')
            update_type = RemdisUpdateType.ADD

            x = numpy.array([])
            sr = 0
            sleep_time = 0

            if output_text != '':
                # 音声合成
                if self.engine_name == 'ttslearn':
                    x, sr = self.engine.tts(output_text)
                elif self.engine_name == 'openjtalk':
                    x, sr = pyopenjtalk.tts(output_text, half_tone=-3.0)
                elif self.engine_name == 'azure':
                    with tempfile.NamedTemporaryFile() as temp_file:
                        audio_config = speechsdk.audio.AudioOutputConfig(
                            use_default_speaker=False,
                            filename=temp_file.name,
                        )
                        speech_synthesizer = speechsdk.SpeechSynthesizer(
                            speech_config=self.speech_config,
                            audio_config=audio_config,
                        )
                        voice_name: str = "ja-JP-NanamiNeural"
                        voice_style: str = "chat"
                        ssml_text: str = f"""
                            <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="ja-JP">
                                <voice name="{voice_name}">
                                    <mstts:express-as style="{voice_style}" styledegree="2">
                                        {output_text}
                                    </mstts:express-as>
                                </voice>
                            </speak>
                        """
                        speech_synthesis_result = speech_synthesizer.speak_ssml_async(ssml=ssml_text).get()
                        if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                            x, sr = librosa.load(temp_file.name, sr=self.rate)
                            x = (x * 32767).astype(numpy.int16)
                        elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
                            cancellation_details = speech_synthesis_result.cancellation_details
                            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                                if cancellation_details.error_details:
                                    print("Error details: {}".format(cancellation_details.error_details))
                                    print("Did you set the speech resource key and region values?")
                else:
                    sys.stderr.write('Currently, ttslearn, openjtalk, and azure are acceptable as a tts engine.')

                # MMDAgent-EXの仕様に合わせて音声をダウンサンプリング
                x = librosa.resample(x.astype(numpy.float32),
                                     orig_sr=sr,
                                     target_sr=self.rate)
                
                # チャンクに分割して出力バッファに格納
                t = 0
                while t <= len(x):
                    chunk = x[t:t+self.chunk_size]
                    chunk = base64.b64encode(chunk.astype(numpy.int16).tobytes()).decode('utf-8')
                    snd_iu = self.createIU(chunk, 'tts',
                                           update_type)
                    snd_iu['data_type'] = 'audio'
                    self.output_iu_buffer.put(snd_iu)
                    t += self.chunk_size
            else:
                # テキストがない場合も処理を実施
                x = numpy.zeros(self.chunk_size)
                chunk = base64.b64encode(x.astype(numpy.int16).tobytes()).decode('utf-8')
                snd_iu = self.createIU(chunk, 'tts',
                                       update_type)
                snd_iu['data_type'] = 'audio'
                self.output_iu_buffer.put(snd_iu)

    # 発話終了時のメッセージ送信関数
    def send_commitIU(self, channel):
        snd_iu = self.createIU('', channel,
                               RemdisUpdateType.COMMIT)
        snd_iu['data_type'] = 'audio'
        self.printIU(snd_iu)
        self.publish(snd_iu, channel)


def main():
    tts = TTS()
    tts.run()

if __name__ == '__main__':
    main()
