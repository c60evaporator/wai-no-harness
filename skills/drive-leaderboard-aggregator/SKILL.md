---
name: drive-leaderboard-aggregator
description: "CARLA Leaderboard2.0が出力する評価結果JSONファイルを読み込んで、人間が解釈しやすい形式に集約するスキル。ユーザーが「Bench2Drive」「クローズドループ評価」「closed-loop」「End-to-End」「E2E」などに言及した際は必ずこのスキルを参照すること。"
---

# drive-leaderboard-aggregator
CARLA Leaderboard2.0が出力する評価結果JSONファイルを読み込んで、人間が解釈しやすい形式に集約するスキル

## When to Activate
- CARLA Leaderboard2.0の結果を集計するとき

## Input Format

CARLA Leaderboard2.0は、プロセスを実行したGPUごとに以下のようなフォルダ構成で評価結果を記録

```
出力先フォルダ
├── eval_0.json
├── eval_1.json
:
```

### eval_*.jsonのフォーマット

`eval_*.json`（例えば1個目のGPUであれば`eval_0.json`）は、以下のようなフォーマットになっている

```json
{
    "_checkpoint": {
        "global_record": {  // 全レコードの集計結果
            "index": -1,  // 全レコードの集計結果を表す特別なindex
            "route_id": -1,  // 全レコードの集計結果を表す特別なroute_id
            "status": "Failed",  // 全体ステータス（1つでも失敗があればFailed）
            "infractions": {  // 各違反のkmあたりの回数（各違反の詳細は後述）
                "collisions_layout": 2.8,
                "collisions_pedestrian": 1.12,
                "collisions_vehicle": 6.719,
                "red_light": 0.56,
                "stop_infraction": 5.039,
                "outside_route_lanes": 0.056,
                "min_speed_infractions": 196.526,
                "yield_emergency_vehicle_infractions": 0.0,
                "scenario_timeouts": 0.0,
                "route_dev": 0.0,
                "vehicle_blocked": 3.359,
                "route_timeout": 0.0
            },
            "scores_mean": {  // スコアの全ルート平均（各スコアの詳細は後述）
                "score_composed": 34.790578,
                "score_route": 50.457297,
                "score_penalty": 0.777856
            },
            "scores_std_dev": {  // スコアの全ルート標準偏差（各スコアの詳細は後述）
                "score_composed": 34.479,
                "score_route": 41.429,
                "score_penalty": 0.274
            },
            "meta": {
                "total_length": 3730.2500000000005,  // 全ルートの走行距離合計(m)
                "duration_game": 2978.1,  // ゲーム内経過時間合計(秒)
                "duration_system": 151653.63499999998,  // 実時間合計(秒)
                "exceptions": [  // 異常終了したルートのリスト（route_id, index, 失敗理由）
                    [
                        "RouteScenario_1773_rep0",
                        1,
                        "Failed - TickRuntime"
                    ]
                ]
            }
        },
        "progress": [
            37,  // 実行完了したルート数
            37  // 実行予定の総ルート数
        ],
        "records": [
            {
                "index": 0,  // ルートの実行順序（0始まり）
                "route_id": "RouteScenario_1773_rep0",  // ルートの一意識別子（rep0=1回目の試行）
                "scenario_name": "ParkedObstacle_1",  // テストシナリオの種類
                "weather_id": "25",  // 天候条件のID（26種類の天候プリセット、後述）
                "save_name": "RouteScenario_1773_rep0_Town12_ParkedObstacle_1_25_03_26_04_00_24",  // 保存用名称（Town名・シナリオ名・天候・タイムスタンプを結合）
                "status": "Failed - TickRuntime",  // ルートの終了状態（後述）
                "num_infractions": 6,  // 全違反カテゴリの件数合計
                "infractions": {  // 各違反カテゴリの詳細（スコア計算時の後述）
                    "collisions_layout": [],
                    "collisions_pedestrian": [],
                    "collisions_vehicle": [
                        "Agent collided against object with type=vehicle.mercedes.coupe_2020 and id=7537 at (x=-818.649, y=5242.715, z=376.348)"
                    ],
                    "red_light": [],
                    "stop_infraction": [],
                    "outside_route_lanes": [],
                    "min_speed_infractions": [
                        "Average speed is 89.21% of the surrounding traffic's one",
                        "Average speed is 95.21% of the surrounding traffic's one",
                        "Average speed is 81.89% of the surrounding traffic's one",
                        "Average speed is 72.05% of the surrounding traffic's one",
                        "Average speed is 28.84% of the surrounding traffic's one"
                    ],
                    "yield_emergency_vehicle_infractions": [],
                    "scenario_timeouts": [],
                    "route_dev": [],
                    "vehicle_blocked": [],
                    "route_timeout": []
                },
                "scores": {  // ルートのスコア（各スコアの詳細は後述）
                    "score_route": 33.36,
                    "score_penalty": 0.6,
                    "score_composed": 20.016
                },
                "meta": {  // ルートのメタ情報
                    "route_length": 132.062,  // ルートの全長（m）
                    "duration_game": 200.05,  // ゲーム内経過時間（秒）。タイムアウト時は200.05秒
                    "duration_system": 7523.541  // 実時間（秒）。推論速度の指標
                },
                "town_name": "Town12"  // CARLAのマップ名（Bench2Driveは主にTown12/13使用）
            }
        ]
    },
    "entry_status": "Finished",
    "eligible": true,
    "sensors": [],
    "values": [
        "34.790578",
        "50.457297",
        "0.777856",
        "1.12",
        "6.719",
        "2.8",
        "0.56",
        "5.039",
        "0.056",
        "0.0",
        "0.0",
        "3.359",
        "0.0",
        "0.0",
        "196.526"
    ],
    "labels": [
        "Avg. driving score",
        "Avg. route completion",
        "Avg. infraction penalty",
        "Collisions with pedestrians",
        "Collisions with vehicles",
        "Collisions with layout",
        "Red lights infractions",
        "Stop sign infractions",
        "Off-road infractions",
        "Route deviations",
        "Route timeouts",
        "Agent blocked",
        "Yield emergency vehicles infractions",
        "Scenario timeouts",
        "Min speed infractions"
    ]
}
```

### 各違反の詳細とペナルティ
`global_record.infractions`や`records.infractions`フィールドに記載される違反の詳細は以下（penalty乗数は動的に変更できるが、ここではBench2Driveでの値を記載）

| フィールド | Bench2Driveでのpenalty乗数 | 意味 |
|---|---|---|
| `collisions_layout` | ×0.65 | 静的構造物（フェンス、標識、植栽等）との衝突 |
| `collisions_pedestrian` | ×0.50 | 歩行者との衝突（座標・対象ID記載） |
| `collisions_vehicle` | ×0.60 | 車両との衝突 |
| `red_light` | ×0.70 | 赤信号無視 |
| `stop_infraction` | ×0.80 | 一時停止標識無視 |
| `outside_route_lanes` | ×(1-逸脱割合) | ルート外車線への逸脱（距離と完走率に対する%記載） |
| `min_speed_infractions` | ペナルティなし(unused) | 周囲交通に対する速度比（Bench2Driveでは評価に不使用） |
| `yield_emergency_vehicle_infractions` | ×0.70 | 緊急車両への道譲り違反 |
| `scenario_timeouts` | ×0.70 | シナリオのタイムアウト |
| `route_dev` | — | ルート逸脱 |
| `vehicle_blocked` | — | エージェントが停止（ペナルティ乗数なし、ルート強制終了） |
| `route_timeout` | — | ルートタイムアウト |

> `outside_route_lanes`はpenalty乗数$p_i = 1 - \frac{\text{逸脱％}}{100}$と逸脱割合に応じて動的に計算されます
> `route_dev`、`vehicle_blocked`、`route_timeout`はpenaltyなし（走行を途中で打ち切ることで間接的に`score_route`を下げる）

### status（ルートの終了状態）の種類
`Perfect`,`Completed`以外になったルートが`exceptions`フィールドに記載される

| 値 | 意味 |
|---|---|
| `Perfect` | シナリオの目標を完全達成 |
| `Completed` | ルート完走（途中で強制終了なし） |
| `Failed - TickRuntime` | シミュレーションのtick処理でランタイムエラー（エージェントのPython例外等） |
| `Failed - Agent got blocked` | エージェントが180秒以上停止 |
| `Failed - Agent couldn't be set up` | エージェントの初期化に失敗（モデルロードエラー等） |

### 各スコアの詳細
| フィールド | 例 | 意味 |
|---|---|---|
| `score_route` | 100 | ルート完走率（%）。完走=100、途中終了=走行距離/全長×100。詳細は後述 |
| `score_penalty` | 0.6 | 違反による減衰係数。違反なし=1.0。計算式は後述 |
| `score_composed` | 60.0 | **Driving Score** = `score_route × score_penalty` |

#### score_routeの計算詳細
`RouteCompletionTest` クラス（atomic_criteria.py）で計算：

```
ルートのウェイポイント列に対して、自車位置からの内積で通過判定
→ 通過したウェイポイントまでの累積距離 / ルート全長 × 100
```

- 各ウェイポイント間の距離を累積
- 自車がウェイポイントの前方ベクトルと同方向に位置する（内積 > 0）なら通過と判定
- 最終地点に十分近ければ100%

#### score_penaltyの計算式
`score_penalty`は、初期値`score_penalty = 1.0`から、違反が発生するたびに違反の種類に応じたpenalty乗数$p_i$に従い、乗算的に減衰

$$\text{score\_penalty} = \prod_{i} p_i$$

例えば歩行者衝突（$p_i=0.5$）が2回、車両衝突（$p_i=0.6$）が1回起こった場合、$0.5 \times 0.5 \times 0.6 = 0.15$が`score_penalty`になる

### 天候ID一覧

| ID | 時間帯 | 雲量 | 雨 | 路面水 | 濡れ | 風 | 霧 | 概要 |
|---|---|---|---|---|---|---|---|---|
| **0** | 昼(90°) | 5 | 0 | 0 | 0 | 10 | 2 | ☀️ 快晴・正午 |
| **1** | 夕方(15°) | 5 | 0 | 0 | 0 | 10 | 2 | 🌅 快晴・夕方 |
| **2** | 昼(45°) | 20 | 30 | 50 | 0 | 30 | 3 | 🌦️ 小雨 |
| **3** | 昼(45°) | 60 | 60 | 60 | 0 | 60 | 3 | 🌧️ 中雨 |
| **5** | 昼(45°) | 80 | 0 | 50 | 20 | 10 | 3 | ☁️ 曇り・路面濡れ |
| **6** | 夕方(15°) | 5 | 0 | 50 | 0 | 10 | 10 | 🌫️ 夕方・軽い霧 |
| **7** | 昼(45°) | 5 | 0 | 0 | 0 | 10 | 2 | ☀️ 晴れ・昼 |
| **8** | 昼(45°) | 100 | 100 | 90 | 0 | 100 | 7 | ⛈️ 暴風雨 |
| **9** | 昼(45°) | 70 | 60 | 60 | 0 | 60 | 50 | 🌧️🌫️ 雨+濃霧 |
| **10** | 夜(0°) | 40 | 100 | 90 | 0 | 100 | 7 | 🌙⛈️ 夜・暴風雨 |
| **11** | 昼(45°) | 100 | 60 | 60 | 0 | 60 | 50 | ☁️🌫️ 曇り+雨+濃霧 |
| **12** | 昼(45°) | 5 | 0 | 0 | 0 | 10 | 50 | 🌫️ 晴れ+濃霧 |
| **13** | 夕方(15°) | 5 | 0 | 0 | 0 | 10 | 50 | 🌅🌫️ 夕方+濃霧 |
| **14** | 昼(45°) | 100 | 100 | 50 | 50 | 100 | 10 | ⛈️ 暴風雨・路面濡れ |
| **15** | 昼(45°) | 100 | 50 | 100 | 80 | 80 | 10 | 🌧️ 雨・路面冠水 |
| **18** | 夕方(15°) | 40 | 0 | 50 | 0 | 10 | 2 | 🌅☁️ 夕方・曇り |
| **19** | 夜(-90°) | 40 | 0 | 50 | 0 | 10 | 2 | 🌙 夜・曇り |
| **20** | 夜(-90°) | 60 | 30 | 50 | 60 | 30 | 3 | 🌙🌧️ 夜・小雨 |
| **21** | 夜(-90°) | 100 | 100 | 90 | 100 | 100 | 3 | 🌙⛈️ 夜・暴風雨・路面冠水 |
| **22** | 夜(-90°) | 5 | 0 | 0 | 0 | 10 | 60 | 🌙🌫️ 夜・濃霧 |
| **23** | 夜(-90°) | 80 | 60 | 60 | 80 | 60 | 60 | 🌙🌧️🌫️ 夜・雨+濃霧 |
| **25** | 夜(-90°) | 100 | 100 | 90 | 100 | 100 | 100 | 🌙⛈️🌫️ **最悪条件**（夜・暴風雨・濃霧MAX） |
| **26** | 昼(70°) | 50 | 0 | 0 | 0 | 0 | 0 | ☀️ デフォルト晴れ |

> **補足**: `sun_altitude_angle` の意味：90°=正午、45°=午後、15°=夕方、0°=日没、-90°=深夜。ID 4, 16, 17, 24 は欠番です。

## Output Format
上記のInput Formatをふまえ、以下のような指標を計算して出力する

### ルートごとの集計
従来から`records`フィールド内のリストにフィールドとして含まれる指標、メタデータに加え、以下の指標を計算する

|名称|型|計算方法|
|---|---|---|
|gpu_index|int|評価を実行したGPUのインデックス（eval_*.jsonの番号）|
|success|bool|完走（statusが`Perfect`か`Completed`） and `min_speed_infractions`以外の違反0ならTrue、それ以外ならFalse|
|score_penalty_orginal|float|以下のような外部yamlファイルから与えたpenalty乗数をもとに`records.infractions`から計算した`score_penalty`（`outside_route_lanes`は従来通り(1-逸脱割合)を使用し、`route_dev`,`vehicle_blocked`,`route_timeout`は従来通り）|

```yaml
penalty_ratio:
 - collisions_layout: 0.65
 - collisions_pedestrian: 0.5
 - collisions_vehicle: 0.6
 - red_light: 0.7
 - stop_infraction: 0.8
 - min_speed_infractions: 1.0
 - yield_emergency_vehicle_infractions: 0.65
 - scenario_timeouts: 0.7
```

### 全ルートでの集計
全GPUでの結果（全ての`eval_*.json`）をマージして以下の指標を求める

|名称|計算方法|
|---|---|
|infractions|各違反のkmあたりの回数（`eval_*.json`の`global_record.infractions`と同じ計算法）|
|scores_mean|各スコアの全ルート平均（`eval_*.json`の`global_record.scores_mean`と同じ計算法だが、`score_penalty_orginal`を計算対象に加える）|
|scores_mean_220|各スコアの全ルート合計$\div 220$（元の3種類のスコア＋`score_penalty_orginal`が計算対象）|
|meta|全ルートでの`total_length`,`duration_game`,`duration_system`,`exceptions`|
