---
name: drive-nuscenes-visualization
description: "nuScenesデータセットの可視化に関する説明。特にフロントエンドでの描画時の注意点を中心に説明。Use when user visulizes the nuScenes dataset, especially when user mentions frontend rendering."
description-en: "Description of the visualization of the nuScenes dataset. Use when user mentions frontend rendering."
description-ja: "nuScenesデータセットの可視化に関する説明。特にフロントエンドでの描画時の注意点を中心に説明。"
allowed-tools: ["Read", "Write", "Edit", "Bash", "Grep", "Glob"]
argument-hint: "<entity-name>"
user-invocable: false
---

## 各データの座標変換
グローバル座標（3Dバウンディングボックス等のアノテーションが従う座標系）と、各データの座標系との変換について、フロントエンドでの描画を前提に説明する。

### basemapの座標系

**座標系の定義**

NuScenesのbasemapは各ロケーション（`boston-seaport` 等）ごとに1枚のPNG画像として提供される。座標系は以下の通り：

- **グローバルメートル座標**：マップ左下端を原点とし、右方向がX正、上方向がY正のメートル単位座標
- **元画像ピクセル座標**：左上端を原点とし、右方向がX正、下方向がY正のピクセル座標
- **canvas_edge**：各マップのメートル単位サイズ `[width_m, height_m]`。`NuScenesMap.canvas_edge` から取得可能
- **resolution**：固定値 `0.1 m/px`（= 10 px/m）

**グローバルメートル座標 → 元画像ピクセル座標**

devkitの `MapMask.to_pixel_coords()` と同一の変換式：

```typescript
// transform_matrix（singapore-onenorthの場合）：
// [[ 10,   0,  0,      0],
//  [  0, -10,  0,  20250],   ← canvasH_px = canvas_edge[1] / resolution
//  [  0,   0,  1,      0],
//  [  0,   0,  0,      1]]

const canvasH_px = canvasEdge[1] / resolution  // 例: 2025.0 / 0.1 = 20250

const px =  x / resolution          // x方向: Y軸反転なし
const py = -y / resolution + canvasH_px  // y方向: Y軸反転 + オフセット
```

**各マップのcanvas_edge（NuScenesMap.canvas_edgeで確認済み）**

```typescript
const NUSCENES_MAP_META = {
  'boston-seaport':            { canvasEdge: [2979.5, 2118.1], resolution: 0.1 },
  'singapore-onenorth':        { canvasEdge: [1585.6, 2025.0], resolution: 0.1 },
  'singapore-hollandvillage':  { canvasEdge: [2808.3, 2922.9], resolution: 0.1 },
  'singapore-queenstown':      { canvasEdge: [3228.6, 3687.1], resolution: 0.1 },
}
```

**注意：元画像サイズとcanvas_edgeは対応しない**

各マップの元画像サイズ（`file` コマンドで確認）：

```
boston-seaport:            32286 x 36871 px
singapore-onenorth:        29795 x 21181 px
singapore-hollandvillage:  15856 x 20250 px
singapore-queenstown:      28083 x 29229 px
```

`canvas_edge / resolution` で計算されるピクセルサイズと元画像サイズは一致しない。変換には `canvas_edge` と `resolution` のみを使い、元画像サイズは使わない。

**BEV表示時のbasemap切り出し・回転（devkitのrender_ego_centric_mapと同等）**

```typescript
// 1. Ego poseのピクセル座標を計算
const px =  egoX / resolution
const py = -egoY / resolution + canvasH_px

// 2. axes_limit をピクセルに換算（devkitのaxes_limit=40mに相当）
const axesLimitPx = axesLimitMeters / resolution  // 40 / 0.1 = 400px

// 3. √2倍の範囲で切り出し（回転後クリッピング防止）
const cropSize = Math.ceil(axesLimitPx * Math.sqrt(2))

// 4. OffscreenCanvasで切り出し
offCtx.drawImage(bitmap,
  (px - cropSize) * scaleX, (py - cropSize) * scaleY,
  cropSize * 2 * scaleX, cropSize * 2 * scaleY,
  0, 0, cropSize * 2, cropSize * 2,
)

// 5. yaw角で回転（NuScenes BEV座標系に合わせる）
// グローバル座標のY軸（上正）→ Canvas Y軸（下正）の反転が必要
const yaw = Math.atan2(2*(w*qz + qx*qy), 1 - 2*(qy*qy + qz*qz))
rotCtx.translate(cropSize, cropSize)
rotCtx.scale(1, -1)   // Y軸反転（NuScenes Y軸は上正、Canvas Y軸は下正）
rotCtx.rotate(yaw)    // yaw回転（符号はそのまま）
rotCtx.translate(-cropSize, -cropSize)
rotCtx.drawImage(offscreen, 0, 0)

// 6. 中央からaxesLimitPxの範囲を再切り出してCanvasに描画
ctx.drawImage(rotCanvas,
  cropSize - axesLimitPx, cropSize - axesLimitPx,
  axesLimitPx * 2, axesLimitPx * 2,
  0, 0, size, size,
)
```

**BEV表示後の点群描画時の注意**

basemapをY軸反転して描画した後、点群を重ねる際は点群側もY軸反転して描画する：

```typescript
// 点群・BBoxはY軸反転したCanvas座標系で描画する
ctx.save()
ctx.translate(0, size)
ctx.scale(1, -1)
drawPointCloud(ctx, points, viewParams, ...)
// BBox描画もこのsave/restore内で行う
ctx.restore()
```

### カメラ画像の座標系

**座標系の定義**

- **グローバル座標** → **Ego座標系**（自車中心）→ **センサー座標系**（カメラ中心）→ **画像ピクセル座標** の順に変換する
- カメラのZ軸が前方、X軸が右方向、Y軸が下方向（OpenCV標準）

**グローバル座標 → 画像ピクセル座標の変換**

```typescript
// 1. グローバル → Ego座標系
const R_ego_T = transpose(quatToRotMat(egoPose.rotation))
const p_ego = matVecMul(R_ego_T, vecSub(point, egoPose.translation))

// 2. Ego → センサー座標系
const R_cs_T = transpose(quatToRotMat(calibSensor.rotation))
const p_cam = matVecMul(R_cs_T, vecSub(p_ego, calibSensor.translation))

// 3. カメラ前方（z > 0）でない場合は投影不可
if (p_cam[2] <= 0) return null

// 4. ピンホールカメラモデルで画像座標に投影
const u = intrinsic[0][0] * (p_cam[0] / p_cam[2]) + intrinsic[0][2]  // fx * x/z + cx
const v = intrinsic[1][1] * (p_cam[1] / p_cam[2]) + intrinsic[1][2]  // fy * y/z + cy
```

**camera_intrinsicの形式**

APIから `CalibratedSensor.camera_intrinsic` として返される3×3行列（LiDAR・RADARは`null`）：

```
[[fx,  0, cx],
 [ 0, fy, cy],
 [ 0,  0,  1]]
```

**BBox投影に使うego_poseはカメラ固有のものを使う**

devkitは各カメラのBBox投影に、そのカメラのsample_dataに紐づくego_poseを使用する。LIDAR_TOPのego_poseとは数十msのタイムラグがあり、同一のego_poseを全センサーで使い回すと小さなオブジェクトで誤差が生じる。

バックエンドに `GET /sensor-data/{token}/ego-pose` エンドポイントを実装し、`sample_data.ego_pose_token` からEgoPoseを返す：

```python
@router.get("/sensor-data/{token}/ego-pose", response_model=EgoPoseResponse)
async def get_sensor_data_ego_pose(token: str, db: AsyncSession = Depends(get_db)):
    """SampleDataに紐づくEgoPoseを取得する（カメラBBox投影用）"""
    pose = await SensorRepository(db).get_ego_pose_by_sample_data_token(token)
    if not pose:
        raise HTTPException(status_code=404, detail="EgoPose not found")
    return SensorConverter.to_ego_pose_response(pose)
```

フロントエンドでは `useSensorDataEgoPose(camBrief.token)` で各カメラのego_poseを取得し `CameraImageCanvas` に渡す。ego_poseが未取得の場合はLIDAR_TOPのego_poseにフォールバックすることで初回レンダリングからBBoxを表示できる：

```typescript
// SensorCell.tsx
const camBrief = channel.startsWith('CAM_') ? sampleDataMap[channel] : null
const { data: camEgoPose } = useSensorDataEgoPose(camBrief?.token ?? null)

// CameraImageCanvasにはカメラ固有のego_poseを優先して渡す
egoPose={camEgoPose ?? currentEgoPose}
```

**カメラ画像上にBBoxを重ねて表示する際の注意点**

カメラ画像をCanvasに描画しその上にBBox用のCanvasを重ねる場合、以下の点に注意する：

- 画像Canvasの `width/height` 属性は元画像の解像度（例: 1600×900）で設定し、CSSの `width: 100%` で表示サイズを調整する
- BBox用Canvasは画像Canvasの表示サイズ（`getBoundingClientRect()`で取得）に合わせてサイズを設定する。`devicePixelRatio` を考慮しないとRetinaディスプレイでBBoxがずれる：

```typescript
const dpr = window.devicePixelRatio || 1
const imgRect = imgCanvas.getBoundingClientRect()

bboxCanvas.width  = imgRect.width  * dpr
bboxCanvas.height = imgRect.height * dpr
bboxCanvas.style.width  = imgRect.width  + 'px'
bboxCanvas.style.height = imgRect.height + 'px'

const ctx = bboxCanvas.getContext('2d')!
ctx.scale(dpr, dpr)  // 以降はCSS座標系で描画できる
```

- BBoxの座標は元画像スケール（例: 1600×900）で計算し、`imgRect.width / naturalWidth` のスケールを掛けてCSS座標系に変換する
- ウィンドウリサイズ時にBBoxの位置がずれないよう、`ResizeObserver` でコンテナサイズの変化を監視してBBoxを再描画する：

```typescript
useEffect(() => {
  const observer = new ResizeObserver(() => {
    if (bitmapRef.current) drawBBoxesRef.current?.()
  })
  observer.observe(containerRef.current!)
  return () => observer.disconnect()
}, [])
```

**BBox座標がNaNになる場合の確認順序**

1. `ann.rotation` がAPIから正しい値で返っているか（型定義の不一致で `.w` などが `undefined` になっていないか）
2. `calibArray.translation/rotation` が `undefined` になっていないか
3. `egoPose` が選択中のSampleに対応した値か
4. `bboxCanvas` のサイズが `devicePixelRatio` を考慮しているか

### LiDAR点群の座標系

**座標系の定義**

- LiDAR点群は**センサー座標系**（LIDAR_TOP中心）で格納されている
- X軸が前方、Y軸が左方向、Z軸が上方向（右手座標系）
- 各点は `[x, y, z, intensity]` の4要素（5列目のring_indexは除外）

**BEV（鳥瞰図）表示時の座標変換**

センサー座標系のままBEVとしてCanvas描画する場合：

```typescript
// センサー座標系 → BEVピクセル座標
// X軸（前方）→ Canvas上方向
// Y軸（左方向）→ Canvas左方向
const cx = size / 2
const cy = size / 2

const px = cx + (y - offsetY) * scale   // Y軸 → 画面X
const py = cy - (x - offsetX) * scale   // X軸 → 画面Y（反転）
```

**BBoxをBEV上に描画する場合**

アノテーションはグローバル座標で格納されているため、センサー座標系に変換してから描画する：

```typescript
// グローバル → センサー座標系
// 1. グローバル → Ego座標系
const R_ego_T = transpose(quatToRotMat(egoPose.rotation))
const p_ego = matVecMul(R_ego_T, vecSub(point, egoPose.translation))

// 2. Ego → センサー座標系
const R_cs_T = transpose(quatToRotMat(calibSensor.rotation))
const p_sensor = matVecMul(R_cs_T, vecSub(p_ego, calibSensor.translation))
```

**basemapとBEVを重ねる場合のY軸の扱い**

basemapのY軸（グローバル座標、上正）とLiDAR点群のBEV Y軸（Canvas座標、下正）は逆方向になる。basemapをY軸反転して描画した後、点群を重ねる際は点群もY軸反転して描画することで位置が一致する（前節「basemapの座標系」の実装例を参照）。

### RADAR点群の座標系

**座標系の定義**

RADARの点群は各センサー（`RADAR_FRONT`、`RADAR_BACK_LEFT` 等）固有の座標系で格納されている。
BEV表示にはLiDAR_TOP座標系への変換が必要。devkitの `from_file_multisweep()` はこの変換を内部で行っているが、独自実装では明示的に変換する必要がある。

**BEV表示時の座標変換（RADAR → LIDAR_TOP座標系）**

```
RADAR座標系 → Ego座標系 → LIDAR_TOP座標系
```

```python
from pyquaternion import Quaternion

# RADAR座標系 → Ego座標系
pt = radar_rot.rotate(pt) + radar_trans

# Ego座標系 → LIDAR_TOP座標系
pt = lidar_rot.inverse.rotate(pt - lidar_trans)
```

変換後の点群はLiDARと同じBEV描画処理で表示できる。

**実装上の注意**

- バックエンドでAPIレスポンス時に変換する方が、フロントエンドの描画ロジックを共通化できる
- クエリパラメータ `ref_sensor_token`（LIDAR_TOPのcalibrated_sensor_token）をフロントから渡し、バックエンドで変換する
- RADARにはBBoxアノテーションを重ねない（アノテーションはLiDAR基準のため座標系が異なる）
- RADARは点数が少ない（数十点）ためpointSizeを大きく（4px程度）設定するとよい
