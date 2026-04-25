---
name: backend-fastapi-postgis
description: "地図・描画アプリケーションのバックエンド実装。FastAPI + PostGISでAPIとDBを構築し、必要に応じて空間クエリやインデックスを使用して地図上の点や線を効率的に取得する。ユーザーが「Leaflet」「Deck.gl」「PostGIS」「map application」「GIS」などに言及した際は必ずこのスキルを参照すること。自動運転や地図に関係したアプリ作成、API開発、データベース設計にも適用する。"
---

# backend-fastapi-postgis
地図・描画アプリケーションのバックエンド実装。FastAPI + PostGISでAPIとDBを構築し、必要に応じて空間クエリやインデックスを使用して地図上の点や線を効率的に取得する。

## Tech Stack
- Programming Language: Python 3.12
- API framework: FastAPI + Pydantic
- Database: PostgreSQL 16 + PostGIS 3.4
- ORM: SQLAlchemy 2.x + GeoAlchemy2
- Migration: Alembic

## Directory Structure
root/
├── docker-compose.yml
├── .env
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pytest.ini
│   ├── alembic.ini
│   ├── app/
│   │   ├── main.py                         # FastAPIアプリ初期化・ルーター登録
│   │   ├── dependencies.py                 # DBセッションなど共通依存関係
│   │   ├── core/          # アプリ全体のコアロジック
│   │   │   ├── config.py                   # 環境変数・設定（Pydantic Settings）
│   │   │   └── logging.py                  # ロギング設定
│   │   ├── db/
│   │   │   ├── base.py                     # DeclarativeBase
│   │   │   ├── session.py                  # AsyncSession ファクトリ
│   │   │   └── poitgis.py                  # PostGIS初期化・拡張確認（ファイル名は typo だが変更禁止）
│   │   ├── models/                         # SQLAlchemy ORMモデル
│   │   │   ├── __init__.py                 # Alembicがモデルを検出できるよう全importを記載
│   │   │   └── 各テーブルのスキーマをグループごとに.pyファイルを分けて定義
│   │   ├── schemas/                        # Pydantic スキーマ（APIスキーマ）
│   │   │   ├── common.py                   # 複数のエンドポイントでの共通型
│   │   │   └── 各エンドポイントのスキーマをグループごとに.pyファイルを分けて定義（Point3D, Quaternion, Dimensions3Dなど）
│   │   ├── converters/                     # DB → APIスキーマへの変換ロジック
│   │   │   ├── __init__.py
│   │   │   ├── geometry.py                 # GeoAlchemy2 → GeoJSON変換や面積計算など
│   │   │   ├── sensor.py                   # EgoPose → 変換行列など（必要な場合のみ）
│   │   │   ├── annotation.py               # アノテーション取得・更新（必要な場合のみ）
│   │   │   └── その他必要な変換ロジックをグループごとに.pyファイルを分けて実装
│   │   ├── repositories/                   # DBアクセスの抽象化（クエリの責務）
│   │   │   └── 各テーブルへのクエリをグループごとに.pyファイルを分けて実装
│   │   └── api/
│   │       └── v1/
│   │           ├── router.py               # v1ルーターの集約
│   │           └── endpoints/
│   │               └── 各エンドポイントをグループごとに.pyファイルを分けて実装
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │       └── マイグレーションファイルを自動生成して保存
│   ├── tests/
│   │   └── unit/
│   │       ├── lib/        # coordinateUtils.test.ts, canvasUtils.test.ts
│   │       └── store/      # navigationStore.test.ts
│   ├── scripts/          # DB初期化やマイグレーション用のスクリプト
│   └── config/
│       └── settings.yml    # アプリ全体の設定ファイル
└── db/                     # DB関連のファイルをまとめるディレクトリ
    └── initdb.d/           # DB初期化用のスクリプトを配置するディレクトリ。docker-compose.ymlでマウントして使用する。   
        ├── 01_init.sh
        └── 02-init.sql

## Docker
- APIサーバーのDockerfileは`references/Dockerfile`をベースに、バックエンド処理に必要なパッケージのインストールとビルドコマンドを追加する。
- docker-compose.ymlは`references/docker-compose.yml`をベースにapi・migrations・db（PostGIS）・pgadminサービスを構築し、フロントエンドサービス等を追加する。プロジェクトに合わせてイメージ名やビルドコンテキスト、環境変数等を適切に設定する。
- バックエンドとフロントエンドの通信には`frontend-network`、バックエンドとDBの通信には`backend-network`、DBとpgadminの通信には`pgadmin-network`を使用する。
- FastAPIに `redirect_slashes=False` を設定する（設定しないとViteプロキシが307リダイレクトを追従できずCORSエラーになる）

## DB
### ジオメトリ型のルール
- DBカラム型: GeoAlchemy2の `Geometry` 型を使用
  - Point    → `Geometry('POINT', srid=4326)`
  - LineString → `Geometry('LINESTRING', srid=4326)`
  - Polygon  → `Geometry('POLYGON', srid=4326)`
- SRID: 常に4326（WGS84）を使用
- API入出力: 常にGeoJSON形式（`{"type": "Point", "coordinates": [...]}` 等）
- GeoJSON ↔ PostGIS変換: **geoalchemy2.shape と shapely を使用**
  - 変換ロジックは `app/converters/geometry.py` に集約する
  - RouterやCRUDに変換コードを直接書かない

### geometry.pyの変換パターン（参考実装）
```python
# GeoJSON dict → WKBElement（DB保存時）
from geoalchemy2.shape import from_shape
from shapely.geometry import shape

def geojson_to_wkb(geojson: dict):
    return from_shape(shape(geojson), srid=4326)

# WKBElement → GeoJSON dict（APIレスポンス時）
from geoalchemy2.shape import to_shape

def wkb_to_geojson(wkb) -> dict:
    return to_shape(wkb).__geo_interface__
```

### インデックス
- 明確に検索クエリがパフォーマンスのボトルネックになることが想定される場合、適切なインデックス、またはPostGISの空間インデックスを作成する
- パフォーマンスが問題になるか微妙なケースでは、インデックスを作成せずにフロントエンドまで実装してみて、必要に応じてインデックスを追加する

### Alembicマイグレーション
- `alembic revision --autogenerate` でマイグレーションファイルを生成し、PostGIS拡張の有効化（`CREATE EXTENSION IF NOT EXISTS postgis`）は初回マイグレーションに含める
- DBロールを分ける場合（DDL用・DML用）、`initdb.d` スクリプトでDML用ロールを作成してから Alembic でDDLを実行する

## API Design
### 共通ルール
- prefix: `/api/v1`
- レスポンスは常にPydantic schemaを通す
- ジオメトリフィールドはGeoJSON形式で返す
- エラーは `{"detail": "..."}`形式で返す

### ページネーション
- 全GETリストエンドポイントで共通化`GET /api/v1/scenes?limit=50&offset=0`
- 全エンドポイントに `limit`・`offset` を設け `PaginatedResponse` で返す
- `limit` の上限（`le=`）はデータセット規模によって変わるため、十分大きい値（`le=99999`）を設定する。`le=500` 等の小さい値にするとデータセット切り替え時に全件取得できなくなる
- フロントエンドで全件取得が必要なリソース（calibrated_sensors等）は実装時に `total` フィールドを確認してlimitが足りているか検証する

### ファイルの配信
画像、点群データなどはDBではなくファイルストレージ（ローカルの `storage/` ディレクトリやS3など）に保存し、APIでは以下の形式で返す

#### 画像
- ファイルストレージに静的に保持されている画像（センサ画像、地図のベース画像等）はFileResponseで返す
- 動的に生成するコンテンツやリアルタイムデータはStreamingResponseで返す
- 明示的に指定がなければ、大型画像（数十MB）はPillowで長辺4096px以下にリサイズしてから返す（例：`img.thumbnail((4096, 4096), Image.LANCZOS)`）

#### 点群データ
LiDAR、ミリ波レーダー、ステレオカメラ等の点群データは、明示的な指定がなければPotree形式に変換せず`.pcd`、`.pcd.bin`、`.ply`等を以下の形式で直接配信する。
- フォーマット: float32 × 5列（x, y, z, intensity, ring_index）
- DBの fileformat カラム値: `pcd`
- APIレスポンス: JSON形式 `{"points": [[x,y,z,intensity], ...], "num_points": N}`

### 地図のベース画像とWGS84座標の対応
- 地図のベース画像はローカルメートル座標系で格納されることが多い。Deck.gl等のWGS84ベースのライブラリで使う場合はロケーションごとのGPS原点を基準に線形近似で変換する：
```python
  lat = lat0 + y / 111320.0
  lon = lon0 + x / (111320.0 * math.cos(math.radians(lat0)))
```
- GPS原点は `backend/config/settings.yml` の `map_origins` セクションで管理する
- GeoJSONはWGS84（SRID=4326）で返し、フロントエンドはDeck.glのGeoJsonLayerで直接描画できるようにする

## 設定ファイル
- 明示的に指定がない場合、`backend/config/settings.yml`に設定を保存する
- ロケーションごとのGPS原点（`map_origins`）、データルートパス、DB接続情報等を管理する
- 設定値は `backend/app/core/app_config.py` 等の設定モジュールで読み込み、各モジュールから直接YAMLを読まない

## 実装上の制約
- SQLAlchemy 2.xの `Session` は `Annotated` + `Depends` でDI
- 非同期（async/await）を使用する（ドライバ: asyncpg）
- CORSは開発時 `*` 許可、本番は環境変数で制御
- テストDBは別コンテナ（postgresのみ、PostGIS不要）ではなく同一イメージを使う

## 実装上の禁止事項
- RouterにDB変換ロジックを書かない → app/converters/ に集約
- Pydanticモデルをmodels/と独立して定義しない → schemas/はmodels/から派生
- ジオメトリをWKBのままAPIレスポンスに含めない → 必ずGeoJSONに変換
- 新リソース追加時は endpoints/ + converters/ + repository/ + schemas/ をセットで追加する
