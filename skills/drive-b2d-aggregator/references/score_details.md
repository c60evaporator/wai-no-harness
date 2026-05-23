## 各種最終スコアとの関係
論文等に記載されているスコアと

| メトリクス | 計算式 |
|---|---|
| **Driving Score** | 全220ルートの `score_composed` (= `score_route × score_penalty`) の平均 |
| **Success Rate** | 全220ルートのうち「**完走** かつ **min_speed以外の違反ゼロ**」のルート数 / 220 |
|**Driving Efficiency**|制限速度に対してどれだけ速く走れたか（`min_speed_infractions`の%値の平均）|
|**Driving Smoothness**|急加速・急旋回がどれだけ少なかったか（6基準を全て満たすセグメントの割合）|

### Driving Score
**全ルートの `score_composed` の平均**

```python
"driving score": sum(driving_score) / 220
```

$$\text{Driving Score} = \frac{1}{N}\sum_{i=1}^{N} \text{score\_route}_i \times \text{score\_penalty}_i$$

### Success Rate

**Success = 完走かつ min_speed_infractions 以外の違反がゼロ**とし、

```python
if rd['status'] == 'Completed' or rd['status'] == 'Perfect':
    success_flag = True
    for k, v in rd['infractions'].items():
        if len(v) > 0 and k != 'min_speed_infractions':  # ← min_speed以外の違反があればNG
            success_flag = False
            break
    if success_flag:
        success_num += 1
```

| 条件 | Success？ |
|---|---|
| `Perfect`（完走 + 違反ゼロ） | ✅ |
| `Completed`（完走 + **min_speed違反のみ**） | ✅ |
| `Completed`（完走 + **衝突・信号無視等あり**） | ❌ |
| `Failed - *` | ❌ |

min_speed_infractions（最低速度違反）だけは許容され、それ以外の違反（衝突、信号無視、一時停止違反、ルート逸脱等）が1つでもあれば Success にカウントされない


### Driving Efficiency

**入力**：eval.json 内の `min_speed_infractions` に記録された速度割合（%）

```python
# efficiency_smoothness_benchmark.py:268-277
for min_speed_infrac in record["infractions"]["min_speed_infractions"]:
    number = re.search(r"\b\d+\.?\d*%", min_speed_infrac)
    driving_e.append(float(number.group().rstrip('%')))
driving_e = sum(driving_e) / len(driving_e)   # ルート内の平均
```

`min_speed_infractions` は Leaderboard の `MinimumSpeedRouteTest` が記録するもので、各チェックポイント区間での「**平均速度 / 制限速度 × 100**」の割合（%）です。

$$\text{Driving Efficiency} = \frac{1}{N_\text{routes}} \sum_{\text{routes}} \left( \frac{1}{K} \sum_{k=1}^{K} \text{speed\_percentage}_k \right)$$

- 1000%を超える異常値は除外
- `min_speed_infractions` が無い（違反なし＝速度が十分だった）ルートは**対象外**
- 値が高いほど効率的（制限速度に近い速度で走行した）

### Driving Smoothness (Comfortness)

**入力**：`metric_info.json` の毎フレームのEgo車両状態（加速度、角速度、前方/右方ベクトル、位置、姿勢）

#### 6つの快適性基準

各基準に閾値が設定されており、**全て閾値内に収まっていれば合格（True）**：

| # | 指標 | 閾値 |
|---|---|---|
| 1 | **縦方向加速度** (lon_acc) | $[-4.05,\ 2.40]$ m/s² |
| 2 | **横方向加速度** (lat_acc) | $[-4.89,\ 4.89]$ m/s² |
| 3 | **加速度magnitude のjerk** | $[-8.37,\ 8.37]$ m/s³ |
| 4 | **縦方向jerk** (lon_jerk) | $[-4.13,\ 4.13]$ m/s³ |
| 5 | **ヨー角加速度** (yaw_acc) | $[-1.93,\ 1.93]$ rad/s² |
| 6 | **ヨーレート** (yaw_rate) | $[-0.95,\ 0.95]$ rad/s |

#### 計算手順

1. `metric_info.json` から加速度・角速度等の時系列データを読み込み
2. Savitzky-Golay フィルタで平滑化・微分（jerkの算出）
3. 時系列を **20ステップのセグメントに分割**
4. 各セグメントで**6つの基準が全て閾値内** → そのセグメントは `True`
5. ルートごとの Smoothness = `True のセグメント数 / 全セグメント数`
6. 最終スコア = 全ルートの平均

$$\text{Driving Smoothness} = \frac{1}{N_\text{routes}} \sum_{\text{routes}} \frac{\text{合格セグメント数}}{\text{全セグメント数}}$$

値が**1.0に近いほど滑らか**（急加速・急ハンドルが少ない）な走行であることを示します。
