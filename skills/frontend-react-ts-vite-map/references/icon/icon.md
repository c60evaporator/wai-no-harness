# アイコンの読み込み方法
## アイコン

ブラウザのタブに表示されるアイコンは、16x16または32x32サイズの`frontend/public/favicon.ico`（作成時は`refereneces/create_icon.py`が役に立つ）として格納しておき、以下のように`frontend/index.html`から読み込む

```html
<!doctype html>
<html lang="en">
  <head>
    :略
    <link rel="icon" type="image/x-icon" href="/favicon.ico" />
    :略
  </head>
  <body>
    :略
  </body>
</html>
```

## ヘッダーのアイコン

画面上部のタブ（ヘッダー）のアイコンは、`frontend/src/assets/icons`に格納したsvgファイルを用いる。例えば`scene`, `sample`, `instance`, `annotations`のタブを持つ場合、以下のようなsvgファイルを格納しておく（作成時は`refereneces/create_icon.py`が役に立つ）

```
frontend/src/assets/icons/
├── scene.svg
├── sample.svg
├── instance.svg
└── annotation.svg
```

アイコン用のsvgファイルは、`fill`や`stroke`を"currentColor"にしておくことで、色をpropsで制御できるようにしておく（`refereneces/scene.svg`も参照）。

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" shape-rendering="crispEdges">
<rect x="10" y="3" width="1" height="1" fill="currentColor" fill-opacity="1.000000" />
<rect x="11" y="3" width="1" height="1" fill="currentColor" fill-opacity="1.000000" />
:
中略
:
</svg>
```

`frontend/src/components/layout/Header.tsx`から以下のように、vite-plugin-svgrを用いてsvgファイルをコンポーネントとして読み込み、タブ選択時（ACTIVE_COLOR）と選択されていないとき（INACTIVE_COLOR）で色を変えられるようにする

```typescript
import SceneIcon      from '@/assets/icons/scene.svg?react'
import SampleIcon     from '@/assets/icons/sample.svg?react'
import InstanceIcon   from '@/assets/icons/instance.svg?react'
import AnnotationIcon from '@/assets/icons/annotation.svg?react'

export type TabId = 'scene' | 'sample' | 'instance' | 'annotation'

const ACTIVE_COLOR   = '#4A90D9'
const INACTIVE_COLOR = '#ffffff'

export const TABS: {
  id:    TabId
  label: string
  Icon:  React.FC<React.SVGProps<SVGSVGElement>>
}[] = [
  { id: 'scene',      label: 'Scene',      Icon: SceneIcon },
  { id: 'sample',     label: 'Sample',     Icon: SampleIcon },
  { id: 'instance',   label: 'Instance',   Icon: InstanceIcon },
  { id: 'annotation', label: 'Annotation', Icon: AnnotationIcon },
]

interface HeaderProps {
  activeTab:    TabId
  onTabChange:  (tab: TabId) => void
}

export default function Header({ activeTab, onTabChange }: HeaderProps) {
  :
  中略
  :
  return (
    <header className="flex items-center h-12 bg-black px-3 gap-4 flex-shrink-0">
      :
      中略
      :
      <nav className="flex items-center gap-1">
        {TABS.map(({ id, label, Icon }) => {
          const isActive = activeTab === id
          const color    = isActive ? ACTIVE_COLOR : INACTIVE_COLOR
          return (
            <button
              key={id}
              onClick={() => handleTabChange(id)}
              className="flex flex-col items-center px-3 py-1 rounded transition-colors gap-0.5"
            >
              <Icon
                width={22}
                height={22}
                style={{ fill: color, color }}
              />
              <span
                className="text-xs font-medium"
                style={{ color }}
              >
                {label}
              </span>
            </button>
          )
        })}
      </nav>
    </header>
  )
}
```

`frontend/vite.config.ts`にもvite-plugin-svgrを追加しておく

```typescript
import svgr from 'vite-plugin-svgr'

export default defineConfig({
  plugins: [react(), svgr()],
})
```
