# advanced_design.md
SKILL.mdに記載した最小構成から、負荷対策やユーザビリティ向上のための以下の発展的なアプリ構成について記載

- マルチAZ構成への移行: 冗長性向上のためにマルチAZ構成に移行する方法
- 負荷が増えた場合の対応: 負荷が増えた場合にスケールアウト・スケールアップで対応する方法
- オリジナルドメインと証明書の取得

## マルチAZ構成への移行
以下設定を変更することで、バックエンドのコンピューティング（ECS Fargate）とDBをマルチAZ構成に移行できる
- ECS
  - Service
    - Desired tasksを2以上に増やす
    - Turn on Availability Zone rebalancingをチェックして有効化する
    - Subnetsにもう一方のAZのプライベートサブネットを追加する
- RDS
  - Modify DB instance
    - Multi-AZ deploymentを選択する
    - Secondary AZにもう一方のAZを選択する

## 負荷が増えた場合の対応
以下設定を変更することで、スケールアウト・スケールアップで処理能力を向上させられる
### スケールアウト
- ECS
  - Service
    - Desired tasksを増やす（例: 1 → 2）
    - Use service auto scalingをチェックして有効化する

### スケールアップ
- ECS
  - Task definition
    - Task sizeを大きくする（例: CPU: 1 vCPU, Memory: 2 GB → CPU: 2 vCPU, Memory: 4 GB）

## ドメインと証明書

||最小構成|ドメインと証明書の取得|
|---|---|---|
|URL|シングルAZ||
|RDS|||

### CloudFront
Reactの静的ファイルをCloudFront経由で配信するために、以下の構成でCloudFrontディストリビューションを作成する（index.htmlはキャッシュなしで、その他の静的ファイルはキャッシュありでS3の`{project-name}-static-{account-id}-ap-northeast-1-an`バケットに設置済の前提）
- Distribution name: {project-name}-frontend
- Distribution type: Single website or app
- Origin type: S3
- S3 Origin: {project-name}-static-{account-id}-ap-northeast-1-an.s3.ap-northeast-1.amazonaws.com（静的ファイルをアップロードしたバケット）
- Allow private S3 bucket access to CloudFront: Yes
- Default root object : index.html
- Error pages
  - 403 Forbidden → /index.html (HTTP 200, TTL=0)
  - 404 Not Found → /index.html (HTTP 200, TTL=0)
