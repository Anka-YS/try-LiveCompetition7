import azure.cognitiveservices.speech as speechsdk
import yaml
import os

config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
with open(config_path, 'r', encoding='utf-8') as file:
    config = yaml.safe_load(file)

# Azure TTS config
api_key = config['TTS']['azure']['api_key']
region = config['TTS']['azure']['region']
voice_name = "ja-JP-NanamiNeural"

# 创建语音配置
speech_config = speechsdk.SpeechConfig(subscription=api_key, region=region)

# 设置语音合成参数
speech_config.speech_synthesis_voice_name = voice_name

# 创建语音合成器
speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)

# 要合成的文本
text_to_speak = "こんにちは、これはAzureの音声合成テストです。"

try:
    # 开始语音合成
    speech_synthesis_result = speech_synthesizer.speak_text_async(text_to_speak).get()

    # 检查合成结果
    if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("Speech synthesis successful。")
    elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_synthesis_result.cancellation_details
        print("Error: {}".format(cancellation_details.error_details))
        print("message: {}".format(cancellation_details.reason))

except Exception as e:
    print("exception occurred: {}".format(e))
