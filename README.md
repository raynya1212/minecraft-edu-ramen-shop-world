# 🍜 ちいかわ 郎 ラーメン Minecraft Education ワールド

Minecraft Education / Bedrock 向けの `.mcworld` を Python で生成するプロジェクトです。白い箱型のラーメン店、食券機、カウンター、NPC 店員とのコール体験、店内外の画像パネル、歴史学習 NPC などを配置した体験型ワールドを作ります。

このプロジェクトは個人制作の非公式ファンプロジェクトです。ちいかわ、ラーメン二郎、Minecraft、Microsoft、Mojang などの公式プロジェクトではありません。

## ✨ 概要

プレイヤーは店に入り、食券販売機でメニューを選び、カウンター奥の NPC 店員をタップして「ニンニク入れますか？」に答えます。正しい二郎系のコールを選ぶとラーメンが提供され、NG コールを選ぶと退店になります。

主な要素:

- Minecraft Education / Bedrock 用 `.mcworld` の自動生成
- Python 3.12 + Amulet によるワールド編集
- Behavior Pack による食券、NPC、コール、ラーメン提供の進行制御
- tryashtar Image Map による画像の地図化と額縁配置
- 歴史案内 NPC による二郎系ラーメン文化のページ式学習コンテンツ
- バニラブロック中心の実装。カスタムブロック、Resource Pack、実験的機能は使いません

## ⚠️ 重要な注意

このリポジトリを公開する場合は、画像や生成済み `.mcworld` に含まれる素材の権利を必ず確認してください。

- この公開用コピーの `build/assets/characters/` には、自作のプレースホルダ画像だけを入れています。
- 本来使いたい画像がある場合は、利用者自身が権利を確認した画像に差し替える前提です。
- 公式キャラクター画像、店舗写真、ロゴ、その他第三者が権利を持つ素材を使う場合は、権利者の許諾や利用条件を確認し、許可のない公開・再配布は避けてください。
- `dist/ChiikawaRamen.mcworld` は生成物です。画像を含めてビルドした場合、その画像データもワールド内に含まれます。
- `tools/ImageMap4-Windows/` に外部ツールや実行ファイルを置く場合は、そのツールの配布条件も確認してください。

## 📦 生成物

- `dist/ChiikawaRamen.mcworld`: Minecraft Education / Bedrock にインポートできる完成ワールド

`dist/` の中身はビルドで再生成できます。ソースから作り直す場合は、次の手順を使ってください。

## 📖 関連ドキュメント

- [AIでMinecraft Educationのワールドを作る考え方](docs/ai-minecraft-education-world-generation.md)

## 🧰 必要環境

- Windows
- Python 3.12
- Minecraft Education または Bedrock 系のワールドを開ける環境
- Python パッケージ:

```powershell
py -3.12 -m pip install amulet-core amulet-leveldb pillow
```

Python 3.13 では Amulet が動かない場合があります。このプロジェクトでは `py -3.12` を使ってください。

## 🛠️ ビルド方法

リポジトリの `chiikawa_ramen/` ディレクトリで実行します。

```powershell
py -3.12 build/new_world.py
```

成功すると `dist/ChiikawaRamen.mcworld` が生成されます。作業用のワールドは OneDrive のファイルロックを避けるため `%TEMP%\chiikawa_ramen_build` に作られ、最後に `.mcworld` だけが `dist/` に出力されます。

## ✅ 検証方法

生成後に、主要なブロック配置、Behavior Pack、NPC ダイアログ、Image Map 額縁、level.dat 設定を確認できます。

```powershell
py -3.12 build/validate_world.py
```

正常な場合は最後に `=== すべて OK ===` と表示されます。

## 🎮 Minecraft Education への取り込み

1. `dist/ChiikawaRamen.mcworld` をダブルクリックするか、Minecraft Education の「遊ぶ」からインポートします。
2. ワールドを開くと店の前の広場にスポーンします。
3. 入口の感圧板を踏んで入店します。
4. 食券機でメニューを選び、NPC 店員をタップしてコールを選びます。

Behavior Pack が動作するため、ワールド設定ではチート/コマンドと Behavior Pack が有効になっている必要があります。生成時の `level.dat` では有効化済みです。

## 🍥 遊び方

1. 入口の鉄ドアを通って入店します。
2. 入口右手の食券販売機で、上から `ミニ ¥1540` / `小 ¥1760` / `大 ¥1980` のいずれかを選びます。
3. カウンターに近づき、奥の NPC 店員をタップします。
4. 「ニンニク入れますか？」のダイアログからコールを選びます。
5. 正しいコールなら `beetroot_soup` が赤いスープのラーメンとして渡されます。
6. NG コールの場合は理由が表示され、店外に戻されます。

コール選択肢:

| 選択肢 | 判定 | 備考 |
| --- | --- | --- |
| そのまま | OK | 追加トッピングなし |
| 替え玉ください | NG | 替え玉は博多ラーメンなどの文化 |
| ニンニク ヤサイ アブラ カラメ | OK | 定番コール |
| 大盛りで！ | NG | このワールドでは「マシ」と区別する罠選択肢 |
| 全マシマシ | OK | 全部増し |
| はい | NG | 返事だけでコールになっていない |

## 📚 歴史学習スポット

店内左手に歴史案内 NPC がいます。壁の年表看板や本置きは置かず、NPC ダイアログだけで読める構成です。

歴史案内 NPC では次のテーマを読めます。

- 年表を読む
- 一杯の特徴
- コール文化
- 広がりを知る
- マナーを学ぶ
- ミニクイズ

長い内容は NPC ダイアログ内の `前へ` / `次へ` / `目次へ` でページ送りできます。ミニクイズは、問題、選択肢、解答ページを分けています。

主な参考資料:

- [ラーメン二郎 - Wikipedia](https://ja.wikipedia.org/wiki/%E3%83%A9%E3%83%BC%E3%83%A1%E3%83%B3%E4%BA%8C%E9%83%8E)
- [Ramen Jiro - Wikipedia](https://en.wikipedia.org/wiki/Ramen_Jiro)
- [The 50 best things to eat in the world, and where to eat them - The Guardian](https://www.theguardian.com/lifeandstyle/2009/sep/13/best-foods-in-the-world)
- [NPC Dialogue Command - Microsoft Learn](https://learn.microsoft.com/en-us/minecraft/creator/documents/npcdialogue)

## 🖼️ 画像パネル

画像は [tryashtar/image-map](https://github.com/tryashtar/image-map) のコマンドライン版で Bedrock の地図データに変換し、額縁に入れて配置します。Resource Pack や実験的機能は使いません。

現在の割り当て:

| 場所 | ファイル名 | map ID |
| --- | --- | --- |
| 左壁 | `ちいかわとはちわれ.*` | `1000`-`1003` |
| 右壁 | `ちいかわとはちわれ_2.*` | `1100`-`1103` |
| キッチン壁 | `シーサーと鎧さん.*` | `2000`-`2003` |
| 店外パネル | `ちいかわラーメン.*` | `3000`-`3003` |

画像を差し替える場合は、`build/assets/characters/` に同じベース名で画像を置いてからビルドしてください。対応拡張子は `.png`、`.jpg`、`.jpeg`、`.webp` です。

Image Map CLI は [tryashtar/image-map](https://github.com/tryashtar/image-map) を参照してください。この公開用コピーには外部実行ファイルを同梱していません。Windows 版を利用する場合は、ダウンロードした `ImageMap-cmd.exe` を次の場所に配置します。

```text
tools/ImageMap4-Windows/ImageMap-cmd.exe
```

外部ツールなしでコードだけを確認したい場合は、`build/lib/image_maps.py` の `import_image_maps(WORK_DIR)` 呼び出しを一時的に外すか、Image Map CLI を配置してからビルドしてください。

## 🧍 NPC の見た目変更

Minecraft Education の NPC の見た目は、公式には NPC 編集画面の `Appearance` から選ぶ方式です。

1. ワールド内で `/gamemode creative` に切り替えます。
2. NPC を右クリックします。
3. `Appearance` の左右矢印から見た目を選びます。
4. ワールドを保存します。

生成処理は既存タグの NPC を消さずに再利用するため、保存済みワールドでは手動変更した外見が残る想定です。生成コードから安定してスキン番号を固定する公式な方法は確認できていません。

## 🧯 トラブルシューティング

### NPC が出ない / 食券機が動かない

- 古いインポート済みワールドを削除し、最新の `dist/ChiikawaRamen.mcworld` を再インポートしてください。
- チャットで `/function jiro/boot` を実行してみてください。
- `Unknown function` と出る場合は、Behavior Pack が有効になっていないか、古いワールドを開いています。

### NPC ダイアログのボタンが反応しない

店員 NPC を直接タップして開いたダイアログで操作してください。Bedrock では、コマンドで強制表示した NPC ダイアログのボタンが期待どおり動かない場合があります。

### 画像が表示されない

- `tools/ImageMap4-Windows/ImageMap-cmd.exe` が存在するか確認してください。
- `build/assets/characters/` に必要な画像ファイルがあるか確認してください。
- ビルドログに `Generated map IDs` が出ているか確認してください。

## 📁 ディレクトリ構成

```text
chiikawa_ramen/
├── README.md
├── design/
│   ├── world.json
│   └── design-notes.md
├── build/
│   ├── new_world.py
│   ├── validate_world.py
│   ├── assets/characters/
│   └── lib/
│       ├── behavior_pack.py
│       ├── building.py
│       ├── consts.py
│       ├── geom.py
│       ├── image_maps.py
│       ├── interior.py
│       ├── packer.py
│       ├── protection.py
│       └── worldgen.py
├── tools/
│   └── ImageMap4-Windows/
└── dist/
    └── ChiikawaRamen.mcworld
```

## 📝 実装メモ

- `build/lib/consts.py`: 座標、メニュー、コール、NPC、歴史コンテンツの定義
- `build/lib/interior.py`: カウンター、食券機、自販機、水コーナー、店内装飾
- `build/lib/behavior_pack.py`: Behavior Pack、mcfunction、NPC ダイアログ生成
- `build/lib/image_maps.py`: Image Map CLI 呼び出しと額縁配置
- `build/lib/worldgen.py`: level.dat、フラットワールド、Education 設定
- `build/validate_world.py`: 生成結果の検証

## 免責

このプロジェクトは教育・学習・個人制作のためのサンプルです。各名称、キャラクター、商標、画像素材の権利はそれぞれの権利者に帰属します。
