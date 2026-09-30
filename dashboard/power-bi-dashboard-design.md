# Power BI ダッシュボード設計書

対象:LP・診断アプリのアクセス分析(`analysis/session_data.csv`, `channel_ad_cost.csv`)

---

## 1. 目的

`funnel_analysis.ipynb`で行ったPythonでの分析結果を、**インタラクティブに触って確認できるダッシュボード**として再構築する。用途は2つ。

1. 施策の意思決定者が、期間・チャネルを自分で絞り込みながら状況を確認できるようにする
2. ポートフォリオとして「BIツールの運用ができる」ことを示す

## 2. データモデル

### 2-1. 読み込むテーブル

| テーブル名 | ファイル | 役割 |
|---|---|---|
| `session_data` | `session_data.csv` | ファクトテーブル(1行=1セッション) |
| `channel_ad_cost` | `channel_ad_cost.csv` | チャネル別の広告費(ディメンション兼コストテーブル) |

### 2-2. リレーション

```
session_data[channel]  (多)  ---  (1)  channel_ad_cost[channel]
```

Power BI上で「モデリング」タブから、両テーブルの`channel`列同士をドラッグ&ドロップして接続する(カーディナリティ:多対1、クロスフィルター方向:単一)。

### 2-3. 日付テーブルの追加(推奨)

`session_data`の`visit_date`は文字列またはDate型として読み込まれる。期間スライサーを綺麗に機能させるため、Power BI側で「日付テーブルを自動作成」を有効にするか、`visit_date`の列の型を必ず「日付」に変換しておく。

## 3. 主要メジャー(DAX)

Power BIの「新しいメジャー」で、以下を作成する。

```dax
総セッション数 = COUNTROWS(session_data)

総CV数 = SUM(session_data[conversion])

CVR = DIVIDE([総CV数], [総セッション数], 0)

総広告費 =
CALCULATE(
    SUM(channel_ad_cost[monthly_ad_cost_jpy]),
    ALLEXCEPT(channel_ad_cost, channel_ad_cost[channel])
)

CPA = DIVIDE([総広告費], [総CV数], BLANK())

診断開始率 = DIVIDE(SUM(session_data[diagnostic_started]), SUM(session_data[reached_pain_section]), 0)

診断完了率 = DIVIDE(SUM(session_data[diagnostic_completed]), SUM(session_data[diagnostic_started]), 0)

診断経由CVR =
CALCULATE([CVR], session_data[diagnostic_completed] = 1)

非診断CVR =
CALCULATE([CVR], session_data[diagnostic_completed] = 0)

CTAクリック率 = DIVIDE(SUM(session_data[cta_click]), [総セッション数], 0)
```

`CPA`は`channel_ad_cost`が0円のチャネル(自然検索・紹介)では「BLANK」になる想定(広告費がないため計算不可)。ビジュアル上で0や空欄になっても想定通りの挙動である。

## 4. ページ構成(4ページ構成)

### ページ1:全体サマリー

| ビジュアル | 内容 |
|---|---|
| カード ×4 | 総セッション数 / CVR / 総CV数 / 診断完了率 |
| 折れ線グラフ | 日別のセッション数とCV数の推移(`visit_date`を軸に) |
| スライサー | 期間(`visit_date`)、チャネル(`channel`) |

### ページ2:チャネル分析

| ビジュアル | 内容 |
|---|---|
| 縦棒グラフ | チャネル別セッション数 |
| 縦棒グラフ | チャネル別CVR(%) |
| 縦棒グラフ | チャネル別CPA(円) |
| テーブル | チャネル / セッション数 / CV数 / CVR / CPA を一覧表示 |

### ページ3:ファネル分析

| ビジュアル | 内容 |
|---|---|
| ファネルチャート | LP訪問 → 悩みセクション到達 → 診断開始 → 診断完了 → CTAクリック → CV の6段階 |
| カード | 各ステップの前ステップ比(%)(計算列またはメジャーで算出) |

**ファネルチャート作成のポイント**:Power BIの「ファネル」ビジュアルは、6段階それぞれの合計人数を渡す必要があるため、`session_data`から6行×2列(ステップ名、人数)の小さな集計テーブルを、Power Queryで作成しておくとスムーズ。

### ページ4:診断アプリの効果

| ビジュアル | 内容 |
|---|---|
| ドーナツ or 縦棒グラフ | 診断完了有無別のCVR比較(`診断経由CVR` vs `非診断CVR`) |
| 縦棒グラフ | 診断結果タイプ別(`diagnostic_result_type`)のCTAクリック率・CVR |
| マトリックス | チャネル × 診断完了有無 のCVRクロス表(A-5相当) |
| スライサー | 診断結果タイプ(`diagnostic_result_type`) |

## 5. フィルター・スライサー設計

全ページ共通で使うスライサーは、「フィルター」ペインではなく**各ページ上部にスライサービジュアルとして配置**し、直感的に触れるようにする。

- 期間(`visit_date`):スライダー形式
- チャネル(`channel`):チェックボックス形式(複数選択可)

## 6. デザイン仕様

LP・診断アプリと同じブランドカラーをダッシュボードにも適用する。同梱の`power-bi-theme.json`を、Power BIの「表示」タブ→「テーマ」→「テーマの参照」から読み込むことで、色を一括反映できる。

| 用途 | カラーコード |
|---|---|
| メインカラー(緑) | `#8fae94` |
| メインカラー(濃) | `#4f6b54` |
| 差し色(オレンジ) | `#e2a37b` |
| 背景 | `#fdfcf9` |
| テキスト | `#4a4842` |

## 7. 実装手順

1. Power BI Desktopを開き、「データを取得」→「テキスト/CSV」で`session_data.csv`と`channel_ad_cost.csv`を読み込む
2. 「データの変換」で`visit_date`の型を日付に変更する
3. 「モデリング」タブでリレーションシップを設定する(2-2参照)
4. 「新しいメジャー」で3章のDAXメジューを1つずつ作成する
5. 「表示」→「テーマ」→「テーマの参照」で`power-bi-theme.json`を読み込む
6. ページを4枚追加し、それぞれ4章の構成に沿ってビジュアルを配置する
7. 各ページにスライサーを配置し、実際に絞り込んで動作確認する
8. 完成したら「ファイル」→「名前を付けて保存」で`.pbix`ファイルとして保存する

## 8. 成果物の格納場所

Power BIの`.pbix`ファイルはバイナリ形式でGitHubとの相性が悪いため、以下の形で格納する。

```
dashboard/
├── power-bi-dashboard-design.md   ← 本書
├── power-bi-theme.json            ← カラーテーマファイル
├── dashboard-overview.png          ← ページ1のスクリーンショット
├── dashboard-channel.png           ← ページ2のスクリーンショット
├── dashboard-funnel.png            ← ページ3のスクリーンショット
└── dashboard-diagnostic.png        ← ページ4のスクリーンショット
```

`.pbix`ファイル自体はGitHubに含めず、**スクリーンショットで実装結果を示す**運用にする(必要であればGoogle DriveなどのリンクをREADMEに記載する)。
