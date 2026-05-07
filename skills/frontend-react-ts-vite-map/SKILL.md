---
name: frontend-react-ts-vite-map
description: "タブで画面遷移する地図描画アプリケーションのフロントエンド実装。React + TypeScript + ViteでUIを構築し、必要に応じてDeck.glやLeafletを使用して地図上に点や線を描画する。ユーザーが「Leaflet」「Deck.gl」「PostGIS」「map application」「GIS」などに言及した際は必ずこのスキルを参照すること。自動運転や地図に関係したアプリ作成、可視化タスクも適用する。"
---

# frontend-react-ts-vite-deckgl
タブで画面遷移する地図描画アプリケーションのフロントエンド実装。React + TypeScript + ViteでUIを構築し、必要に応じてDeck.glやLeafletを使用して地図上に点や線を描画する。

## Tech Stack
- 描画:     Deck.gl 9.x（大量データの描画時のみ使用） + Leaflet 1.x（地図基盤必要時のみ使用）
- UI:       React 19 + TypeScript 5.x + Vite 6.x
- スタイル:  Tailwind CSS 4.x + shadcn/ui
- 状態管理:  Zustand 5.x
- API通信:  TanStack Query（@tanstack/react-query）5.x
- フォーム:  React Hook Form 7.x + Zod 3.x（アノテーション編集時のみ使用）
- テスト:    Vitest 3.x

## Directory Structure
root/
├── docker-compose.yml
├── .env
└── frontend/
    ├── Dockerfile
    ├── .env.production  # VITE_API_BASE_PATHでバックエンドAPIのベースパスを指定（AWS環境用。ローカル環境では使用しない）
    ├── vitest.config.ts
    ├── package.json
    ├── package-lock.json
    ├── tsconfig.json
    ├── tailwind.config.js
    ├── postcss.config.js
    ├── nginx.conf
    ├── src/
    │   ├── types/          # 型定義（バックエンドschemas/と対応）
    │   │   └── 各リソースの型定義用tsファイル
    │   ├── api/            # TanStack Query hooks + apiFetch
    │   │   ├── client.ts         # apiFetch関数（全API呼び出しの共通関数）
    │   │   └── 各リソースのAPI呼び出し関数と対応するuseQuery/useMutationフック
    │   ├── store/          # Zustand stores
    │   │   ├── viewerStore.ts       # 選択状態
    │   │   ├── navigationStore.ts   # 画面遷移ロック
    │   │   └── その他必要に応じて作成
    │   ├── layers/         # Deck.glレイヤー定義
    │   │   └── 各タブのレイヤー定義ファイル
    │   ├── lib/
    │   │   ├── coordinateUtils.ts  # 3D→2D投影・座標変換
    │   │   ├── canvasUtils.ts      # Canvas描画ユーティリティ
    │   │   └── utils.ts            # shadcn/ui用cn関数
    │   ├── pages/          # 各タブに対応するページコンポーネント
    │   │   └── 各タブのページコンポーネントtsxファイル
    │   └── components/
    │       ├── ui/         # shadcn/uiコンポーネント（自動生成）
    │       ├── layout/     # Header, MainLayout, LeftPane, RightPane
    │       ├── common/     # MapCanvas, PointCloudCanvas, CameraImageCanvas 等の共通描画コンポーネント
    │       └── 各タブ固有のUIコンポーネント
    ├── tests/
    │   └── unit/
    │       ├── lib/        # coordinateUtils.test.ts, canvasUtils.test.ts
    │       └── store/      # navigationStore.test.ts
    └── config/
        └── settings.yml    # アプリ全体の設定ファイル（例：APIのbaseURLなど）

## Docker
- Dockerfileは`references/Dockerfile`をベースに、フロントエンド処理に必要なパッケージのインストールとビルドコマンドを追加する。
- docker-compose.ymlは`references/docker-compose.yml`をベースに、プロジェクトに合わせてイメージ名やビルドコンテキスト、環境変数等を適切に設定し、バックエンドサービス等を追加する。バックエンドとの通信には`frontend-network`を使用する。

## API
- baseURL: /api/v1
- クライアント: src/api/client.ts の apiFetch を必ず経由する
- コンポーネントから直接fetchを呼ばない
- パスの末尾は、`/`なしで統一する（例：`/api/v1/scenes`、`/api/v1/scenes/{scene_id}/samples`）

### 型定義
- `src/types/` がフロントエンドの唯一の型定義
- バックエンドの `schemas/` と1対1で対応させる
- Claude Codeは型を勝手に作らず必ず `src/types/` を参照する

## レイアウト共通仕様
- 全体: 明記がなければ3ペイン構成（左280px固定 / 中央flex / 右280px固定）
- ヘッダー: 上部固定バー（黒背景）
  - 左端: プルダウンで最上位のリソースを選択
  - 残り: 各画面を遷移させるタブ
  - アクティブタブは青文字
- 左ペイン: 上部フィルタ群（濃いグレー背景） + リスト（白背景・枠線あり）
- 左ペインのリストアイテムクリックで中央ペインの内容が切り替わる動作が基本
- 中央ペイン: 地図描画（Deck.gl or Canvas）、カメラ等の画像表示、その他ビジュアライゼーション
- 右ペイン: 左ペインまたは中央ペインのクリックに応じて表示されるテキスト情報エリア + 下部にアクションボタン（青）
- ボタン色: #4A90D9（青）
- フィルタUI背景色: #606060（濃いグレー）

## State Management（Zustand）
### navigationStore
本来はタブで遷移する画面に対して、ボタンによる画面遷移時のフィルタ引き継ぎを管理する。例えば「Scene」「Sample」「Annotation」という画面に対して、
- 「Scene」画面上のボタン押下時にSceneフィルタを掛けて「Sample」画面に遷移
- 「Sample」画面上のボタン押下時にSampleフィルタを掛けて「Annotation」画面に遷移
という遷移を実行する場合、以下のような状態を管理する。

```typescript
interface NavigationState {
  // 画面遷移元からの固定フィルタ
  lockedSceneToken:    string | null  // Scene→Sample遷移時
  lockedSampleToken:   string | null  // Sample→Annotation遷移時

  // ロック元画面（ロック解除の判定に使用）
  lockSource: 'scene' | 'sample' | null
}
```

### viewerStore
現在選択中の画面内リソースを管理する。
- currentMapLocation:     string | null
- currentSceneToken:      string | null
- currentSampleToken:     string | null
- currentAnnotationToken: string | null

### mapLayerStore
各画面のチェックボックス状態を管理する。
- visibleLayers: Set\<string\> — デフォルトの例：`road_segment, lane, road_divider, lane_divider, ped_crossing`
- toggle(layer): void
- setVisible(layer, visible): void

### layerStore
Sample画面の点群・BBox等の可視性を管理する。
- layers: Record\<string, boolean\> — `pointcloud, bbox3d, ego_trajectory, drivable_area, lane` 等
- toggle(key): void

## 描画方針
### ベースレイヤー
- ベースの画像指定時（例：nuScenesのbasemap）はそれを使用する
- 地図基盤が必要な場合はLeafletを使用する
- 地図基盤が不要な場合はCanvasまたはWebGLに直接描画する
- 地図ライブラリを使用しない場合、ズーム・パンは座標変換（scale / translate）で実装する
- ベースレイヤー上のマウスカーソルの形状は、ドラッグ移動可能なときは `grab`、ドラッグ中は `grabbing` にし、Polygon等のオブジェクト上では下記内容に従う
  - ポリゴン上: `pointer`
  - Line上: `crosshair`
  - Point上: `default`

### MapへのPolygon/LineString/Point描画
- 描画数が多い場合（目安：数千以上）はDeck.glのGeoJsonLayerを使用する
- 描画数が少ない場合はHTMLCanvas（2D Context）を使用する
- 明示的にDeck.gl指定がある場合はGeoJsonLayerを優先する
- フィーチャーの選択時は、以下のようにハイライトする
  - ホバー時 → 白半透明 (+60/255) でうっすら明るくなる（autoHighlight）
  - クリック後 → 白い太アウトラインが最前面に重なり選択状態を永続表示
  - 別の場所をクリック → 選択解除（他のオブジェクトを選択した場合は新しい選択に切り替わる）

### センサ画像へのオーバーレイ描画（2D）
- Polygon / LineString / Point / 2D BBoxを対象とする
- 描画数が多い場合（目安：数千以上）はDeck.glのGeoJsonLayerを使用する
- 描画数が少ない場合はHTMLCanvas（2D Context）を使用する
- Deck.glを使用する場合はベース画像をBitmapLayer、オーバーレイをGeoJsonLayerとする
- BBoxのクリック時は、黄色等の目立つ色でハイライトする

### カメラ画像 + 3D BBox描画
- <img>タグの上にCanvas（position:absolute）を重ねてBBoxを描画する
- カメラ内部パラメータ（camera_intrinsic）を使って3D→2D投影する
- 投影計算は src/lib/coordinateUtils.ts に集約する
- 画像の表示コンポーネントは元画像のアスペクト比を維持する
- 画像は `object-fit: contain` を使用する
- Canvasサイズは表示中の画像領域に同期させる
- BBoxのクリック時は、黄色等の目立つ色でハイライトする

### LiDAR点群の描画
- バックエンドのpointcloud用エンドポイントで取得したJSON座標データを描画対象とする
- 指定がなければBEV（真上からの俯瞰）で描画する
- BEVの場合：
  - 点群の数が少ない場合（目安：〜1万点）はHTMLCanvas（2D Context）を、多い場合はDeck.glのPointCloudLayerを使用する
  - 点群とBBoxは可能な限り同じ描画基盤（Canvas または Deck.gl）で扱う
  - BBoxはEgo座標系に変換して2D投影して描画する
  - 表示コンポーネントはアスペクト比を固定し、親要素内で中央揃えにする
  - ResizeObserverで親要素サイズを監視し、canvasサイズを正方形として設定する
  - BBoxのクリック時は、黄色等の目立つ色でハイライトする
- LiDAR点群の3D描画が指定された場合：
  - HTMLCanvas（2D Context）は使用しない
  - React画面への統合を優先する場合は Deck.gl または React Three Fiber を使用する
  - 自由視点の3Dビューアとして構築する場合は Three.js / React Three Fiber を使用する
  - 大規模点群のストリーミング表示が必要な場合は Potree 系を検討する

## 設定ファイル
- 明示的に指定がない場合、`backend/config/settings.yml`に設定を保存する

## 実装上の禁止事項
- コンポーネント内に描画ロジック（座標変換・投影計算）を直接書かない
  → coordinateUtils.ts / canvasUtils.ts に集約する
- コンポーネント内から直接fetchを呼ばない
  → api/ のTanStack Queryフックを経由する
- 明示的に指定がなければLiDAR/カメラ描画にThree.jsを使わない
  → Deck.glのPointCloudLayerやGeoJsonLayer、Canvas描画で実装する
- フィルタのロック状態をコンポーネントのlocalStateで管理しない
  → navigationStoreで管理する

## よくある実装ミスと対処法
### Viteプロキシのリダイレクト追従
FastAPI等のバックエンドはURLの末尾スラッシュ有無で307リダイレクトを返すことがある。
Viteのdevサーバープロキシはデフォルトでリダイレクトを追従しないため、
ブラウザが `api:8000` に直接リクエストしてCORSエラーになる。

```typescript
// vite.config.ts
server: {
  proxy: {
    '/api': {
      target: 'http://api:8000',
      changeOrigin: true,
      followRedirects: true,  // ← 必須
    },
  },
},
```

FastAPI側で根本対処する場合：
```python
app = FastAPI(redirect_slashes=False)
```

### Radix UI の Select.Item に空文字を渡さない
shadcn/ui の `<Select.Item value="">` は空文字を渡すとエラーになる。
「フィルタなし」等の選択肢には専用の文字列を使う：

```tsx
// NG
<SelectItem value="">すべて</SelectItem>

// OK
<SelectItem value="__all__">すべて</SelectItem>

// 選択値がデフォルト値かを判定
const isAll = selectedValue === '__all__'
const filterToken = isAll ? null : selectedValue
```

### バックエンドからの画像取得はfetch経由でImageBitmapに変換する
`<img src="/api/v1/...">` はViteのdevサーバープロキシを経由しないことがある（特にChrome）。
画像はfetchで取得してImageBitmapに変換し、Canvasにdrawする。

```typescript
// src/api/maps.ts
export function useBasemap(location: string | null) {
  return useQuery({
    queryKey: ['basemap', location],
    queryFn: async () => {
      const res = await fetch(`/api/v1/maps/${location}/basemap`)
      if (!res.ok) throw new Error('basemap fetch failed')
      const blob = await res.blob()
      return createImageBitmap(blob)  // ← ImageBitmapに変換
    },
    enabled: !!location,
    staleTime: Infinity,
    gcTime: Infinity,
  })
}

// Canvas描画
ctx.drawImage(bitmap, 0, 0)
```

カメラ画像も同様：
```typescript
export function useSensorImage(token: string | null) {
  return useQuery({
    queryKey: ['sensor-image', token],
    queryFn: async () => {
      const res = await fetch(`/api/v1/sensor-data/${token}/image`)
      if (!res.ok) throw new Error('image fetch failed')
      const blob = await res.blob()
      return createImageBitmap(blob)
    },
    enabled: !!token,
    staleTime: Infinity,
    gcTime: Infinity,
  })
}
```

### 大型画像はプリフェッチする
basemap等の大型画像（数百KB〜数MB）は初回表示時のラグを防ぐため、
最上位リソース（location等）選択直後にプリフェッチする。

```typescript
// src/components/layout/Header.tsx
const queryClient = useQueryClient()

const handleLocationChange = (location: string) => {
  viewerStore.setMapLocation(location)

  // basemapをバックグラウンドで先読み
  queryClient.prefetchQuery({
    queryKey: ['basemap', location],
    queryFn: async () => {
      const res = await fetch(`/api/v1/maps/${location}/basemap`)
      const blob = await res.blob()
      return createImageBitmap(blob)
    },
    staleTime: Infinity,
  })
}
```

バックエンド側で画像をリサイズして返すことも重要（長辺4096px程度を推奨）：
```python
img.thumbnail((4096, 4096), Image.LANCZOS)
```

### Canvas地図のパン（ドラッグ移動）とズーム
Canvas上に地図を描画する場合、パンとズームを必ず実装する。

```typescript
const [zoom, setZoom]     = useState(1)
const [offset, setOffset] = useState({ x: 0, y: 0 })
const [isDragging, setIsDragging] = useState(false)
const dragStartRef = useRef({ x: 0, y: 0 })
const containerRef = useRef<HTMLDivElement>(null)

// パン
const handleMouseDown = (e: React.MouseEvent) => {
  setIsDragging(true)
  dragStartRef.current = { x: e.clientX - offset.x, y: e.clientY - offset.y }
}
const handleMouseMove = (e: React.MouseEvent) => {
  if (!isDragging) return
  setOffset({ x: e.clientX - dragStartRef.current.x, y: e.clientY - dragStartRef.current.y })
}
const handleMouseUp = () => setIsDragging(false)

// ズーム（マウスカーソル位置を中心に）
const handleWheel = (e: React.WheelEvent) => {
  e.preventDefault()
  const newZoom = Math.min(Math.max(zoom * (e.deltaY > 0 ? 0.9 : 1.1), 0.5), 10)
  const rect = e.currentTarget.getBoundingClientRect()
  const mouseX = e.clientX - rect.left
  const mouseY = e.clientY - rect.top
  // マウス位置が変わらないようにoffsetを補正
  setOffset({
    x: mouseX - (mouseX - offset.x) * (newZoom / zoom),
    y: mouseY - (mouseY - offset.y) * (newZoom / zoom),
  })
  setZoom(newZoom)
}

// +/-ボタン（コンテナ中央を基準）
const zoomAtCenter = (delta: number) => {
  const container = containerRef.current
  if (!container) return
  const newZoom = Math.min(Math.max(zoom * delta, 0.5), 10)
  const cx = container.clientWidth  / 2
  const cy = container.clientHeight / 2
  setOffset({
    x: cx - (cx - offset.x) * (newZoom / zoom),
    y: cy - (cy - offset.y) * (newZoom / zoom),
  })
  setZoom(newZoom)
}

// JSX
<div
  ref={containerRef}
  style={{ overflow: 'hidden', width: '100%', height: '100%',
           cursor: isDragging ? 'grabbing' : 'grab' }}
  onMouseDown={handleMouseDown}
  onMouseMove={handleMouseMove}
  onMouseUp={handleMouseUp}
  onMouseLeave={handleMouseUp}
  onWheel={handleWheel}
>
  <canvas
    ref={canvasRef}
    style={{
      display: 'block',
      transform: `translate(${offset.x}px, ${offset.y}px) scale(${zoom})`,
      transformOrigin: 'top left',
    }}
  />
</div>
```

### 最上位リソース変更時の選択状態リセット
左上プルダウンで最上位リソース（location等）が変わったとき、
viewerStoreの関連する全選択状態をリセットする。

```typescript
// src/store/viewerStore.ts
setMapLocation: (location) => set({
  currentMapLocation:     location,
  currentSceneToken:      null,  // 全てリセット
  currentSampleToken:     null,
  currentAnnotationToken: null,
}),
```

各ページの左ペインのローカルstateも合わせてリセットする。
ローカルstateが前のlocationのトークンを保持したまま残ると、
新しいlocationのリソース一覧に存在しないトークンでフィルタが掛かり続ける。

```typescript
// SamplePage.tsx等
// location変更時にselectedSceneTokenをリセット
useEffect(() => {
  if (!lockedSceneToken) {
    setSelectedSceneToken(null)
    setSample(null)
  }
}, [currentMapLocation])

// selectedSceneTokenが現在のlocationのSceneか検証してからデフォルト値を設定
useEffect(() => {
  if (lockedSceneToken) {
    setSelectedSceneToken(lockedSceneToken)
    return
  }
  const isValid = locationScenes.some((s) => s.token === selectedSceneToken)
  if (!isValid && locationScenes.length > 0) {
    setSelectedSceneToken(locationScenes[0].token)
  }
}, [lockedSceneToken, locationScenes])
// ↑ selectedSceneToken を依存配列に入れると無限ループになるため除外
```

### Canvas地図のデフォルト中心とズーム
左ペインのリストでアイテムを選択したとき、
地図の中心を選択アイテムの代表座標に移動し、ズームは選択アイテムの全体サイズの3倍程度の範囲が表示されるように調整する。

| アイテム種類 | 代表座標 | 全体サイズの定義 |
|---|---|---|
| ポリゴン | 全頂点の重心（各座標の平均） | 全頂点の最大距離 |
| 線（LineString） | 中間点（`Math.floor(points.length / 2)` 番目の点） | 線の長さ |
| 点（Point） | その点の座標 | 点のサイズ |
| Ego pose軌跡 | 軌跡の中間点（`egoPoses[Math.floor(egoPoses.length / 2)]`） | 軌跡構成点の最大距離 |

```typescript
// centerPointが変わったときのoffset計算はResizeObserverでコンテナサイズを確認してから行う
const [containerSize, setContainerSize] = useState({ w: 0, h: 0 })

useEffect(() => {
  const container = containerRef.current
  if (!container) return
  const observer = new ResizeObserver((entries) => {
    const { width, height } = entries[0].contentRect
    if (width > 0 && height > 0) setContainerSize({ w: width, h: height })
  })
  observer.observe(container)
  return () => observer.disconnect()
}, [])

useEffect(() => {
  if (!centerPoint || !bitmap) return
  if (containerSize.w === 0 || containerSize.h === 0) return  // コンテナ未描画時はスキップ

  const [cx, cy] = centerPointToPixel(centerPoint, ...)
  setOffset({
    x: containerSize.w / 2 - cx * zoom,
    y: containerSize.h / 2 - cy * zoom,
  })
}, [centerPoint, bitmap, location, containerSize])
```

`centerPoint` と `bitmap` と `containerSize` の3つが揃ってから計算する。
`containerSize` が0のままだとoffsetが正しく計算されず、
Sceneを初めて選択したときだけ中心がずれる症状が出る。

location変更時のリセットは `centerPoint` ではなく `location` を監視する：
```typescript
useEffect(() => {
  setOffset({ x: 0, y: 0 })
  setZoom(1)
}, [location])  // centerPointではなくlocationの変化でリセット
```

### 点群の色
背景色に合わせて点群の色を選ぶ。

**暗い背景（黒・濃紺等）の場合**：明るい色を使う
```typescript
// intensity（0〜255）を明るい青〜シアン〜白にマップ
const normalized = Math.min((intensity ?? 0) / 255, 1)
const r = Math.round(normalized * 200)
const g = Math.round(100 + normalized * 155)
const b = Math.round(200 + normalized * 55)
color = `rgb(${r},${g},${b})`
```

**明るい背景（白・グレー等）の場合**：暗い色を使う
```typescript
const normalized = Math.min((intensity ?? 0) / 255, 1)
const v = Math.round((1 - normalized) * 180)
color = `rgb(${v},${v},${v})`
```

basemapを半透明で背景に重ねる場合は暗い背景として扱い、
明るい色の点群を使うとbasemapとのコントラストが取れて見やすくなる。
RADARはLiDARより点数が少ないため `pointSize` を大きく（4px程度）設定する。

### 型定義とAPIレスポンスの対応
`src/types/` の型定義は必ずAPIの実際のレスポンス形式と一致させる。
実装前に `curl` でAPIレスポンスを確認し、フィールド名・型を正確に反映すること。

よくある不一致パターン：

| 誤り | 正しい |
|---|---|
| `translation: Point3D`（`{x,y,z}`） | `translation: number[]`（`[x,y,z]`） |
| `rotation: Quaternion`（`{w,x,y,z}`） | `rotation: number[]`（`[w,x,y,z]`） |
| `sensor_channel: string` | `channel: string`（APIのフィールド名に合わせる） |
