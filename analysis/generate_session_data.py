"""
LP・診断アプリの架空セッションデータ生成スクリプト

analysis-design.md の設計に基づき、以下を意図的に仕込んだデータを生成する。

- チャネルによって流入数・CVR・CPAが異なる(紹介・SNS広告のCVRが高く、検索広告は低い)
- 診断アプリを完了したセッションは、完了しなかったセッションよりCVRが明確に高い
  (診断アプリがCVR改善に貢献している、という結論を後から確認できるようにする)
- 診断結果タイプによってCTAクリック率・CVRに差がある
  (rest=休息不足タイプが最もLPの主訴求と一致するため、やや高いCVRになるよう設定)
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

rng = np.random.default_rng(7)
N = 2000

# ---------------------------------------------------------
# 1. 流入チャネル(チャネルごとに流入ボリュームの重みを変える)
# ---------------------------------------------------------
channels = ["SNS広告", "検索広告", "自然検索", "紹介"]
channel_weights = [0.55, 0.20, 0.18, 0.07]
channel = rng.choice(channels, size=N, p=channel_weights)

# ---------------------------------------------------------
# 2. 訪問日(過去60日間でランダム)
# ---------------------------------------------------------
today = datetime(2026, 9, 1)
visit_date = [
    (today - timedelta(days=int(rng.uniform(0, 60)))).strftime("%Y-%m-%d")
    for _ in range(N)
]

# ---------------------------------------------------------
# 3. 悩みセクション到達率(チャネルによって多少差をつける。紹介はより深く読む傾向)
# ---------------------------------------------------------
pain_reach_prob_by_channel = {
    "SNS広告": 0.62,
    "検索広告": 0.58,
    "自然検索": 0.66,
    "紹介": 0.75,
}
reached_pain_section = np.array([
    1 if rng.random() < pain_reach_prob_by_channel[c] else 0 for c in channel
])

# ---------------------------------------------------------
# 4. 診断アプリの開始・完了(悩みセクションに到達した人だけが対象になりうる)
# ---------------------------------------------------------
diagnostic_started = np.zeros(N, dtype=int)
diagnostic_completed = np.zeros(N, dtype=int)

# 悩みセクション到達者のうち、一定割合が診断を開始する
start_prob_by_channel = {
    "SNS広告": 0.40,
    "検索広告": 0.28,
    "自然検索": 0.35,
    "紹介": 0.45,
}
# 開始した人のうち、完了まで至る割合(離脱ポイントの1つ)
complete_prob = 0.72

for i in range(N):
    if reached_pain_section[i] == 1:
        if rng.random() < start_prob_by_channel[channel[i]]:
            diagnostic_started[i] = 1
            if rng.random() < complete_prob:
                diagnostic_completed[i] = 1

# ---------------------------------------------------------
# 5. 診断結果タイプ(完了した人のみ付与)
# ---------------------------------------------------------
result_types = ["rest", "reset", "overwork"]
result_type_weights = [0.38, 0.34, 0.28]

diagnostic_result_type = np.array([
    rng.choice(result_types, p=result_type_weights) if diagnostic_completed[i] == 1 else None
    for i in range(N)
], dtype=object)

# ---------------------------------------------------------
# 6. CTAクリック
#    - 診断完了者: タイプによってクリック率に差をつける(restが最も高い)
#    - 診断未完了だが悩みセクションに到達した人: 診断を経由しない直接クリック
#    - 診断未開始・悩み未到達: クリックしない
# ---------------------------------------------------------
cta_click_prob_by_type = {"rest": 0.58, "reset": 0.50, "overwork": 0.45}
direct_cta_click_prob_by_channel = {
    "SNS広告": 0.22,
    "検索広告": 0.15,
    "自然検索": 0.20,
    "紹介": 0.30,
}

cta_click = np.zeros(N, dtype=int)
for i in range(N):
    if diagnostic_completed[i] == 1:
        p = cta_click_prob_by_type[diagnostic_result_type[i]]
        cta_click[i] = 1 if rng.random() < p else 0
    elif reached_pain_section[i] == 1:
        # 診断を使わなかった(または開始したが完了しなかった)場合の直接クリック
        p = direct_cta_click_prob_by_channel[channel[i]]
        cta_click[i] = 1 if rng.random() < p else 0

# ---------------------------------------------------------
# 7. コンバージョン(フォーム完了)
#    CTAをクリックした人のうち、フォーム完了に至る割合。
#    診断完了者はより「自分ごと化」できているため、フォーム完了率がやや高くなるよう設定
# ---------------------------------------------------------
conversion = np.zeros(N, dtype=int)
for i in range(N):
    if cta_click[i] == 1:
        base_p = 0.55
        if diagnostic_completed[i] == 1:
            base_p = 0.68
        conversion[i] = 1 if rng.random() < base_p else 0

# ---------------------------------------------------------
# データフレーム化
# ---------------------------------------------------------
df = pd.DataFrame({
    "session_id": [f"S{str(i).zfill(5)}" for i in range(1, N + 1)],
    "channel": channel,
    "visit_date": visit_date,
    "reached_pain_section": reached_pain_section,
    "diagnostic_started": diagnostic_started,
    "diagnostic_completed": diagnostic_completed,
    "diagnostic_result_type": diagnostic_result_type,
    "cta_click": cta_click,
    "conversion": conversion,
})

# ---------------------------------------------------------
# チャネル別 月間広告費用(ダミー。紹介・自然検索は広告費なし=0円)
# ---------------------------------------------------------
channel_ad_cost = pd.DataFrame({
    "channel": ["SNS広告", "検索広告", "自然検索", "紹介"],
    "monthly_ad_cost_jpy": [450000, 380000, 0, 0],
})

# ---------------------------------------------------------
# 出力
# ---------------------------------------------------------
session_csv = "/mnt/user-data/outputs/analysis/session_data.csv"
session_xlsx = "/mnt/user-data/outputs/analysis/session_data.xlsx"
cost_csv = "/mnt/user-data/outputs/analysis/channel_ad_cost.csv"
cost_xlsx = "/mnt/user-data/outputs/analysis/channel_ad_cost.xlsx"

df.to_csv(session_csv, index=False, encoding="utf-8-sig")
df.to_excel(session_xlsx, index=False, sheet_name="session_data")
channel_ad_cost.to_csv(cost_csv, index=False, encoding="utf-8-sig")
channel_ad_cost.to_excel(cost_xlsx, index=False, sheet_name="channel_ad_cost")

# ---------------------------------------------------------
# 検算
# ---------------------------------------------------------
print("件数:", len(df))
print("\n--- チャネル別 流入数・CVR ---")
summary = df.groupby("channel").agg(
    sessions=("session_id", "count"),
    conversions=("conversion", "sum"),
).reset_index()
summary["CVR(%)"] = (summary["conversions"] / summary["sessions"] * 100).round(2)
summary = summary.merge(channel_ad_cost, on="channel", how="left")
summary["CPA(円)"] = summary.apply(
    lambda r: round(r["monthly_ad_cost_jpy"] / r["conversions"]) if r["conversions"] > 0 and r["monthly_ad_cost_jpy"] > 0 else None,
    axis=1,
)
print(summary)

print("\n--- 診断完了有無によるCVR比較 ---")
print(df.groupby("diagnostic_completed")["conversion"].mean().mul(100).round(2))

print("\n--- 診断結果タイプ別 CTAクリック率・CVR ---")
diag_df = df[df["diagnostic_completed"] == 1]
print(diag_df.groupby("diagnostic_result_type").agg(
    cta_click_rate=("cta_click", "mean"),
    cvr=("conversion", "mean"),
).mul(100).round(2))
