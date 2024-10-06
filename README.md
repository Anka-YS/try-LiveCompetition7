<!-- ![Color logo with background](https://github.com/remdis/remdis/assets/15374299/da5eb1c0-b3b4-4056-9c68-99448265e9a4) -->

# [対話システムライブコンペ 7](https://sites.google.com/view/dslc7)配布ソフトウェア

対話システムライブコンペ 7 では，[Remdis](https://github.com/remdis/remdis)をベースとしたシステムを使用します．

## Release Notes

- 2024/09/12 `v0.0.1`の公開
  - TTS を Azure TTS へ変更
  - 動画入力への対応
  - Py-feat を用いた感情認識と顔向き推定

## Remdis: Realtime Multimodal Dialogue System Toolkit とは？

![git_top_remdis](https://github.com/remdis/remdis/assets/15374299/dbc9deab-54b2-4b72-9ef9-06d6fcf38240)

> Remdis はテキスト・音声・マルチモーダル対話システム開発のためのプラットフォームです．

### 特徴

- 非同期処理に基づくモジュールベースの対話システム
- Incremental Units (IU)を単位としたメッセージングと Incremental Modules (IM)による逐次処理
- Large Language Model (ChatGPT)の並列実行・ストリーミング生成による疑似的な逐次応答生成
- Voice Activity Projection (VAP)によるターンテイキング
- MMDAgent-EX との連携によるエージェント対話
- Python 実装，クロスプラットフォーム (Windows/MacOS/Ubuntu)
- マルチモーダル対応 (テキスト対話/音声対話)

## インストール方法

**注意) Windows 環境で実施する場合，WSL はオーディオデバイスとの相性がよくないため，コマンドプロンプトの利用を推奨します．**

### Step 1. 事前準備

Remdis では RabbitMQ の実行に Docker を利用します．Audio VAP で GPU を利用する場合は CUDA Toolkit と CuDNN のインストールが必要です．GPU なしでも実行可能ですが，リアルタイム性は若干低下します．

**安定的な開発環境として，Docker image を整備し，近日公開予定です**

- **Docker Desktop のインストール**
  - MacOS
    ```
    brew install --cask docker
    ```
  - Ubuntu
    - 最新の deb パッケージを DL し，インストール ([こちらのページ](https://docs.docker.jp/desktop/install/ubuntu.html)をご参照ください)
      ```
      sudo apt-get install ./docker-desktop-<version>-<arch>.deb
      ```
  - Windows
    - [Docker docs](https://docs.docker.com/desktop/install/windows-install/)からインストーラをダウンロードし，実行
- **(Optional) CUDA Toolkit/CuDNN のインストール**
  - Windows/Ubuntu は公式ドキュメントを参照し，インストールしてください．
  - Windows でのインストールには下記手順で Visual C++のインストールが必要です．
    - [インストーラ](https://visualstudio.microsoft.com/ja/vs/community/)をダウンロードし，実行
    - 「C++ によるデスクトップ開発」にチェックを入れてインストールを実行

### Step 2. Remdis 本体のインストール

- Clone
  ```
  git clone --recursive https://github.com/p1n0k0/Dialogue_System_Live_Competition_7.git
  cd Dialogue_System_Live_Competition_7
  git submodule init
  git submodule update
  ```
- Install

  ```
  cd Dialogue_System_Live_Competition_7

  # 仮想環境での実行を推奨
  conda create -n remdis python=3.11
  conda activate remdis

  # 依存パッケージのインストール
  pip3 install -r requirements.txt
  ```

### Step 3. 各種 API 鍵の取得と設定

- Google Speech Cloud API の API 鍵を JSON 形式で取得し，config/config.yaml の下記部分にパスを記載
  ```
  ASR:
   ...
   json_key: <enter your API key>
  ```
- OpenAI の API 鍵を取得し，config/config.yaml の下記部分に記載
  ```
  ChatGPT:
    api_key: <enter your API key>
  ```
- Azure TTS の API 鍵を取得し，config/config.yaml の下記部分に記載
  ```
  azure: # This option is only used when "engine_name" is "azure". Otherwise, no setting is required.
    api_key: <enter your azure API key>
    region: <enter your azure region> # <-- japaneast or japanwest
  ```

### Step 4. VAP のインストール

- Clone
  ```
  git clone https://github.com/ErikEkstedt/VAP.git
  ```
- Install

  ```
  # pytorch, torchvision, torchaudioのインストール
  # torchは2.0.1以下 (= pyaudio 2.0.2)でのみ動作
  # インストールコマンドはOSによって若干異なる可能性あり
  pip3 install torch==2.0.1 torchvision torchaudio

  # 本体のインストール
  # Cloneしたディレクトリに移動し，下記を実行
  pip3 install -r requirements.txt
  pip3 install -e .

  # Ekstedsらのrequirementsではtorchsummaryが不足しているため追加でインストール
  pip3 install torchsummary

  # モデルの解凍
  cd models/vap
  unzip sw2japanese_public0.zip
  ```

### Step 5. MMDAgent-EX のインストール (Windows 以外)

- Windows 以外の OS は，[MMDAgent-EX 公式サイト](https://mmdagent-ex.dev/ja/)の[入手とビルド](https://mmdagent-ex.dev/ja/docs/build/) に従って MMDAgent-EX をインストール
- Windows はそのまま次へ（実行バイナリが同梱されているので手順不要）

---

## 利用方法

**注意) IM を実行する際は，個別のプロンプトで実施してください．例えば「3 つの IM を起動」と書かれている場合は，まずプロンプトを 3 つ立ち上げ，それぞれのプロンプトで仮想環境を activate，IM (Python プログラム)を実行という実施手順になります．**

### テキスト対話

- RabbitMQ サーバを実行
  ```
  # Docker Desktopの場合はあらかじめアプリケーションを起動しておく必要あり
  docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3.12-management
  ```
- 仮想環境を activate
  ```
  conda activate remdis
  ```
- 3 つの IM を起動
  ```
  python tin.py
  python dialogue.py
  python tout.py
  ```

### 音声対話

- RabbitMQ サーバを実行
  ```
  # Docker Desktopの場合はあらかじめアプリケーションを起動しておく必要あり
  docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3.12-management
  ```
- 仮想環境を activate
  ```
  conda activate remdis
  ```
- 6 つの IM を起動 (**システム発話が音声認識されないよう，ヘッドセットでの利用を推奨**)
  ```
  # 初回のみVideoProcess・TTSでモデルの読み込みが入ります
  # audio_vap.pyまたはtext_vap.pyを動かさない場合は，ASR終端とTTS終端がターンの交代に用いられます
  python video_process.py
  python input.py
  python audio_vap.py or text_vap.py
  python asr.py
  python dialogue.py
  python tts.py
  python output.py
  ```

### MMDAgent-EX を用いたエージェント対話

- RabbitMQ サーバを実行
  ```
  # Docker Desktopの場合はあらかじめアプリケーションを起動しておく必要あり
  docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3.12-management
  ```
- 仮想環境を activate
  ```
  conda activate remdis
  ```
- 5 つの IM を起動　(**システム発話が音声認識されないよう，ヘッドセットでの利用を推奨**)
  ```
  python video_process.py
  python input.py
  python audio_vap.py or text_vap.py
  python asr.py
  python dialogue.py
  python tts.py
  ```
- MMDAgent-EX を起動
  - Windows: `MMDAgent-EX/run.vbs` を実行
  - WIndows 以外: MMDAgent-EX フォルダにある main.mdf を指定して MMDAgent-EX を実行
    ```
    cd MMDAgent-EX
    /somewhere/MMDAgent-EX/Release/MMDAgent-EX main.mdf
    ``
    ```

## TIPS

### マイクとスピーカーが正しく接続されているか確認したい

- chk_mic_spk.py を実行
  ```
  # 自分の発話がフィードバックされて聴こえていればOK
  python input.py
  python chk_mic_spk.py
  python output.py
  ```

### Audio VAP の出力を可視化したい

- draw_vap_result.py を実行
  ```
  # 音声対話の例
  python input.py
  python audio_vap.py
  python asr.py
  python dialogue.py
  python tts.py
  python output.py
  python draw_vap_result.py
  ```

### 一定時間が経過したらシステム側から話しかけるようにしたい

- time_out.py を実行
  ```
  # テキスト対話の例
  python tin.py
  python dialogue.py
  python tout.py
  python time_out.py
  ```

## 開発可能範囲

### シチュエーショントラック

シチュエーショントラックでは，本ソフトウェアのうち `modules/prompt/response.txt`，`modules/prompt/text_vap.txt`，`modules/prompt/time_out.txt` の 3 ファイルについて自由に書き換えることができます．  
対話戦略へ焦点を当てた評価を実施するために，その他の部分については全チームで共通とさせていただきます．

### タスクトラック

タスクトラックでは，「音声合成に Azure API の `ja-JP-NanamiNeural` を用いる」，「指定の CG アバターを指定のソフトウェアで表示・動作させる（10/10 までに詳細アナウンス予定）」の 2 点を除き自由に開発いただけます．

## 開発時の参考情報

### 入力情報・形式

ユーザの音声と映像から発話文・顔向き・感情を取得します．取得された顔向きと感情は，離散化（顔向き：右向き・左向き・うなずき・首をかしげる・正面，感情：怒り・嫌悪・恐怖・幸福・悲しみ・驚き・中立）され，発話文/感情/顔向きの形で LLM に入力されます．

### CG アバターのモーションについて

現在はプロンプト中に記述されている以下の標準で定義されている感情と動きに対応しています．今後はなるべく早くより多様なモーションに対応する予定です．

感情：平静・喜び・感動・納得・考え中・眠い・ジト目・同情・恥ずかしい・怒り

動き：待機・ユーザの声に気づく・うなずく・首をかしげる・考え中・会釈・お辞儀・片手を振る・両手を振る・見渡す

## ライセンス

### ソースコードの利用規約

本リポジトリに含まれるオリジナルのソースコードは，ライブコンペ 7 にエントリし，本リポジトリへのアクセス権を付与された代表者およびその共同開発者が，ライブコンペ 7 のシステムを開発する際のみにご利用いただけるものとし，利用者以外の第三者に提供、販売、貸与、譲渡、再配布する行為を禁じます．
加えて，他のライセンスがすでに付与されているファイルはそのライセンスにも注意を払ってご利用ください．

### 外部パッケージの利用規約

本ソフトウェアでは，音声認識に[Google Cloud Speech-to-Text API](https://cloud.google.com/speech-to-text?hl=ja)，音声合成に[Azure Text-to-Speech](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/text-to-speech)，対話生成に[OpenAI API](https://openai.com/blog/openai-api)，ターンテイキングに[VAP](https://github.com/ErikEkstedt/VAP.git)，顔画像処理に[Py-feat](https://github.com/cosanlab/py-feat)及び[Py-feat 内のモデル](https://github.com/cosanlab/py-feat?tab=License-1-ov-file)といった外部パッケージを利用します．
ライセンスに関してはそれぞれのパッケージの利用規約をご参照ください．

## References

### Remdis

```
@inproceedings{remdis2024iwsds,
  title={The Remdis toolkit: Building advanced real-time multimodal dialogue systems with incremental processing and large language models},
  author={Chiba, Yuya and Mitsuda, Koh and Lee, Akinobu and Higashinaka, Ryuichiro},
  booktitle={Proc. IWSDS},
  pages={1--6},
  year={2024},
}
```

```
@inproceedings{remdis2023slud,
  title={Remdis: リアルタイムマルチモーダル対話システム構築ツールキット},
  author={千葉祐弥 and 光田航 and 李晃伸 and 東中竜一郎},
  booktitle={人工知能学会 言語・音声理解と対話処理研究会（第99回）},
  pages={25--30},
  year={2023},
}
```

### Audio VAP

```
@inproceedings{vap-sato2024slud,
  title={複数の日本語データセットによる音声活動予測モデルの学習とその評価},
  author={佐藤友紀 and 千葉祐弥 and 東中竜一郎},
  booktitle={人工知能学会 言語・音声理解と対話処理研究会（第100回）},
  pages={192--197},
  year={2024},
}
```
