# metadata-fields.md
nuScenesデータセットのメタデータの各フィールドの内容とフォーマットを記載

**トークンはすべてハイフンなしUUIDであることに注意**

#### scene.json

シーン（連続した一連の運転データ）の一覧を表します。

|フィールド名|型|内容|
|---|---|---|
|log_token|UUID|このシーンが含まれるログ(log)のtoken|
|nbr_samples|int|含まれるキーフレームの数|
|first_sample_token|UUID|最初のキーフレームのtoken|
|last_sample_token|UUID|最後のキーフレームのtoken|
|name|str|シーンの名称|
|description|str|シーンの説明|

例

```json:例
[
  {
    "token": "cc8c0bf57f984915a77078b10eb33198",
    "log_token": "7e25a2c8ea1f41c5b0da1e69ecfa71a2",
    "nbr_samples": 39,
    "first_sample_token": "ca9a282c9e77460f8360f564131a8af5",
    "last_sample_token": "ed5fc18c31904f96a8f0dbb99ff069c0",
    "name": "scene-0061",
    "description": "Parked truck, construction, intersection, turn left, following a van"
  },
]
```

#### sample.json

キーフレームの一覧を表します。

|フィールド名|型|内容|
|---|---|---|
|timestamp|int|取得した時刻のタイムスタンプ|
|prev|UUID|前のキーフレームのtoken|
|next|UUID|次のキーフレームのtoken|
|scene_token|UUID|このキーフレームが含まれるシーンのtoken|

例

```json:例
[
  {
    "token": "ca9a282c9e77460f8360f564131a8af5",
    "timestamp": 1532402927647951,
    "prev": "",
    "next": "39586f9d59004284a7114a68825e8eec",
    "scene_token": "cc8c0bf57f984915a77078b10eb33198"
  },
]
```

例えばキーフレームを時刻順に並び変えたい場合、`timestamp`でソートする方法と、`prev`と`next`を辿っていく方法両方を使えます。

#### sample_data.json

センサデータの一覧を表します。

|フィールド名|型|内容|
|---|---|---|
|sample_token|UUID|紐づくキーフレーム(samples)のtoken|
|ego_pose_token|UUID|紐づく車両の姿勢情報(ego_pose)のtoken|
|calibrated_sensor_token|UUID|紐づくセンサのキャリブレーション情報(calibrated_sensor)のtoken|
|timestamp|int|取得した時刻のタイムスタンプ|
|fileformat|str|データの保存形式（カメラなら`jpg`、LiDARやRADARなら`pcd`）|
|is_key_frame|bool|キーフレームのデータかどうか|
|height|int|センサデータの高さ（カメラのみ）|
|width|int|センサデータの幅（カメラのみ）|
|filename|str|実際のセンサデータのパス（`samples`で始まっていればキーフレーム、`sweeps`で始まっていればそれ以外のデータ）|
|prev|UUID|前の同センサのデータのtoken|
|next|UUID|次の同センサのデータのtoken|

例

```json:例
[
  {
    "token": "5ace90b379af485b9dcb1584b01e7212",
    "sample_token": "39586f9d59004284a7114a68825e8eec",
    "ego_pose_token": "5ace90b379af485b9dcb1584b01e7212",
    "calibrated_sensor_token": "f4d2a6c281f34a7eb8bb033d82321f79",
    "timestamp": 1532402927814384,
    "fileformat": "pcd",
    "is_key_frame": false,
    "height": 0,
    "width": 0,
    "filename": "sweeps/RADAR_FRONT/n015-2018-07-24-11-22-45+0800__RADAR_FRONT__1532402927814384.pcd",
    "prev": "f0b8593e08594a3eb1152c138b312813",
    "next": "978db2bcdf584b799c13594a348576d2"
  },
]
```

例えばキーフレームを時刻順に並び変えたい場合、`timestamp`でソートする方法と、`prev`と`next`を辿っていく方法両方を使えます。

#### sample_annotation.json

物体アノテーション(3次元バウンディングボックスと分類ラベル)を表します。**translationとrotationはグローバル座標**で記載されていることにご注意ください（自車を中心としたローカル座標ではない）。

|フィールド名|型|内容|
|---|---|---|
|sample_token|UUID|該当するキーフレーム(sample)のtoken|
|instance_token|UUID|該当するインスタンス(instance)のtoken|
|visibility_token|UUID|写っているピクセルの割合(visibility)のtoken|
|attribute_tokens|list[UUID]|含まれる状態属性(attribute)のtokenのリスト|
|translation|list[float]|バウンディングボックスの位置情報(xyz)|
|size|list[float]|車両姿勢の位置情報(xyz)|
|rotation|list[float]|バウンディングボックスの回転情報(quaternion)|
|prev|UUID|同インスタンスの前のアノテーションのtoken|
|next|UUID|同インスタンスの次のアノテーションのtoken|

```json:例
[
  {
    "token": "70aecbe9b64f4722ab3c230391a3beb8",
    "sample_token": "cd21dbfc3bd749c7b10a5c42562e0c42",
    "instance_token": "6dd2cbf4c24b4caeb625035869bca7b5",
    "visibility_token": "4",
    "attribute_tokens": [
      "4d8821270b4a47e3a8a300cbec48188e"
    ],
    "translation": [
      373.214,
      1130.48,
      1.25
    ],
    "size": [
      0.621,
      0.669,
      1.642
    ],
    "rotation": [
      0.9831098797903927,
      0.0,
      0.0,
      -0.18301629506281616
    ],
    "prev": "a1721876c0944cdd92ebc3c75d55d693",
    "next": "1e8e35d365a441a18dd5503a0ee1c208",
    "num_lidar_pts": 5,
    "num_radar_pts": 0
  },
]
```

#### instance.json

物体インスタンス(複数キーフレームに写る同一の物体)の一覧を表します

|フィールド名|型|内容|
|---|---|---|
|category_token|UUID|該当する分類ラベル(category)のtoken|
|nbr_annotations|int|アノテーション数(写っているキーフレームの数を意味する)|
|first_annotation_token|UUID|最初のアノテーション(sample_annotation)のtoken|
|last_annotation_token|UUID|最後のアノテーション(sample_annotation)のtoken|

```json:例
[
  {
  "token": "6dd2cbf4c24b4caeb625035869bca7b5",
  "category_token": "1fa93b757fc74fb197cdd60001ad8abf",
  "nbr_annotations": 39,
  "first_annotation_token": "ef63a697930c4b20a6b9791f423351da",
  "last_annotation_token": "8bb63134d48840aaa2993f490855ff0d"
  },
]
```

#### category.json

物体アノテーションのカテゴリ一覧(e.g. vehicle, human)を表します。

|フィールド名|型|内容|
|---|---|---|
|name|str|カテゴリ名|
|description|str|カテゴリの説明|

```json:例
[
  {
    "token": "1fa93b757fc74fb197cdd60001ad8abf",
    "name": "human.pedestrian.adult",
    "description": "Adult subcategory."
  },
]
```

#### attribute.json

物体アノテーションの状態ラベル一覧を表します。

|フィールド名|型|内容|
|---|---|---|
|name|str|状態ラベル名|
|description|str|状態ラベルの説明|

```json:例
[
  {
    "token": "1fa93b757fc74fb197cdd60001ad8abf",
    "name": "human.pedestrian.adult",
    "description": "Adult subcategory."
  },
]
```

#### visibility.json

物体アノテーションのどれくらいの割合のピクセルがカメラに写っているかを表します。

|フィールド名|型|内容|
|---|---|---|
|level|str|写っているピクセルの割合|
|description|str|より詳細な説明|

```json:例
[
  {
  "description": "visibility of whole object is between 0 and 40%",
  "token": "1",
  "level": "v0-40"
  },
]
```

tokenがint型(厳密には数字を表すstr型)であることに注意してください

#### sensor.json

センサの一覧を表します。

|フィールド名|型|内容|
|---|---|---|
|channel|str|センサの名称|
|modality|str|センサの種類（カメラなら`camera`、LiDARなら`lidar`、レーダーなら`radar`）|

例

```json:例
[
  {
    "token": "725903f5b62f56118f4094b46a4470d8",
    "channel": "CAM_FRONT",
    "modality": "camera"
  },
]
```

#### calibrated_sensor.json

センサのキャリブレーション情報(自車`ego_vehicle`のbody frameに対する相対位置や、カメラの内部パラメータ)の一覧を表します。

|フィールド名|型|内容|
|---|---|---|
|sensor_token|int|該当するsensorのtoken|
|translation|list[float]|自車body frameに対するセンサの位置情報(xyz)|
|rotation|list[float]|自車body frameに対するセンサの回転情報(quaternion)|
|camera_intrinsic|list[float]|カメラの内部パラメータ(カメラのみ)|

例

```json:例
[
  {
    "token": "1d31c729b073425e8e0202c5c6e66ee1",
    "sensor_token": "725903f5b62f56118f4094b46a4470d8",
    "translation": [
      1.70079118954,
      0.0159456324149,
      1.51095763913
    ],
    "rotation": [
      0.4998015430569128,
      -0.5030316162024876,
      0.4997798114386805,
      -0.49737083824542755
    ],
    "camera_intrinsic": [
      [
        1266.417203046554,
        0.0,
        816.2670197447984
      ],
      [
        0.0,
        1266.417203046554,
        491.50706579294757
      ],
      [
        0.0,
        0.0,
        1.0
      ]
    ]
  },
]
```

#### ego_pose.json

各時刻でのセンサの姿勢情報を表します。

|フィールド名|型|内容|
|---|---|---|
|timestamp|int|取得した時刻のタイムスタンプ|
|rotation|list[float]|車両姿勢の回転情報(quaternion)|
|translation|list[float]|車両姿勢の位置情報(xyz)|

```json:例
[
  {
    "token": "5ace90b379af485b9dcb1584b01e7212",
    "timestamp": 1532402927814384,
    "rotation": [
      0.5731787718287827,
      -0.0015811634307974854,
      0.013859363182046986,
      -0.8193116095230444
    ],
    "translation": [
      410.77878632230204,
      1179.4673290964536,
      0.0
    ]
  },
]
```

#### log.json

ログ（シーンと車両・マップの紐づけに使う）の一覧を表します。

|フィールド名|型|内容|
|---|---|---|
|logfile|str|？|
|vehicle|str|車両名|
|date_captured|str|取得日|
|location|str|走行したマップの名称|

例

```json:例
[
  {
    "token": "7e25a2c8ea1f41c5b0da1e69ecfa71a2",
    "logfile": "n015-2018-07-24-11-22-45+0800",
    "vehicle": "n015",
    "date_captured": "2018-07-24",
    "location": "singapore-onenorth"
  },
]
```

#### map.json

マップ情報と紐づくログの一覧を表します

|フィールド名|型|内容|
|---|---|---|
|category|str|？|
|filename|str|マップのラスタファイルのパス|
|log_tokens|list[UUID]|紐づくログのtokenのリスト|

例

```json:例
[
  {
    "category": "semantic_prior",
    "token": "37819e65e09e5547b8a3ceaefba56bb2",
    "filename": "maps/37819e65e09e5547b8a3ceaefba56bb2.png",
    "log_tokens": [
      "853a9f9fe7e84bb8b24bff8ebf23f287",
      "e55205b1f2894b49957905d7ddfdb96d",
      "8fefc430cbfa4c2191978c0df302eb98",
      "f93e8d66ce4b4fbea7062d19b1fe29fb",
      "89a56a5dc3aa4e56a2e57b52de738da5"
    ]
  }
]
```
