---
title: "Minecraft Educationでラーメン屋ワールドを生成してみた"
emoji: "🍜"
type: "tech"
topics: ["minecraft", "minecrafteducation", "python", "bedrock", "amulet"]
published: false
---

Minecraft Education で、ラーメン屋さんを舞台にした `.mcworld` を Python から生成してみました 🍜

食券を買って、店員 NPC に「ニンニク入れますか？」と聞かれて、コールを選ぶとラーメンが出てくるワールドです。

最初は「ちいかわに出てくる郎っぽいラーメン屋さんを作れたら楽しそう」くらいの気持ちだったのですが、作っていくうちに

- Minecraft Education / Bedrock の `.mcworld` の中身
- Behavior Pack で NPC やコマンドを動かす方法
- 壁に画像を貼る方法
- 教育要素として NPC に歴史解説をさせる方法

など、思ったよりいろいろ学びがありました。

この記事では、完成したワールドの紹介と、どうやって作ったかをまとめます。

:::message
このワールドは個人制作の非公式ファンプロジェクトです。
公開用リポジトリでは、第三者が権利を持つ画像の代わりにプレースホルダ画像を使っています。
:::

## つくったもの

今回つくったのは、Minecraft Education / Bedrock で開けるラーメン店ワールドです。

GitHub に公開したリポジトリはこちらです：

https://github.com/raynya1212/minecraft-edu-ramen-shop-world

### 最初の構想

最初に考えていたのは、かなりシンプルでした。

> ちいかわの「郎」っぽいラーメン屋さんに入って、食券を買って、ラーメンを受け取れるワールドを作りたい

という感じです。

外観としては、白い建物、黄色い看板、赤いカウンター、食券機があるお店。
ゲームとしては、入店して、注文して、ラーメンを受け取るくらいの体験を想定していました。

ただ、作っているうちに「せっかく Minecraft Education で作るなら、ただのお店ではなく、ちょっと学べる要素も入れたい」と思い、二郎系ラーメンの歴史やコール文化を学べる NPC も追加しました。

### 完成したもの

最終的には、こんなワールドになりました。

- 入口に自動ドアがあるラーメン店
- 縦型の食券販売機
- NPC 店員とのコール選択
- 正しいコールを選ぶとラーメンが提供されるゲーム性
- 店内外の画像パネル
- 黒烏龍茶の自販機
- 店外に並ぶお客さん NPC
- 歴史案内 NPC によるページ式の解説

スクリーンショットを入れるなら、このあたりがよさそうです。

<!-- TODO: Minecraft Education で撮影した画像を配置して、コメントアウトを外す -->
<!-- ![店の外観](/images/minecraft-edu-ramen-shop-world/ramen-world-exterior.png) -->
<!-- ![食券機](/images/minecraft-edu-ramen-shop-world/ticket-machine.png) -->
<!-- ![NPCダイアログ](/images/minecraft-edu-ramen-shop-world/npc-dialogue.png) -->
<!-- ![歴史案内NPC](/images/minecraft-edu-ramen-shop-world/history-npc.png) -->

:::message
スクリーンショットは Minecraft Education 側で撮影して、`images/minecraft-edu-ramen-shop-world/` に置く想定です。
:::

## どうつくったのか

今回のワールドは、手作業でブロックを置いたのではなく、Python で `.mcworld` を生成しています。

ざっくりした流れはこんな感じです。

```text
1. 空の Bedrock ワールドを作る
2. Amulet でブロックや Block Entity を配置する
3. Behavior Pack を生成する
4. level.dat を Minecraft Education 向けに設定する
5. Image Map で画像を地図データに変換する
6. .mcworld として zip 化する
```

使っている主な技術は以下です。

- Python 3.12
- Amulet
- amulet-leveldb
- Pillow
- tryashtar/image-map
- Minecraft Behavior Pack / mcfunction

ビルドは以下で行います。

```powershell
py -3.12 build/new_world.py
```

検証用のスクリプトも用意しました。

```powershell
py -3.12 build/validate_world.py
```

この検証では、入口、食券機、NPC ダイアログ、Image Map の額縁、Behavior Pack、level.dat の設定などをざっくり確認しています。

## Minecraft Education / Bedrock の `.mcworld` 構造

`.mcworld` は、ざっくり言うと Bedrock ワールドを zip にしたものです。

中には、たとえば以下のようなファイルやディレクトリが入ります。

```text
ChiikawaRamenWorld/
├── level.dat
├── db/
├── levelname.txt
├── behavior_packs/
│   └── chiikawa_jiro_bp/
├── world_behavior_packs.json
└── world_behavior_pack_history.json
```

今回とくに大事だったのは、以下の3つです。

### level.dat

ワールドの基本設定が入っています。

今回は Minecraft Education で遊べるように、コマンドや Education Features を有効にしています。
また、ゲームモードはアドベンチャーにして、展示が壊れにくいようにしました。

### db/

ブロック配置などのワールド本体データが入っています。
Amulet を使って、この中の LevelDB を編集しています。

### behavior_packs/

NPC やコマンドの動きを入れるところです。
今回は `chiikawa_jiro_bp` という Behavior Pack を生成しています。

中には、たとえば以下があります。

```text
behavior_packs/chiikawa_jiro_bp/
├── manifest.json
├── functions/
│   ├── tick.json
│   └── jiro/
│       ├── main.mcfunction
│       ├── boot.mcfunction
│       ├── order_mini.mcfunction
│       ├── order_small.mcfunction
│       ├── order_large.mcfunction
│       └── serve.mcfunction
└── dialogue/
    └── jiro_call.json
```

`mcfunction` と NPC ダイアログを組み合わせて、食券購入からコール、ラーメン提供までの流れを作っています。

## 工夫したこと

### ゲーム性をどう入れるか

Minecraft の中で「注文ゲーム」っぽくするために、状態をスコアボードで管理しました。

`jiro_state` というスコアを使って、プレイヤーごとの状態を持たせています。

```text
0 = 店外
1 = 食券購入済
3 = コール中
5 = 提供済
```

食券機を押すと、たとえば `order_small.mcfunction` が動きます。

```mcfunction
function jiro/boot
scoreboard players set @s jiro_state 3
scoreboard players set @s jiro_menu 2
title @s subtitle ラーメン豚 小 ¥1760（ハチワレ）
title @s title 食券を買った！
give @s paper 1
```

そのあと NPC 店員をタップして、コールのダイアログを開きます。

正解のコールなら `serve`、NG のコールなら `fail` へ進む、という流れです。

### 食券機のボタンが意外とむずかしい

最初は食券機のボタンを横に3つ並べていました。

ただ、実機で試すと「見た目では大を押しているつもりなのに、小が選ばれる」ようなズレが起きました。

そこで、上・中・下の縦配置に変更しました。
さらに、コマンドブロック同士が隣接しているとレッドストーン信号で複数の注文が走る可能性があったので、ボタン段を1ブロックずつ離しています。

こういうところは、実際に Minecraft Education で触ってみないと気づきにくかったです。

### NPC ダイアログを使ったコール

NPC ダイアログは、`dialogue/jiro_call.json` にシーンを定義して、NPC に割り当てています。

```json
{
  "scene_tag": "jiro_call",
  "npc_name": "郎の店主",
  "text": "ニンニク入れますか？",
  "buttons": [
    {
      "name": "そのまま",
      "commands": [
        "/execute as @initiator if score @s jiro_state matches 3 run function jiro/call1"
      ]
    }
  ]
}
```

ここで大事だったのが `@initiator` です。
NPC をタップしたプレイヤー自身に対してコマンドを実行できます。

ただし、NPC ダイアログは `/dialogue open` で強制的に開いた場合と、プレイヤーが直接 NPC をタップして開いた場合で挙動に差がありました。
このワールドでは、NPC に `dialogue change` でシーンを割り当てておき、プレイヤーが直接タップする方式にしています。

### 画像の挿入方法: Image Map

最初は、画像をカスタムブロックや Resource Pack で表現しようとしていました。

でも Minecraft Education では、実験的機能やカスタムブロックを使うと Behavior Pack 全体が読み込まれないことがありました。
結果として、NPC も食券機も画像も全部動かない、という状態になりました。つらい。

そこで、画像は [tryashtar/image-map](https://github.com/tryashtar/image-map) を使い、Bedrock の地図データとして取り込む方式にしました。

2×2 の地図に分割して、額縁に入れて壁に配置しています。

```python
def set_filled_map_frame(self, x, y, z, map_id, facing_direction, rotation=0):
    # frame + ItemFrame BlockEntity に filled_map を入れる
```

この方式だと Resource Pack も実験的機能も不要です。
Minecraft Education で安定しやすい構成になりました。

### 歴史解説 NPC

ただのラーメン屋さんワールドだと遊んで終わりなので、教育要素として歴史解説 NPC も入れました。

歴史案内 NPC では、以下のテーマを読めます。

- 年表を読む
- 一杯の特徴
- コール文化
- 広がりを知る
- マナーを学ぶ
- ミニクイズ

長文を看板に書くと店内がごちゃごちゃしてしまうので、最終的には NPC ダイアログだけに集約しました。

ページ送りは、NPC ダイアログのボタンから次のシーンを開く形です。

```json
{
  "name": "次へ",
  "commands": [
    "/dialogue open @e[type=npc,tag=jiro_history,c=1] @initiator jiro_history_timeline_2"
  ]
}
```

ミニクイズも、最初は Q と A が同時に表示されてしまっていたのですが、問題 → 選択肢 → 解答ページ、という形に直しました。

## 今回の学び

今回やってみて、いちばん大きかった学びは「Minecraft Education では安定性をかなり優先したほうがよい」ということでした。

### カスタムブロックは魅力的だけど、教育版では慎重に

カスタムブロックや Resource Pack を使うと、表現力はかなり上がります。

ただ、Minecraft Education では実験的機能まわりの相性があり、Behavior Pack 全体が読まれなくなることがありました。

今回のように、NPC や食券機などのゲーム進行を Behavior Pack に頼っている場合、BP が読まれないと体験全体が止まってしまいます。

なので最終的には、バニラブロック + Behavior Pack + Image Map という構成に落ち着きました。

### 実機で触らないとわからないことが多い

検証スクリプトではOKでも、実際に Minecraft Education で触ると「ボタンとラベルがズレて見える」「NPC がそっぽを向いている」「店内がごちゃごちゃしている」など、体験として気になる点が出てきました。

ワールド生成はコードでできますが、最後はやっぱりプレイヤー目線で歩いてみるのが大事ですね。

### `.mcworld` は思ったよりプログラムで作れる

`.mcworld` は最初、もっとブラックボックスなものかと思っていました。

でも実際には、Bedrock のワールドデータ、Behavior Pack、level.dat、地図データを組み合わせることで、かなりいろいろ作れます。

もちろんハマりどころは多いですが、Python で座標や構造を管理しながら作れるのは楽しかったです。

## おわりに

Minecraft Education のワールドを Python で生成するの、思った以上におもしろかったです。

ふつうにブロックを置くだけでなく、NPC ダイアログ、スコアボード、mcfunction、地図データなどを組み合わせると、ちょっとした体験型教材みたいなものも作れます。

今回はラーメン屋さんでしたが、同じ仕組みで

- 博物館ワールド
- 防災学習ワールド
- 英会話 NPC ワールド
- クイズつき校外学習ワールド

みたいなものも作れそうだなと思いました。

ちょこっとでも参考になれば嬉しいです 🍜✨
