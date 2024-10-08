# LiveCompetition7 👋  
対話システムライブコンペ 7の個人用Repository   
元のプロジェクト：https://github.com/remdis/remdis   
対話システムライブコンペ 7について：https://sites.google.com/view/dslc7  

## Roadmap
<table  align="center" width="100%">
<tr>
<td valign="top">

#### Completed
- :sparkles:local_llmの実装
- :sparkles:run.pyを追加
- :rocket:音声対話

</td>
<td valign="top">

#### In Progress
- :sparkles:ASR & TTS のロケーション化
- :ambulance:ズレ問題の解決(重要)

</td>
<td valign="top">

#### Not Started
- :art:記憶メカニズムの改造
- :zap:VAPの改造

</tr></td>

</tr>
</table>

## run.py
ウィンドウを毎回開くのは面倒なので、複数のIMを同時に起動するために run.py を書きました。
具体的にどのプロセスを起動するかは
```
sub = [
    "tin.py",
    "lllm_dialogue.py",
    "tout.py"
]
```
で変更できます
`MMDAgent-EX` の起動文は含まれていますが、コメントアウトを解除する必要があります。

## ロケーション化
Ollama使っています、環境配置に問題がなければ、config内の[Ollama][llm_model]を変えば実行できると思います。  
正しく Ollama のストリームデータを処理するために、`lllm_dialogue.py` と `local_llm` にいくつかの変更を加えましたが、使用方法は配布されているプログラムと変わらないはずです。