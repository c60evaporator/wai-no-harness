# metadata-fields.md
nuScenes Map Expansionのメタデータの各フィールドの内容とフォーマットを記載

**トークンはすべてハイフン付きUUIDであることに注意**

## polygon
ポリゴンで表されるアノテーション (drivable_area, road_segment, road_block, lane, lane_connector, carpark_area, stop_line, ped_crossing, walkway)。

|フィールド名|型|概要|Nullable|
|---|---|---|---|
|token|UUID|IDを表すトークン|False|
|exterior_node_tokens|UUID|外形の頂点を表す点(node)のtoken一覧|False|
|holes|list[dict[str,UUID]]|穴の頂点を表す点(node)のtoken一覧|False（空リストは可）|

```json
[
    {
        "token": "a60970c7-86cd-4169-ae9a-b9b51e4ec950",
        "exterior_node_tokens": ["3af81dd8-b5b5-4c2b-812b-915f7c780997", "5b68ea07-a1b5-4ecd-95b6-8893e1beb24f", "8f321957-55d9-4c01-91d9-61aa7158918f", "7a8c11fb-517e-4ae0-ad71-37cfdf136452"],
        "holes": [
            {
                "node_tokens": ["1b58a0cc-b57e-49ff-b536-9a94dd34d458", "aaab7288-1c55-4cfb-916a-d06888ad84de", "a4a5bb33-af31-4b93-9198-e7091b91d1ce", "81a4487d-4671-49f7-be28-604914814d8b"]
            },
        ]
    },
]
```

## line
折れ線で表されるアノテーション (road_divider, lane_divider)。road_blockとlane（from_edge_line, to_edge_line）も補助的に使用

|フィールド名|型|概要|Nullable|
|---|---|---|---|
|token|UUID|IDを表すトークン|False|
|node_tokens|UUID|頂点を表す点(node)のtoken一覧|False|

```json
[
    {
        "token": "98c91318-5854-41ac-9210-001b57b8185f", 
        "node_tokens": ["4e2605d4-b9f4-41f9-a03c-032c8d4a3c24", "1cbbdda6-5ee6-4b4d-8bcc-30af18094978"]
    }
]
```

## node
点で表されるアノテーション、polygonとlaneの実際の座標を保持している

|フィールド名|型|概要|Nullable|
|---|---|---|---|
|token|UUID|IDを表すトークン|False|
|x|float|点のX座標 (左端を原点としたメートル単位)|False|
|y|float|点のX座標 (上端を原点としたメートル単位)|False|

```json
[
    {
        "token": "2163fdc8-77fc-4c1c-a099-70bc5be9f9b7",
        "x": 994.6139837360693,
        "y": 1054.5199816348131
    },
]
```

## drivable_area
連続して運転可能なエリアを表す

|フィールド名|型|概要|Nullable|
|---|---|---|---|
|token|UUID|IDを表すトークン|False|
|polygon_tokens|list[UUID]|構成するpolygonのtoken一覧|False|

```json
{
    "token": "c3e28556-b711-4581-9970-b66166fb907d", 
    "polygon_tokens": ["fff7b0c9-1eaf-4988-afe3-e4e4607f85e3", "d235013d-2a07-4181-9862-c666b49a79b4", "0bbf311c-405d-433b-a097-7d9c292a9b87", "b4dfb634-2721-42d9-aa5d-0f8ec9a2fa31", "c4b4c925-6ddb-4e4b-a4ca-609e1ca626c2", "a60970c7-86cd-4169-ae9a-b9b51e4ec950", "1209379e-bc10-4d65-9fb1-0ee938032130"]
}
```

## road_segment
交差点や車線増減ごとに分割された道路エリアを表す。上下両車線を含み、交差点自身も含む。

|フィールド名|型|概要|Nullable|
|---|---|---|---|
|token|UUID|IDを表すトークン|False|
|polygon_token|UUID|構成するpolygonのtoken|False|
|is_intersection|bool|交差点かどうか|False|
|drivable_area_token|UUID|対応するdrivable_areaのtoken|True|

```json
{
    "token": "006f28b3-2b4c-4221-8957-d3b7f5739d3d",
    "polygon_token": "255d40c0-9c80-434d-9b8e-742c8672ec69",
    "is_intersection": true,
    "drivable_area_token": ""
}
```

## road_block
road_segmentの上下両車線を分離したもの

|フィールド名|型|概要|Nullable|
|---|---|---|---|
|token|UUID|IDを表すトークン|False|
|polygon_token|UUID|構成するpolygonのtoken|False|
|from_edge_line_token|UUID|road_blockの後端のlineのtoken|True|
|to_edge_line_token|UUID|road_blockの前端のlineのtoken|True|
|road_segment_token|UUID|対応するroad_segmentのtoken|False|

```json
{
    "token": "002d8233-c9bf-4a9b-9d53-be86cd6cf73f", 
    "polygon_token": "29fc4c78-75ae-4777-adab-f33d93591661", 
    "from_edge_line_token": "b0d2163e-732b-4be6-b6f7-2add8b4c7e8f",
    "to_edge_line_token": "7ce97362-1133-4c19-a73c-5cfa8f0d64f0", 
    "road_segment_token": "85a06614-958c-461f-bc11-6cadd68efa7d"
}
```

## lane
road_blockを車線ごとに分離したもの

|フィールド名|型|概要|Nullable|
|---|---|---|---|
|token|UUID|IDを表すトークン|False|
|polygon_token|UUID|構成するpolygonのtoken|False|
|lane_type|str|laneの種類 (`CAR`)|False|
|from_edge_line_token|UUID|laneの後端のline|True|
|to_edge_line_token|UUID|laneの前端のline|True|
|left_lane_divider_segments|list[dict[str,UUID]]|laneの左端のlane_dividerの位置と白線の種類|True|
|right_lane_divider_segments|list[dict[str,UUID]]|laneの右端のlane_dividerの位置と白線の種類|True|

```json
{
    "token": "02febd64-12a7-4b3e-9cd0-a108f1b52c27",
    "polygon_token": "7e009c98-6f1a-4ae8-a230-b2d81f597b0a",
    "lane_type": "CAR",
    "from_edge_line_token": "f762542c-3b9c-49d9-8c40-5d66f7b1b97a",
    "to_edge_line_token": "9098214a-6919-4763-9bf3-909a81430634",
    "left_lane_divider_segments": [
        {"node_token": "d71e9d84-2ea6-4838-89b7-1748747f61e2",
        "segment_type": "DOUBLE_DASHED_WHITE"},
        {"node_token": "05910631-3254-409d-becd-4ff52cc8302a",  
        "segment_type": "DOUBLE_DASHED_WHITE"}
    ],
    "right_lane_divider_segments": [
        {"node_token": "4de92a39-57ec-47ef-a127-0c2468528f18", "segment_type": "DOUBLE_DASHED_WHITE"},
        {"node_token": "10954e68-814a-4226-96cf-041fd69d4f4e", "segment_type": "DOUBLE_DASHED_WHITE"}
    ]
}
```

またlaneはパスを表すarcline形式のアノテーションも持っており、laneのtokenを使って`arcline_path_3`とも紐づけられる

## lane_connector
lane同士の接続パス

|フィールド名|型|概要|Nullable|
|---|---|---|---|
|token|UUID|IDを表すトークン|False|
|outgoing|UUID|構成するpolygonのtoken (常に長方形なので、形状にあまり意味はない)|False|

```json:例
{
    "token": "345b7add-6ef7-46ea-9589-00c1173aaf16",
    "polygon_token": "aca616b5-6cb9-4434-ad01-d5e0a1890490"
}
```

## road_divider
道路の上下線の境目となる線（中央分離帯は含まず、白線で区切られたもののみを示す）

|フィールド名|型|概要|Nullable|
|---|---|---|---|
|token|UUID|IDを表すトークン|False|
|line_token|UUID|構成するlineのtoken|False|
|road_segment_token|UUID|該当するroad_segment|False|

```json
{
    "token": "00bbfc65-0b44-4b4c-b517-6d87dc02529c",
    "line_token": "98c91318-5854-41ac-9210-001b57b8185f",
    "road_segment_token": "b1ed2f76-bfcd-4b0c-b367-7a20cf707b95"
}
```

## lane_divider
道路の同方向の車線の境目

|フィールド名|型|概要|Nullable|
|---|---|---|---|
|token|UUID|IDを表すトークン|False|
|line_token|UUID|構成するlineのtoken|False|
|lane_divider_segments|list[dict[str,UUID]]|lane_divider各点の白線の種類|False（空リストは可）|

```json
{
    "token": "00569b72-a7dc-4cdf-9bf3-7f3583c6dbae",
    "line_token": "9ac741dc-20b5-44f3-9f0a-41e371a722ee",
    "lane_divider_segments": [
        {"node_token": "57d546eb-682c-4540-871c-2e8d6a67f2de",  
         "segment_type": "DOUBLE_DASHED_WHITE"},
        {"node_token": "fef2c634-7096-4b48-bf87-6575d2a67b56", 
         "segment_type": "DOUBLE_DASHED_WHITE"},
        {"node_token": "153990f1-b0da-4243-a065-e4a99d29e180",  
         "segment_type": "DOUBLE_DASHED_WHITE"},
        {"node_token": "8ad3000f-c1e9-4eda-8bf1-c5f64a879c54", 
         "segment_type": "NIL"}
    ]
}
```

## ped_crossing
横断歩道

|フィールド名|型|概要|Nullable|
|---|---|---|---|
|token|UUID|IDを表すトークン|False|
|polygon_token|UUID|構成するpolygonのtoken|False|
|road_segment_token|UUID|対応するroad_segmentのtoken|False|

```json
{
    "token": "027c4ccd-56c9-4980-9949-1d42bb36f23c",
    "polygon_token": "62138b18-6dd1-4c1e-8f11-7a2c8d5783c8",
    "road_segment_token": "af7744d2-6dfe-4b9f-ab9a-58cc155f3f08"
}
```

## walkway
歩道

|フィールド名|型|概要|Nullable|
|---|---|---|---|
|token|UUID|IDを表すトークン|False|
|polygon_token|UUID|構成するpolygonのtoken|False|

```json
{
    "token": "00a01743-8d10-41ca-849e-ef6a32bee77d",
    "polygon_token": "17ff2a4b-a5c2-41d2-abf5-4a8aa07cb30f"
}
```

## stop_line
停止線

|フィールド名|型|概要|Nullable|
|---|---|---|---|
|token|UUID|IDを表すトークン|False|
|polygon_token|UUID|構成するpolygonのtoken|False|
|stop_line_type|str|停止線の種類|False|
|ped_crossing_tokens|list[UUID]|対応するped_crossingのtokenのリスト|False（空リストは可）|
|traffic_light_tokens|list[UUID]|対応するtraffic_lightのtokenのリスト|False（空リストは可）|
|road_block_token|UUID|対応するroad_blockのtoken|True|

```json
{
    "token": "009cf7f7-b428-49e8-976a-2507bdf24cc3",
    "polygon_token": "0430a2e0-5fe7-4a97-be7f-f86369adb4c1",
    "stop_line_type": "TRAFFIC_LIGHT",
    "ped_crossing_tokens": [],
    "traffic_light_tokens": ["182079de-ffeb-48fe-a9a4-ae1ed0870714", "51edd45a-b57a-496e-96b0-7c649e4831ed", "cc19ad44-15c8-4cea-bf71-c1023cc1b280", "589e639e-81aa-4ff1-be26-c5b36d04e5c6"],
    "road_block_token": "fcf80474-21be-44b5-93d4-b05cc2864280"
}
```

## carpark_area
駐車スペース

|フィールド名|型|概要|Nullable|
|---|---|---|---|
|token|UUID|IDを表すトークン|False|
|polygon_token|UUID|構成するpolygonのtoken|False|
|orientation|float|方向|False|
|road_block_token|UUID|対応するroad_blockのtoken|False|

```json
{
    "token": "0782a606-7637-4190-94b5-72f212119413",
    "polygon_token": "f7fbde12-6895-4dc1-b83c-7fa2fc4c9897",
    "orientation": 0.36144074186203157,
    "road_block_token": "0b23e9db-9839-4a84-9a31-4029c37fdf37"
}
```

## traffic_light
信号機

|フィールド名|型|概要|Nullable|
|---|---|---|---|
|token|UUID|IDを表すトークン|False|
|line_token|UUID|構成するlineのtoken (poseと同情報)|False|
|traffic_light_type|str|信号機の種類（`VERTICAL`,`HORIZONTAL`）|False|
|from_road_block_token|UUID|対応するroad_blockのtoken|False|
|items|list[dict]|信号機の赤青黄の位置等の詳細を記載|False（空リストは可）|
|pose|dict|信号機の姿勢（位置＋方向）|False|

```json
{
    "token": "00590fed-3542-4c20-9927-f822134be5fc",
    "line_token": "5bffb006-bce8-44a4-a466-5580f1d748fd",
    "traffic_light_type": "VERTICAL",
    "from_road_block_token": "71c79c48-819c-4b17-ad2HORIZONTAL-2a9e82ba1596",
    "items": [
        {"color": "RED", "shape": "CIRCLE", "rel_pos": {"tx": 0.0, "ty": 0.0, "tz": 0.632, "rx": 0.0, "ry": 0.0, "rz": 0.0}, "to_road_block_tokens": []}, 
        {"color": "YELLOW", "shape": "CIRCLE", "rel_pos": {"tx": 0.0, "ty": 0.0, "tz": 0.381, "rx": 0.0, "ry": 0.0, "rz": 0.0}, "to_road_block_tokens": []},
        {"color": "GREEN", "shape": "CIRCLE", "rel_pos": {"tx": 0.0, "ty": 0.0, "tz": 0.13, "rx": 0.0, "ry": 0.0, "rz": 0.0}, "to_road_block_tokens": []},
        {"color": "GREEN", "shape": "RIGHT", "rel_pos": {"tx": 0.0, "ty": -0.26, "tz": 0.13, "rx": 0.0, "ry": 0.0, "rz": 0.0}, "to_road_block_tokens": ["bd26d490-8822-469b-ae60-74f6c0c9e1cb"]}
    ],
    "pose": {"tx": 369.2207339994191, "ty": 1129.3945093980494, "tz": 2.4, "rx": 0.0, "ry": 0.0, "rz": -0.6004778487509836}
}
```

"items"フィールドにはリスト形式で各ライトの位置や種類を保持している。各要素は以下の意味を持つ
- "pose"フィールドとリストの各要素の"rel_pos"フィールドの合成poseで、各ライトの位置と方向が分かる
- リストの各要素の"shape"フィールドに以下のようにライト形状が格納されている
    - CIRCLE: 通常の赤緑黄のライト
    - RIGHT: 右向き矢印
    - LEFT: 左向き矢印
    - UP: 前向き矢印
- "shape"がRIGHT,LEFT,UPの場合、その矢印の進む先にあるroad_blockが"to_road_block_tokens"フィールドに格納されている
- リストの各要素の"color"フィールドに以下のようにライトの色が格納されている
    - GREEN: 緑色
    - YELLOW: 黄色
    - RED: 赤色

## canvas_edge
メートル単位のMapのサイズを`[w, h]`で指定

```json
[1585.6, 2025.0]
```

## arcline_path_3
[Dubins path](https://myenigma.hatenablog.com/entry/2017/05/01/144956)と呼ばれる形式で記録された、円弧パスのアノテーション。
※このフィールドのみリスト形式ではなくLaneやLane connectorのtokenをkeyとしたdictになっている

|フィールド名|型|概要|Nullable|
|---|---|---|---|
|start_pose|list[float]|旋回開始姿勢 (x, y, yaw)|False|
|end_pose|list[float]|旋回終了姿勢 (x, y, yaw)|False|
|shape|str|コースカテゴリ（`LRL`,`RLR`,`LSL`,`LSR`,`RSL`,`RSR`）|False|
|radius|float|旋回半径|False|
|segment_length|list[float]|信号機の赤青黄の位置等の詳細を記載|False|

```json
"arcline_path_3": {
    "724c1eea-4f02-4d48-9465-c8afc0445c9f": [
        {
            "start_pose": [784.4807911377701, 1889.4182732702996, 0.23426813461523752],
            "end_pose": [804.6818385337588, 1891.580100889031, -0.03626940290556443],
            "shape": "RSR",
            "radius": 71.1115664877138,
            "segment_length": [0.00016042214627488553, 1.146545252879975, 19.238187664686603]
        },
        {
            "start_pose": [804.6818385337588, 1891.580100889031, -0.03626940290556443],
            "end_pose": [810.6731869344062, 1891.0965872766553, -0.12464973712793109],
            "shape": "RSR",
            "radius": 67.9285431418773,
            "segment_length": [6.001598757692033, 0.009242372903952889, 0.0019485884255349205]
        }
    ],
}
```

## connectivity
arcline_path_3同士の接続を表す。arcline_path_3のtoken（laneまたはlane_connectorのtokenともみなせる）をキーとしたdict形式。

|フィールド名|型|概要|Nullable|
|---|---|---|---|
|incoming|list[UUID]|接続元のlaneまたはlane_connectorのtokenのリスト|False|
|outgoing|list[UUID]|接続先のlaneまたはlane_connectorのtokenのリスト|False|

```json:例
"532d610d-70b4-43d7-8097-d8ebe8e3870b": {
    "incoming": [
        "f3b40393-5301-4a20-a3da-823c5c1d129f"
    ],
    "outgoing": [
        "345b7add-6ef7-46ea-9589-00c1173aaf16",
        "ce1d134b-0d81-4f4f-a249-10d97de8a7d9"
    ]
}
```

incomingまたはoutgoingが複数ある場合は交差点に相当
