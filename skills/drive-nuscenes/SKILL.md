---
name: drive-nuscenes
description: "nuScenesデータセットの構造とファイル形式の説明。Use when user uses ."
description-en: ""
description-ja: ""
allowed-tools: ["Read", "Write", "Edit", "Bash", "Grep", "Glob"]
argument-hint: "<entity-name>"
user-invocable: false
---

## フォルダ構成とファイル形式

### フォルダ構成
```
root
├─ v1.0-trainval <- メタデータtrainval
|   ├─ scene.json
|   ├─ sample.json
|   ├─ sample_data.json
|   ├─ sample_annotation.json
|   ├─ instance.json
|   ├─ category.json
|   ├─ attribute.json
|   ├─ visibility.json
|   ├─ sensor.json
|   ├─ calibrated_sensor.json
|   ├─ ego_pose.json
|   ├─ log.json
|   └─ map.json
├─ samples <- キーフレームのセンサデータ
|   ├─ CAM_BACK
|   |   ├─ n008-2018-08-01-15-16-36-0400__CAM_BACK__1533151603537558.jpg
|   ├─ CAM_BACK_LEFT
|   ├─ CAM_BACK_RIGHT
|   ├─ CAM_FRONT
|   ├─ CAM_FRONT_LEFT
|   ├─ CAM_FRONT_RIGHT
|   ├─ LIDAR_TOP
|   |   ├─ n008-2018-08-01-15-16-36-0400__LIDAR_TOP__1533151603547590.pcd.bin
|   ├─ RADAR_BACK_LEFT
|   |   ├─ n008-2018-08-01-15-16-36-0400__RADAR_BACK_LEFT__1533151603522238.pcd
|   ├─ RADAR_BACK_RIGHT
|   ├─ RADAR_FRONT
|   ├─ RADAR_FRONT_LEFT
|   └─ RADAR_FRONT_RIGHT
├─ sweeps <- キーフレーム以外のセンサデータ
|   ├─ CAM_BACK
|   ├─ CAM_BACK_LEFT
|   ├─ CAM_BACK_RIGHT
|   ├─ CAM_FRONT
|   ├─ CAM_FRONT_LEFT
|   ├─ CAM_FRONT_RIGHT
|   ├─ LIDAR_TOP
|   ├─ RADAR_BACK_LEFT
|   ├─ RADAR_BACK_RIGHT
|   ├─ RADAR_FRONT
|   ├─ RADAR_FRONT_LEFT
|   └─ RADAR_FRONT_RIGHT
└─ maps
    ├─ 36092f0b03a857c6a3403e25b4b7aab3.png <- boston-seaportのbasemap画像
    ├─ 37819e65e09e5547b8a3ceaefba56bb2.png <- singapore-onenorthのbasemap画像
    ├─ 53992ee3023e5494b90c316c183be829.png <- singapore-hollandvillageのbasemap画像
    ├─ 93406b464a165eaba6d9de76ca09f5da.png <- singapore-queenstownのbasemap画像
    ├─ basemap <- Map Expansionのマップ高精細画像
    |   ├─ boston-seaport.png
    |   ├─ singapore-hollandvillage.png
    |   ├─ singapore-onenorth.png
    |   └─ singapore-queenstown.png
    ├─ expansion <- Map Expansionのメタデータ
    |   ├─ boston-seaport.json
    |   ├─ singapore-hollandvillage.json
    |   ├─ singapore-onenorth.json
    |   └─ singapore-queenstown.json
    └─ prediction <- Map Expansionの予測タスクのアノテーション
        └─ prediction_scenes.json
```

### ファイル形式

|データ種別|ファイル形式|内容|
|---|---|---|
|basemap|.png|ロケーションごとの地図画像|
|カメラ画像|.jpg|フレームごとの前方・後方カメラ画像など|
|LiDAR|.pcd.bin|float32 × 5列|
|RADAR|.pcd|標準PCD形式、ASCIIまたはbinary|

**RADARのファイル形式詳細**

標準PCD形式（`.pcd`、binary）。LiDARの `.pcd.bin`（float32固定）とは異なり、
フィールドごとにSIZEとTYPEが異なる混在形式：

```
FIELDS x y z dyn_prop id rcs vx vy vx_comp vy_comp is_quality_valid ...
SIZE   4 4 4 1        2  4   4  4 4        4        1               ...
TYPE   F F F I        I  F   F  F F        F        I               ...
```

`SIZE=1` のフィールドは `np.int8`（TYPE=I）または `np.uint8`（TYPE=U）で読む必要がある。
`SIZE=2` は `np.int16`（TYPE=I）または `np.uint16`（TYPE=U）。
`SIZE=4` は `np.float32`（TYPE=F）または `np.int32`（TYPE=I）。
SIZEとTYPEを組み合わせてdtypeを決定しないと全点が0になる。

