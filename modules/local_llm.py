
import json
import time
import re
import yaml
import requests

from base import MMDAgentEXLabel


class ResponseGenerator:
    def __init__(self, config, asr_timestamp, query, dialogue_history, prompts):
        # 設定の読み込み
        self.max_tokens = config['Ollama']['max_tokens']
        self.max_message_num_in_context = config['Ollama']['max_message_num_in_context']
        self.local_model_url = config['Ollama']['ollama_url']
        self.model_name = config['Ollama']['llm_model']

        # 処理対象のユーザ発話に関する情報
        self.asr_timestamp = asr_timestamp
        self.query = query
        self.dialogue_history = dialogue_history
        self.prompts = prompts

        # 生成中の応答を保持・パースする変数
        self.response_fragment = ''
        self.punctuation_pattern = re.compile('[、。！？]')

        # ChatGPTに入力する対話文脈
        messages = []

        # 過去の対話履歴を対話文脈に追加
        i = max(0, len(self.dialogue_history) - self.max_message_num_in_context)
        messages.extend(self.dialogue_history[i:])

        # プロンプトおよび新しいユーザ発話を対話文脈に追加
        if query:
            messages.extend([
                {'role': 'user', 'content': self.prompts['RESP']},
                {'role': 'system', 'content': "OK"},
                {'role': 'user', 'content': query}
            ])
        # 新しいユーザ発話が存在せず自ら発話する場合のプロンプトを対話文脈に追加
        else:
            messages.extend([
                {'role': 'user', 'content': prompts['TO']}
            ])

        self.log(f"Call ChatGPT: {query=}")

        # ChatGPTに対話文脈を入力してストリーミング形式で応答の生成を開始
        self.response = requests.post(
            self.local_model_url,
            json={
                "model": self.model_name,
                "max_tokens": self.max_tokens,
                "messages": messages
            },
            stream=True
        )
        self.response.raise_for_status()
        self.response_lines = self.response.iter_lines()

    # Dialogueのsend_response関数で呼び出され，応答の断片を順次返す
    def __next__(self):
        # 引数（例: '1_喜び,6_会釈'）をパースして，expressionとactionを取得
        def _parse_split(split):
            expression = MMDAgentEXLabel.id2expression[0]
            action = MMDAgentEXLabel.id2action[0]

            # expression/actionを取得
            if "," in split:
                expression, action = split.split(",", 1)

                expression = expression.split("_")[0]
                expression = int(expression) if expression.isdigit() else 0
                expression = MMDAgentEXLabel.id2expression[expression]

                action = action.split("_")[0]
                action = int(action) if action.isdigit() else 0
                action = MMDAgentEXLabel.id2action[action]

            return {
                "expression": expression,
                "action": action
            }

        # Ollamaの応答を順次パースして返す,参考：https://tedboy.github.io/requests/adv13.html
        for line in self.response_lines:
            chunk_message = json.loads(line).get('message')

            if chunk_message.get('content'):
                new_token = chunk_message['content']
                # print(f"[DEBUG] new_token: {new_token}")

                # 応答の断片を追加
                if new_token != "/":
                    self.response_fragment += new_token

                # 句読点で応答を分割
                splits = self.punctuation_pattern.split(self.response_fragment, 1)
                # print(f"[DEBUG] splits: {splits}")

                # 次のループのために残りの断片を保持
                self.response_fragment = splits[-1]
                # print(f"[DEBUG] self.response_fragment: {self.response_fragment}")

                # 句読点が存在していた場合は1つ目の断片を返す
                if len(splits) == 2 or new_token == "/":
                    if splits[0]:
                        # print("phrase:", splits[0])  
                        return {"phrase": splits[0]}

                # 応答の最後が来た場合は残りの断片を返す
                if new_token == "/":
                    if self.response_fragment:
                        return {"phrase": self.response_fragment}
                    self.response_fragment = ''
            else:
                # ChatGPTの応答が完了した場合は残りの断片をパースして返す
                if self.response_fragment:
                    return _parse_split(self.response_fragment)
        raise StopIteration

    # ResponseGeneratorをイテレータ化
    def __iter__(self):
        return self

    # デバッグ用のログ出力
    def log(self, *args, **kwargs):
        print(f"[{time.time():.5f}]", *args, flush=True, **kwargs)


class ResponseChatGPT():
    def __init__(self, config, prompts):
        self.config = config
        self.prompts = prompts
        
        # 入力されたユーザ発話に関する情報を保持する変数
        self.user_utterance = ''
        self.response = ''
        self.last_asr_iu_id = ''
        self.asr_time = 0.0
    
    # ChatGPTの呼び出しを開始
    def run(self, asr_timestamp, user_utterance, dialogue_history, last_asr_iu_id, parent_llm_buffer):
        self.user_utterance = user_utterance
        self.last_asr_iu_id = last_asr_iu_id
        self.asr_time = asr_timestamp

        # ChataGPTを呼び出して応答の生成を開始
        self.response = ResponseGenerator(self.config, asr_timestamp, user_utterance, dialogue_history, self.prompts)
        # print(f"[DEBUG] self information: {vars(self.response)}")
        #for part in self.response :
        #    self.response.log(part)
        # 自身をDialogueモジュールが持つLLMバッファに追加
        parent_llm_buffer.put(self)


if __name__ == "__main__":

    config_file_path = '../config/config.yaml'
    with open(config_file_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    asr_timestamp = time.time()
    query = '今日は良い天気だね'
    dialogue_history = []
    prompts = {}

    with open('./prompt/response.txt', encoding="utf-8") as f:
        prompts['RESP'] = f.read()

    response_generator = ResponseGenerator(config, asr_timestamp, query, dialogue_history, prompts)
    
    for part in response_generator:
        response_generator.log(part)
