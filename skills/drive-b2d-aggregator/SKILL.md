# drive-b2d-aggregator
Bench2Driveが出力する評価結果JSONファイルや画像を読み込んで、人間が解釈しやすいよう集約・表示するためのスキル

## When to Activate
- Bench2Driveの結果を集計するとき

## 依存スキル
このスキルを使う前に以下を読んでください：
`/mnt/skills/public/carla-leaderboard-aggregator/SKILL.md`

## Input Format

Bench2Driveは、以下のようなフォルダ構成で評価結果を記録します（Bench2Driveスクリプト実行時に、フレームデータ保存用フォルダは`SAVE_PATH`引数で、Leaderboard出力先フォルダは`CHECKPOINT_ENDPOINT`引数で別々に指定されます）。

```
フレームデータ保存用フォルダ
├── RouteScenario_1711_rep0_Town12_ParkingCutIn_1_15_02_26_01_02_58 <- シナリオごとフォルダ
:   ├── meta <- フレームごとのPID制御メタデータ
    :   ├── 0000.json
        :
    ├── rgb_back <- フレームごとの後方カメラ画像
    :   ├── 0000.png
        :
    ├── rgb_back_left <- フレームごとの左後方カメラ画像
    :   ├── 0000.png
        :
    ├── rgb_back_right <- フレームごとの右後方カメラ画像
    :   ├── 0000.png
        :
    ├── rgb_front <- フレームごとの前方カメラ画像
    :   ├── 0000.png
        :
    ├── rgb_front_left <- フレームごとの左前方カメラ画像
    :   ├── 0000.png
        :
    ├── rgb_front_right <- フレームごとの右前方カメラ画像
    :   ├── 0000.png
        :
    ├── bev <- フレームごとのBEV画像（CARLAの上空カメラで撮ったデバッグ向け）
    :   ├── 0000.png
        :
    └── metric_info.json <- タイムステップごとの車両状態

Leaderboard出力先フォルダ（GPUごとに別ファイルで出力）
├── eval_0.json
├── eval_1.json
:
```

### 各jsonファイルのフォーマット
`eval_*.json`の詳細については`carla-leaderboard-aggregator`スキルを参照してください。また`metric_info.json`の情報は使用しません。

`meta/****.json`は以下のようなフォーマットになっています（`uniad_b2d_agent.py`の`PIDController.control_pid()`が返す`metadata`に、`run_step()`で追加情報を付与したもの）。

| フィールド | 値の例 | 意味 |
|---|---|---|
| `speed` | `1.02e-05` | 現在の車速 [m/s]（CARLAのspeedometerセンサ値） |
| `steer` | `-0.0067` | 実際にCARLAに送った操舵量（`np.clip(steer_traj, -1, 1)`） |
| `throttle` | `0.75` | 実際に送ったスロットル（`np.clip(throttle_traj, 0, 0.75)`） |
| `brake` | `0.0` | 実際に送ったブレーキ（`np.clip(brake_traj, 0, 1)`） |
| `wp_4` ~ `wp_1` | `[x, y]` | PIDコントローラが使うウェイポイント（lidar座標系、`plan`の逆順：wp_1=最近、wp_4=最遠） |
| `aim` | `[x, y]` | PIDが操舵計算に使う目標点（通常`wp_2`、速度に応じて選択） |
| `target` | `[-0.67, 52.25]` | ルートプランナーの次の目標ナビポイント（lidar座標系のローカル座標） |
| `desired_speed` | `7.02` | PIDが算出した目標速度 [m/s]（`aim`点までの距離から計算） |
| `angle` | `-0.012` | `aim`点への方位角 [rad]（操舵量計算に使用） |
| `angle_last` | `0.297` | 前フレームの`angle`値 |
| `angle_target` | `-0.0082` | `target`（ナビポイント）への方位角 [rad] |
| `angle_final` | `-0.0082` | 最終的に操舵計算に使われた角度（通常`angle_target`と同じ） |
| `delta` | `0.25` | `desired_speed - speed`の差分（スロットル/ブレーキ判定に使用） |
| `agent` | `"only_traj"` | 使用した制御モード（`run_step()`で`"only_traj"`固定） |
| `steer_traj` | `-0.0067` | PIDが軌跡から算出した生の操舵値（clip前） |
| `throttle_traj` | `0.75` | PIDが算出した生のスロットル値（clip前） |
| `brake_traj` | `0.0` | PIDが算出した生のブレーキ値（clip前） |
| `plan` | `[[x,y]×6]` | UniADのPlannerヘッドが出力した6ステップの将来軌跡 [lidar座標系、各0.5秒間隔=計3秒先] |
| `command` | `3` | ナビコマンド（0=Left, 1=Right, 2=Straight, 3=LaneFollow, 4=ChangeLaneL, 5=ChangeLaneR） |

**制御フロー**: `plan`（UniAD出力）→ PIDコントローラが`wp`/`aim`/`angle`/`desired_speed`を計算 → `steer_traj`/`throttle_traj`/`brake_traj`を算出 → clip後に`steer`/`throttle`/`brake`としてCARLAに送信。

### 推論結果の保持
通常のBench2Driveで保存される上記のセンサ情報に加え、AIモデル（UniAD等）の推論結果を独自に以下のように保存しています

```
画像保存用フォルダ
├── RouteScenario_1711_rep0_Town12_ParkingCutIn_1_15_02_26_01_02_58 <- シナリオごとフォルダ
    :
    ├── inference <- フレームごとのAIの推論結果情報
    :   ├── 0000.npz
        :
```

#### UniADの場合
UniAD用のエージェントでは、1フレームの推論情報（3D追跡=TrackFormer、軌跡予測=MotionFormer、マップセグメンテーション=MapFormer）を以下の9つのキーで`inference/****.npz`に記録しています

| キー | コンポーネント | shape | dtype | 内容 |
|---|---|---|---|---|
| `corners_3d` | TrackFormer | (24, 8, 3) | float32 | 検出された24物体の3Dバウンディングボックス8頂点の(x,y,z)座標 |
| `boxes_tensor` | TrackFormer | (24, 9) | float32 | 各物体のボックスパラメータ (x,y,z, w,l,h, yaw, vx, vy) |
| `scores_3d` | TrackFormer | (24,) | float32 | 各物体の検出スコア |
| `labels_3d` | TrackFormer | (24,) | int64 | 各物体のクラスラベル（0=car, 4=barrier, 6=traffic_coneなど） |
| `track_ids` | TrackFormer | (24,) | int64 | 各物体のトラッキングID |
| `traj` | MotionFormer | (25, 6, 12, 5) | float32 | 25物体×6モード×12ステップ×5値(x,y,z,σ?,score?)の将来軌跡予測 |
| `traj_scores` | MotionFormer | (25, 6) | float32 | 各物体×6モードの軌跡スコア（logit） |
| `lane_score` | MapFormer | (6, 200, 200) | float32 | BEV形式のマップセグメンテーション（6チャネル、200×200グリッド） |
| `drivable` | MapFormer | (200, 200) | bool | BEV形式の走行可能領域のセグメンテーション |

## Output Format
上記のInput Formatをふまえ、以下のような指標や可視化UIを出力する

### 指標

`carla-leaderboard-aggregator`スキルで得られる指標に加え、`meta/****.json`に記載されたフィールド情報をそのまま出力

### 可視化UI
カメラ画像上に推論結果を可視化する際の指針

#### 各カメラ画像
- 物体検出（例：UniADのTrackFormer）：`inference/****.npz`の`corners_3d`の8頂点を3Dバウンディングボックスとしてカメラ画像に投影して描画（物体ごとに色分け）
- 各物体の軌跡予測（例：UniADのMotionFormer）：`inference/****.npz`の`traj`から、各物体の将来軌跡予測のスコア上位3モード（`traj_scores`で選択）を緑色の折れ線としてカメラ画像に投影して描画（物体ごとに色分け）
- 自車の軌跡予測（例：UniADのPlanner）：`meta/****.json`の`plan`を折れ線（オレンジ→黄のグラデーション）としてカメラ画像に投影して描画（`inference/****.npz`の`traj`ではないので注意）
- 自車の正解軌跡（ナビポイント）：`meta/****.json`の`target`を赤い点で描画して示す

#### BEV画像
BEV画像上の推論結果の可視化は、CARLAの上空カメラで撮ったデバッグ向けのBEV画像（`bev/****.png`）をベースに、以下のように描画する
- 物体検出（例：UniADのTrackFormer）：`inference/****.npz`の`corners_3d`の8頂点をBEV用の射影行列で2Dに落とし、下側の面だけを線で結んだ2DバウンディングボックスとしてBEV画像に投影して描画（物体ごとに色分け）
- 各物体の軌跡予測（例：UniADのMotionFormer）：`inference/****.npz`の`traj`から、各物体の将来軌跡予測のスコア上位3モード（`traj_scores`で選択）を緑色の折れ線としてBEV画像に投影して描画（物体ごとに色分け）
- マップセグメンテーション（例：UniADのMapFormer）：`inference/****.npz`の`lane_score`をBEV画像に投影して、車線や歩道などのマップ情報を半透明でオーバーレイ表示（チャネルごとに色分け）。さらに`drivable`もオーバーレイ表示して走行可能領域を示す
- 自車の軌跡予測（例：UniADのPlanner）：`meta/****.json`の`plan`を折れ線（オレンジ→黄のグラデーション）としてBEV画像に投影して描画（`inference/****.npz`の`traj`ではないので注意）

#### Ego-pose
あらかじめBEV画像（`bev/****.png`）をオルソ画像のような形で合成しておき（高さは一定の前提でOK）、ユーザーが任意のフレームを選択したときに、そのフレームの`meta/****.json`の`target`（ナビポイント）を合成画像上に赤い点で描画して現在位置を示す

#### 
