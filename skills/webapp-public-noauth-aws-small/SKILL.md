---
name: webapp-public-noauth-aws-small
description: "公開の認証なしWebアプリケーションのインフラをAWSで構築するためのスキル。ユーザーが「Webアプリ」「インフラ」「AWS」「ECS」「Fargate」などに言及した際は必ずこのスキルを参照すること。"
---

# webapp-public-noauth-aws-small
小規模のユーザ数を想定した、公開の認証なしWebアプリケーションのインフラをAWSで構築するためのスキル。以下構成のFastAPI/ReactアプリケーションをAWS ECS Fargate上で動かし、データベースにはAWS RDSのPostgreSQLを使用する構成を基本とする。
- Database: PostgreSQL 16
- Migration tool: Alembic
- API framework: FastAPI（ポート8000を使用。ヘルスチェック用に`/health`エンドポイントを実装）
- ORM: SQLAlchemy 2.x
- Frontend: React + Typescript（Viteを使用。.env.productionの`VITE_API_BASE_PATH`でバックエンドAPIのベースパスを指定）
- Containerization: Docker（環境変数`DEPLOY_ENV`を使用してlocalとawsを切り替え。awsのときは環境変数S3_BUCKETで配信データ向けS3バケットを指定）

## Tech Stack
- Cloud Provider: AWS
- Networking: AWS VPC, Subnets, Security Groups, VPC Endpoints
- Database: AWS RDS (PostgreSQL)
- Data storage: AWS S3
- Parameter Management: AWS Systems Manager Parameter Store
- Load Balancing: AWS Application Load Balancer (ALB)
- Container Registry: AWS ECR
- Backend Compute: AWS ECS (Fargate)
- Frontend Hosting: AWS S3 + AWS CloudFront
- Logging & Monitoring: AWS CloudWatch
- IaC: Terraform
- CI/CD: GitHub Actions

## アプリケーション用の構成
こちらの`references/`

### VPC
"{project-name}-vpc"という名前でVPCを作成し、以下のように将来的なマルチAZ構成への移行を見込んで2つのAZにまたがるサブネットを作成し、基本的にはコスト削減のため片方のAZにのみリソースを配置する
```
VPC: 10.0.0.0/16
├── Public Subnet 1 (10.0.1.0/24) ap-northeast-1a
│     └── ALB
├── Public Subnet 2 (10.0.2.0/24) ap-northeast-1c
│     └── ALB (2つ目のAZにもマッピングしておく)
├── Private Subnet 1 (10.0.11.0/24) ap-northeast-1a
│     ├── ECS Fargate タスク
│     └── RDS (Primary)
└── Private Subnet 2 (10.0.12.0/24) ap-northeast-1c
```

マルチAZ構成に拡張する場合、以下のようにリソースを両方のAZに配置する
```
VPC: 10.0.0.0/16
├── Public Subnet 1 (10.0.1.0/24) ap-northeast-1a
│     └── ALB
├── Public Subnet 2 (10.0.2.0/24) ap-northeast-1c
│     └── ALB (マルチAZ)
├── Private Subnet 1 (10.0.11.0/24) ap-northeast-1a
│     ├── ECS Fargate タスク
│     └── RDS (Primary)
└── Private Subnet 2 (10.0.12.0/24) ap-northeast-1c
      ├── ECS Fargate タスク (マルチAZ)
      └── RDS (Standby)
```

#### セキュリティグループ
以下の構成（Postgres DBを想定）を基本とし、必要に応じてポートやルールを変更。Security Group nameと同名のNameタグを付与する。
- Security Group name: {project-name}-sg-alb
  - Inbound: 0.0.0.0/0 → 80, 443
  - Outbound: sg-ecs → 8000
- Security Group name: {project-name}-sg-ecs
  - Inbound: sg-alb → 8000
  - Inbound: sg-ecs → 443 (SSM用)
  - Inbound: sg-maintenance → 443 (SSM用)
  - Outbound: sg-rds → 5432
  - Outbound: 0.0.0.0/0 → 443 (ECR pull, S3, CloudWatch, SSM用)
- Security Group name: {project-name}-sg-rds
  - Inbound: sg-ecs → 5432
  - Inbound: sg-maintenance → 5432
  - Outbound: なし
- Security Group name: {project-name}-sg-maintenance
  - Inbound: なし
  - Outbound: sg-rds → 5432
  - Outbound: Anywhere-IPv4 → 443 (SSM, 用)

#### VPCエンドポイント
以下の構成を基本とし、必要に応じてサービスやルートテーブルを変更（vpce-logsはECSタスクログのCloudWatch Logsへの送信、vpce-ssmはSSMのParameter storeアクセスが目的）
- Name tag: {project-name}-vpce-s3
  - Service: com.amazonaws.ap-northeast-1.s3
  - Type: Gateway
- Name tag: {project-name}-vpce-logs
  - Service: com.amazonaws.ap-northeast-1.logs
  - Type: Interface
  - Route Table: Private Subnet 1
  - Security Group: sg-ecs
- Name tag: {project-name}-vpce-ssm
  - Service: com.amazonaws.ap-northeast-1.ssm
  - Type: Interface
  - Route Table: Private Subnet 1
  - Security Group: sg-ecs

以下はコンテナデプロイ時のみ必要となるため、コスト削減のためにデプロイ用Makefileで立ち上げ、デプロイ後は削除する構成を基本とする
- Name tag: {project-name}-vpce-dkr
  - Service: com.amazonaws.ap-northeast-1.ecr.dkr
  - Type: Interface
  - Route Table: Private Subnet 1
  - Security Group: sg-ecs
- Name tag: {project-name}-vpce-ecr
  - Service: com.amazonaws.ap-northeast-1.ecr.api
  - Type: Interface
  - Route Table: Private Subnet 1
  - Security Group: sg-ecs

### IAMポリシー
IAMロールにアタッチするため、以下4種類のIAMポリシーを基本とし、必要に応じてポリシー内容を変更・追加

1. パラメータストアアクセス用ポリシー
- Policy name: {project-name}-ssm-parameter-access
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "SSMParameterAccess",
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:GetParameters"
      ],
      "Resource": "arn:aws:ssm:ap-northeast-1:{account-id}:parameter/{project-name}/*"
    }
  ]
}
```

2. SSMのKMSキーアクセス用ポリシー
- Policy name: {project-name}-ssm-kms-access
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "KMSDecrypt",
      "Effect": "Allow",
      "Action": "kms:Decrypt",
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "kms:ViaService": "ssm.ap-northeast-1.amazonaws.com"
        }
      }
    }
  ]
}
```

3. S3バケット読取用ポリシー
- Policy name: {project-name}-s3-read-access
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3Access",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::{project-name}-data",
        "arn:aws:s3:::{project-name}-data/*"
      ]
    }
  ]
}
```

4. S3バケット書込用ポリシー
- Policy name: {project-name}-s3-write-access
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3Access",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::{project-name}-data/*"
    }
  ]
}
```

### IAMロール
Dockerの運用やコンテナ内のアプリケーションがAWSリソースにアクセスするための以下3種類のIAMロールを基本とし、必要に応じてロールやポリシーを変更・追加

1. ECSタスク実行ロール: DockerイメージのプルやCloudWatch Logsへのアクセスなど、ECSタスクの実行に必要な権限を持つロール
Role name: {project-name}-ecs-task-execution-role
Trust policy: ecs-tasks.amazonaws.com (Use case: Task Execution Role for Elastic Container Service)
Permissions policy: AmazonECSTaskExecutionRolePolicy, {project-name}-ssm-parameter-access, {project-name}-ssm-kms-access

2. コンテナ内アプリケーション用ロール: コンテナ内で動作するアプリケーションが、S3からのファイル取得やSSMからのパラメータ取得などを行うためのロール
Role name: {project-name}-ecs-task-role
Trust policy: A custom trust policy below
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```
Permissions policy: {project-name}-ssm-parameter-access, {project-name}-s3-read-access, {project-name}-s3-write-access

3. 踏み台インスタンス用ロール: 踏み台インスタンスにSSMセッションマネージャーを使用して接続し、S3バケットにアクセスするためのロール
Role name: {project-name}-ec2-ssm-role
Trust policy: ec2.amazonaws.com (Use case: EC2 Role for AWS Systems Manager)
Permissions policy: AmazonSSMManagedInstanceCore, {project-name}-s3-read-access

### RDS
データベースにはRDSのPostgreSQLを使用した以下の構成を基本とし、必要に応じてエンジンやバージョン、インスタンスクラスなどを変更

#### サブネットグループ
以下の構成を基本とし、必要に応じてサブネット数やリージョンを変更
- Name: {project-name}-db-subnet-group
- Description: Subnet group for RDS instances
- Subnets: Private Subnet 1, Private Subnet 2

#### パラメータグループ
通常のPostgreSQLやMySQL利用時は、明示的に指定がなければデフォルトのパラメータグループを使用する。以下のケースではパラメータグループを作成し、必要に応じてパラメータを変更
##### PostGIS利用時
- Parameter group name: {project-name}-postgis-params
- Description: Parameter group for PostGIS extension
- Engine type: PostgreSQL
- Parameter group family: postgres16
- Type: DB Parameter Group

#### RDSインスタンス
- Envine type: PostgreSQL
- Templates: Free tier（マルチAZ構成に拡張する場合は、Dev/Testに変更）
- Deployment options: Single-AZ DB instance deployment（マルチAZ構成に拡張する場合は、Multi-AZ DB instance deploymentに変更）
- Engine version: 16.9
- DB instance identifier: {project-name}-db
- Credentials management: Self managed
- Master username: migrator（マイグレーション使用を想定）
- Master password: 生成した安全なパスワード
- Database authentication: Password authentication
- Instance class: db.t4g.micro
- Storage type: gp2
- Allocated storage: 20 GiB
- Enabled storage autoscaling: Disabled（データ増加が見込まれる場合は有効化を検討）
- Compute resource: Don't connect to an EC2 compoute resource
- Network type: IPv4
- VPC: {project-name}-vpc（上で作成したVPCを使用）
- Subnet group: {project-name}-db-subnet-group（上で作成したサブネットグループを使用）
- Public access: No
- VPC security groups: sg-rds（上で作成したRDS用セキュリティグループを使用）
- Availability zone: ap-northeast-1a（コスト削減のため片方のAZにのみ配置。マルチAZ構成に拡張する場合は、スタンバイインスタンスをもう一方のAZに配置）
- Initial database name: プロジェクトに応じて適宜設定（例: {project-name}。ただしハイフン使用不可のため、アンダースコアなどに置き換える）
- DB parameter group: 上でパラメータグループを作成した場合はそれを、作成していない場合はデフォルトのパラメータグループを使用
- Backup retention period: 7 days
- Enable auto minor version upgrades: Disabled

#### 初期化用SQLコマンド
アプリの初期化のため、踏み台インスタンスを作成してRDSに接続し、以下のSQLコマンドを実行する。

PostGISを使用する場合は、以下のコマンドを実行（PostGISを使用しない場合はスキップ）
```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
```

以下コマンドで、アプリ用ユーザーを作成し、マイグレーション用ユーザーも含めて適切な権限を付与する（`{project-name}`の部分はプロジェクトに合わせて変更）
```sql
-- 01-init.sh相当) アプリユーザーの作成
CREATE USER app WITH PASSWORD '（強力なパスワードを設定）';

-- 02-init.sql 2) スキーマの所有権と権限設計
ALTER SCHEMA public OWNER TO migrator;
GRANT CONNECT ON DATABASE {project-name} TO app;
GRANT USAGE ON SCHEMA public TO app;
GRANT USAGE, CREATE ON SCHEMA public TO migrator;

-- 3) 既存テーブルへの権限（マイグレーション後に実行）
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO app;

-- 4) 今後作成されるテーブルへの権限も自動付与
ALTER DEFAULT PRIVILEGES FOR ROLE migrator IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app;
ALTER DEFAULT PRIVILEGES FOR ROLE migrator IN SCHEMA public
  GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO app;

-- 5) PUBLICの権限を絞る
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
```

### パラメータストア
RDSの接続情報やアプリケーションのシークレットなどを管理するために、AWS Systems Manager Parameter Storeを使用する。以下の構成を基本とし、必要に応じてパラメータ名や値を変更
1. RDSのホスト名
- Name: /{project-name}/db/host
- Description: RDS instance endpoint
- Type: String
- Value: RDSインスタンスのエンドポイント（例: {project-name}-db.abcdefghijk.ap-northeast-1.rds.amazonaws.com）
2. RDSのポート番号
- Name: /{project-name}/db/port
- Description: RDS instance port
- Type: String
- Value: 5432
3. RDSのデータベース名
- Name: /{project-name}/db/name
- Description: RDS database name
- Type: String
- Value: 上でRDSインスタンスのInitial database nameに設定した値（例: {project-name}）
4. RDSのマイグレーション用ユーザー名
- Name: /{project-name}/db/migrator_user
- Description: RDS username for migration
- Type: String
- Value: 上でRDSインスタンスのMaster usernameに設定した値（例: migrator）
5. RDSのマイグレーション用ユーザーパスワード
- Name: /{project-name}/db/migrator_password
- Description: RDS password for migration
- Type: SecureString
- KMS key: source My current account
- KMS Key ID: alias/aws/ssm（デフォルト）
- Value: 上でRDSインスタンスのMaster passwordに設定した値
6. RDSのアプリ用ユーザー名
- Name: /{project-name}/db/app_user
- Description: RDS username for application
- Type: String
- Value: 上で作成したアプリ用ユーザー名（例: app）
7. RDSのアプリ用ユーザーパスワード
- Name: /{project-name}/db/app_password
- Description: RDS password for application
- Type: SecureString
- KMS key: source My current account
- KMS Key ID: alias/aws/ssm（デフォルト）
- Value: 上で作成したアプリ用ユーザーのパスワード
8. 配信する画像等データを保存するバケット名
- Name: /{project-name}/s3/data_bucket
- Description: S3 bucket name for data storage
- Type: String
- Value: {project-name}-data（下で作成するデータバケット名）
9. Reactの静的ファイルを保存するバケット名
- Name: /{project-name}/s3/static_bucket
- Description: S3 bucket name for React static files
- Type: String
- Value: {project-name}-static（下で作成する静的ファイルバケット名）

### S3 bucket
以下2種類のバケットを作成
1. `{project-name}-data`: 配信する画像等のデータを保存するバケット（非公開。バケット直下の`data/`ディレクトリにローカルと同じ構造でデータを保存）
- Bucket name prefix: `{project-name}-data`

2. `{project-name}-static`: Reactの静的ファイル（CloudFront経由で公開）
- Bucket name prefix: `{project-name}-static`

両バケットは以下を共通設定とする
- AWS Region: ap-northeast-1
- Bucket type: General purpose
- Bucket namespace: Globale namespace
- Object Ownership: ACLs disabled
- Public access: Block all public access
- Bucket Versioning: Disabled
- Default encryption: Server-side encryption with Amazon S3 managed keys (SSE-S3)
- Bucket Key: Enabled

### ALB
#### Target group
- Target type: IP addresses
- Target group name: {project-name}-tg
- Protocol: HTTP
- Port: 8000
- IP address type: IPv4
- VPC: {project-name}-vpc（上で作成したVPCを使用）
- Protocol version: HTTP1
- Health check protocol: HTTP
- Health check path: /health
- Health check port: Traffic port
- Healthy threshold: 2
- Unhealthy threshold: 3
- Timeout: 5 seconds
- Interval: 30 seconds
- Success codes: 200
ターゲット登録は後ほどECSのサービス作成時に行う

#### Load balancer (ALB)
- Name: {project-name}-alb
- Scheme: Internet-facing
- Load balancer IP address type: IPv4
- VPC: {project-name}-vpc（上で作成したVPCを使用）
- Availability Zones and subnets: {project-name}-subnet-public1-ap-northeast-1aと{project-name}-subnet-public2-ap-northeast-1c（マルチAZ移行に備えて両AZを含めておく）
- Security group: {project-name}-sg-alb（上で作成したALB用セキュリティグループを使用）
- Listeners
  - 1
    - Protocol: HTTP
    - Port: 80（ユーザーがアクセスするポート）
    - Routing action: Forward to target groups
    - Target group: {project-name}-tg（上で作成したターゲットグループ）

### ECR repository
以下の構成でECRリポジトリを作成し、Dockerイメージをプッシュする際に使用する
1. バックエンド用
- Name: {project-name}/backend
- Image tag mutability: Mutable
- Encryption settings: AES-256
（フロントエンドはS3とCloudFrontを使用するため、ECRリポジトリは不要）

### CloudWatch Logs
ECSタスクのログをCloudWatch Logsに送信するために、以下の構成でロググループを作成する
- Log group name: /ecs/{project-name}
- Retention setting: 30 days
- Log class: Standard

### ECS
#### ECS cluster
- Cluster name: {project-name}-cluster
- Select a method of obtaining compute capacity: Fargate only

#### Task definition
アプリ用とマイグレーション用の2種類のタスク定義を作成し、必要に応じて構成を変更（例：DBへのデータインポート用タスクをプロジェクトに応じて作成）

両タスクの共通設定
- Launch type: AWS Fargate
- Operating system/Architecture: Linux/x86_64
- Task role: {project-name}-ecs-task-role（上で作成したコンテナ内アプリケーション用ロールを指定）
- Task execution role: {project-name}-ecs-task-execution-role（上で作成したECSタスク実行ロールを指定）

1. アプリ用タスク定義
- Task definition family: {project-name}-backend-task
- Task size
  - CPU: 1 vCPU
  - Memory: 2 GB
- Container - 1
  - Container name: backend
  - Image URI: 上で作成したバックエンド用ECRリポジトリのURI（例: {account-id}.dkr.ecr.ap-northeast-1.amazonaws.com/{project-name}/backend:latest）
  - Port mappings: 8000 (TCP)
  - Environment variables: 以下を基本とし、必要に応じて追加
    - Key: POSTGRES_HOST, Value type: ValueFrom, Value: /{project-name}/db/host (SSM Parameter StoreのRDSのホスト名を参照)
    - Key: POSTGRES_PORT, Value type: ValueFrom, Value: /{project-name}/db/port (SSM Parameter StoreのRDSのポート番号を参照)
    - Key: POSTGRES_DB, Value type: ValueFrom, Value: /{project-name}/db/name (SSM Parameter StoreのRDSのデータベース名を参照)
    - Key: POSTGRES_USER, Value type: ValueFrom, Value: /{project-name}/db/app_user (SSM Parameter StoreのRDSのアプリ用ユーザー名を参照)
    - Key: POSTGRES_PASSWORD, Value type: ValueFrom, Value: /{project-name}/db/app_password (SSM Parameter StoreのRDSのアプリ用ユーザーパスワードを参照)
    - Key: S3_DATA_BUCKET, Value type: ValueFrom, Value: /{project-name}/s3/data_bucket (SSM Parameter Storeの配信する画像等データを保存するバケット名を参照)
    - Key: DEPLOY_ENV, Value type: Value, Value: aws
    - Key: PYTHONPATH, Value type: Value, Value: /app
  - Log collection
    - Destination: AWS CloudWatch
    - awslogs-group: /ecs/{project-name}（先ほど作成したロググループ）
    - awslogs-region: ap-northeast-1
    - awslogs-stream-prefix: backend

2. マイグレーション用タスク定義
- Task definition family: {project-name}-migration-task
- Task size
  - CPU: 0.5 vCPU
  - Memory: 1 GB
- Container - 1
  - Container name: migration
  - Image URI: 上で作成したバックエンド用ECRリポジトリのURI（例: {account-id}.dkr.ecr.ap-northeast-1.amazonaws.com/{project-name}/backend:latest）
  - Port mappings: 8000 (TCP)
  - Environment variables: 以下を基本とし、必要に応じて追加
    - Key: POSTGRES_HOST, Value type: ValueFrom, Value: /{project-name}/db/host (SSM Parameter StoreのRDSのホスト名を参照)
    - Key: POSTGRES_PORT, Value type: ValueFrom, Value: /{project-name}/db/port (SSM Parameter StoreのRDSのポート番号を参照)
    - Key: POSTGRES_DB, Value type: ValueFrom, Value: /{project-name}/db/name (SSM Parameter StoreのRDSのデータベース名を参照)
    - Key: POSTGRES_USER, Value type: ValueFrom, Value: /{project-name}/db/migrator_user (SSM Parameter StoreのRDSのマイグレーション用ユーザー名を参照)
    - Key: POSTGRES_PASSWORD, Value type: ValueFrom, Value: /{project-name}/db/migrator_password (SSM Parameter StoreのRDSのマイグレーション用ユーザーパスワードを参照)
    - Key: DEPLOY_ENV, Value type: Value, Value: aws
  - Log collection
    - Destination: AWS CloudWatch
    - awslogs-group: /ecs/{project-name}（先ほど作成したロググループ）
    - awslogs-region: ap-northeast-1
    - awslogs-stream-prefix: migration
  - Docker configuration
    - Command: alembic,upgrade,head

#### ECS service
アプリ用タスクをサービスとして以下の構成でデプロイする。
- Task definition family: {project-name}-backend-task
- Task definition revision: LATEST
- Service name: {project-name}-service
- Compute options: Launch type
- Launch type: Fargate
- Platform version: LATEST
- Desired tasks: 1
- Turn on Availability Zone rebalancing: Disabled（マルチAZ構成へ移行した場合に有効化）
- VPC: {project-name}-vpc（上で作成したVPCを使用）
- Subnets: {project-name}-subnet-private1-ap-northeast-1a のみ（マルチAZ構成へ移行した場合もう片方のAZを追加）
- Security group: {project-name}-sg-ecs（上で作成したECS用セキュリティグループを使用）
- Public IP: Turned off（ALBを使用するため、タスクにはパブリックIPは割り当てない）
- Use load balancing: Enabled
- Load balancer type: Application Load Balancer
- Application Load Balancer: Use an existing load balancer
- Load balancer: {project-name}-alb（上で作成したALBを指定）
- Listener: Use an existing listener
  - Listener: 上で作成したHTTP:80のリスナーを指定
- Target group: Use an existing target group
  - Target group name: {project-name}-tg（上で作成したターゲットグループを指定）
  - Health check path: /health
  - Health check protocol: HTTP
- Use service auto scaling: Disabled

#### Migration task execution
マイグレーション用タスクはサービス化せず、必要に応じて以下構成でタスクを直接起動する
- Task definition family: {project-name}-migration-task
- Task definition revision: LATEST
- Desired tasks: 1
- Compute options: Launch type
- Launch type: Fargate
- Platform version: LATEST
- VPC: {project-name}-vpc（上で作成したVPCを使用）
- Subnets: {project-name}-subnet-private1-ap-northeast-1a のみ
- Security group: {project-name}-sg-ecs（上で作成したECS用セキュリティグループを使用）
- Public IP: Turned off

### CloudFront
Reactの静的ファイルをCloudFront経由で配信し、
アプリにCloudFrontドメイン（`*************.cloudfront.net`）でアクセスできるようにするため、以下の構成でCloudFrontディストリビューションを作成する（index.htmlはキャッシュなしで、その他の静的ファイルはキャッシュありでS3の`{project-name}-static`バケットに設置済の前提）
- Distribution name: {project-name}-frontend
- Distribution type: Single website or app
- Origins
  - Origin1（フロントエンド用）
    - Origin domain: {project-name}-static.s3.ap-northeast-1.amazonaws.com（静的ファイルをアップロードしたバケット）
    - Origin access: Origin access control settings
      - Name: {project-name}-oac
      - Description: OAC for {project-name} CloudFront distribution
      - Signing behavior: Sign requests
      - Origin type: S3
  - Origin2（ALB用）
    - Origin domain: {project-name}-alb-xxxxxxxxxx.ap-northeast-1.elb.amazonaws.com（ALBのDNS名）
    - Protocol: HTTP only
    - HTTP port: 80
- Behaviors
  - Behavior1（フロントエンド用）
    - Path pattern: Default (*)
    - Origin: Origin1（フロントエンド用）
    - Compress objects automatically: Yes
    - Viewer protocol policy: Redirect HTTP to HTTPS
    - Allowed HTTP methods: GET, HEAD
    - Restrict viewer access: NO
    - Cache policy: CachingOptimized
  - Behavior2（ALB用）
    - Path pattern: /api/*（バックエンドAPIへのリクエストをALBにルーティングする例。必要に応じてパスパターンを変更）
    - Origin: Origin2（ALB用）
    - Compress objects automatically: Yes
    - Viewer protocol policy: Redirect HTTP to HTTPS
    - Allowed HTTP methods: GET, HEAD, OPTIONS, PUT, POST, PATCH, DELETE
    - Restrict viewer access: NO
    - Cache policy: CachingDisabled
    - Origin request policy: AllViewer
- Allow private S3 bucket access to CloudFront: Yes
- Default root object : index.html
- Error pages
  - 403 Forbidden → /index.html (HTTP 200, TTL=0)
  - 404 Not Found → /index.html (HTTP 200, TTL=0)

S3バケット`{project-name}-static`にも次のバケットポリシー（CloudFront OACからのアクセス許可）を追加する
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowCloudFrontServicePrincipal",
      "Effect": "Allow",
      "Principal": {
        "Service": "cloudfront.amazonaws.com"
      },
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::{project-name}-static/*",
      "Condition": {
        "ArnLike": {
          "AWS:SourceArn": "arn:aws:cloudfront::{account-id}:distribution/{distribution-id}"
        }
      }
    }
  ]
}
```
