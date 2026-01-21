---
name: frontend-patterns
description: htmx、Jinja2テンプレート、Alpine.js、CSS/Tailwindのためのフロントエンド開発パターンとベストプラクティス。
---

# フロントエンド開発パターン

htmx、Jinja2、Alpine.jsを使用したモダンなサーバーサイドレンダリングフロントエンドパターン。

## htmxパターン

### 基本的なhtmx属性

```html
<!-- hx-get: GETリクエストを送信 -->
<button hx-get="/api/markets" hx-target="#market-list">
  マーケット一覧を取得
</button>

<!-- hx-post: POSTリクエストを送信 -->
<form hx-post="/api/markets" hx-target="#market-list" hx-swap="beforeend">
  <input type="text" name="name" required>
  <button type="submit">マーケットを作成</button>
</form>

<!-- hx-put, hx-patch, hx-delete -->
<button hx-delete="/api/markets/123" hx-confirm="本当に削除しますか？">
  削除
</button>
```

### ターゲットとスワップ

```html
<!-- hx-target: レスポンスを挿入する要素 -->
<div id="content">
  <button hx-get="/partial/users" hx-target="#content">
    ユーザー一覧
  </button>
</div>

<!-- hx-swap: コンテンツの挿入方法 -->
<!-- innerHTML（デフォルト）: 内部を置換 -->
<div hx-get="/items" hx-swap="innerHTML"></div>

<!-- outerHTML: 要素全体を置換 -->
<div hx-get="/items" hx-swap="outerHTML"></div>

<!-- beforeend: 最後に追加 -->
<ul hx-get="/items" hx-swap="beforeend"></ul>

<!-- afterbegin: 最初に追加 -->
<ul hx-get="/items" hx-swap="afterbegin"></ul>

<!-- delete: 要素を削除 -->
<button hx-delete="/items/1" hx-swap="delete" hx-target="closest li">
  削除
</button>
```

### トリガーパターン

```html
<!-- click（デフォルト） -->
<button hx-get="/data">クリックで取得</button>

<!-- load: ページ読み込み時 -->
<div hx-get="/initial-data" hx-trigger="load"></div>

<!-- revealed: 表示された時（遅延読み込み） -->
<div hx-get="/more-items" hx-trigger="revealed"></div>

<!-- every: 定期的にポーリング -->
<div hx-get="/notifications" hx-trigger="every 30s"></div>

<!-- keyup with delay: デバウンス検索 -->
<input type="search"
       name="q"
       hx-get="/search"
       hx-trigger="keyup changed delay:500ms"
       hx-target="#search-results">

<!-- intersection: Intersection Observer -->
<div hx-get="/lazy-content" hx-trigger="intersect once"></div>
```

### フォーム処理

```html
<!-- 基本的なフォーム送信 -->
<form hx-post="/api/users" hx-target="#result">
  <input type="text" name="name" required>
  <input type="email" name="email" required>
  <button type="submit">登録</button>
</form>

<!-- バリデーションエラー表示 -->
<form hx-post="/api/users"
      hx-target="#form-container"
      hx-swap="outerHTML">
  <div id="form-container">
    <input type="text" name="name" required>
    <span class="error"></span>
    <button type="submit">送信</button>
  </div>
</form>

<!-- ファイルアップロード -->
<form hx-post="/api/upload"
      hx-encoding="multipart/form-data"
      hx-target="#upload-result">
  <input type="file" name="file">
  <button type="submit">アップロード</button>
</form>
```

### 無限スクロール

```html
<div id="item-list">
  {% for item in items %}
    <div class="item">{{ item.name }}</div>
  {% endfor %}

  <!-- 最後の要素が表示されたら次のページを読み込む -->
  <div hx-get="/items?page={{ next_page }}"
       hx-trigger="revealed"
       hx-swap="outerHTML"
       hx-target="this">
    読み込み中...
  </div>
</div>
```

### モーダルパターン

```html
<!-- モーダルトリガー -->
<button hx-get="/modals/edit-user/123"
        hx-target="#modal-container"
        hx-swap="innerHTML">
  編集
</button>

<!-- モーダルコンテナ -->
<div id="modal-container"></div>

<!-- モーダルテンプレート（部分テンプレート） -->
<!-- templates/partials/modal_edit_user.html -->
<div class="modal-backdrop" onclick="closeModal()">
  <div class="modal" onclick="event.stopPropagation()">
    <h2>ユーザー編集</h2>
    <form hx-put="/api/users/{{ user.id }}"
          hx-target="#modal-container"
          hx-swap="innerHTML">
      <input type="text" name="name" value="{{ user.name }}">
      <button type="submit">保存</button>
      <button type="button" onclick="closeModal()">キャンセル</button>
    </form>
  </div>
</div>
```

### リアルタイム更新（SSE）

```html
<!-- Server-Sent Events -->
<div hx-ext="sse"
     sse-connect="/events"
     sse-swap="message">
  <!-- SSEメッセージがここに挿入される -->
</div>

<!-- 特定のイベントタイプを購読 -->
<div hx-ext="sse" sse-connect="/events">
  <div sse-swap="notification">通知エリア</div>
  <div sse-swap="status">ステータスエリア</div>
</div>
```

## Jinja2テンプレートパターン

### ベーステンプレート

```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}アプリ{% endblock %}</title>
  <script src="https://unpkg.com/htmx.org@1.9.10"></script>
  <script defer src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"></script>
  <link href="/static/css/style.css" rel="stylesheet">
  {% block head %}{% endblock %}
</head>
<body>
  {% include "partials/header.html" %}

  <main>
    {% block content %}{% endblock %}
  </main>

  {% include "partials/footer.html" %}

  {% block scripts %}{% endblock %}
</body>
</html>
```

### ページテンプレート

```html
<!-- templates/pages/markets.html -->
{% extends "base.html" %}

{% block title %}マーケット一覧{% endblock %}

{% block content %}
<div class="container">
  <h1>マーケット一覧</h1>

  <!-- 検索フォーム -->
  <input type="search"
         name="q"
         placeholder="マーケットを検索..."
         hx-get="/markets/search"
         hx-trigger="keyup changed delay:500ms"
         hx-target="#market-list">

  <!-- マーケット一覧 -->
  <div id="market-list">
    {% include "partials/market_list.html" %}
  </div>
</div>
{% endblock %}
```

### 部分テンプレート（パーシャル）

```html
<!-- templates/partials/market_list.html -->
{% for market in markets %}
  {% include "partials/market_card.html" %}
{% else %}
  <p class="empty-state">マーケットが見つかりません</p>
{% endfor %}

{% if has_more %}
<div hx-get="/markets?page={{ next_page }}"
     hx-trigger="revealed"
     hx-swap="outerHTML">
  <span class="loading">読み込み中...</span>
</div>
{% endif %}
```

```html
<!-- templates/partials/market_card.html -->
<div class="market-card" id="market-{{ market.id }}">
  <h3>{{ market.name }}</h3>
  <p>{{ market.description | truncate(100) }}</p>
  <div class="market-meta">
    <span class="status status-{{ market.status }}">{{ market.status }}</span>
    <span class="date">{{ market.created_at | format_date }}</span>
  </div>
  <div class="market-actions">
    <button hx-get="/markets/{{ market.id }}/edit"
            hx-target="#modal-container">
      編集
    </button>
    <button hx-delete="/api/markets/{{ market.id }}"
            hx-target="#market-{{ market.id }}"
            hx-swap="outerHTML"
            hx-confirm="削除しますか？">
      削除
    </button>
  </div>
</div>
```

### カスタムフィルター

```python
# app/template_filters.py
from datetime import datetime
from markupsafe import Markup

def format_date(value: datetime, format: str = "%Y年%m月%d日") -> str:
    """日付をフォーマット"""
    if value is None:
        return ""
    return value.strftime(format)

def format_currency(value: float, currency: str = "JPY") -> str:
    """通貨をフォーマット"""
    if currency == "JPY":
        return f"¥{value:,.0f}"
    return f"${value:,.2f}"

def nl2br(value: str) -> Markup:
    """改行をbrタグに変換"""
    return Markup(value.replace("\n", "<br>"))

def truncate_words(value: str, length: int = 50) -> str:
    """文字数で切り詰め"""
    if len(value) <= length:
        return value
    return value[:length] + "..."


# FastAPIでの登録
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")
templates.env.filters["format_date"] = format_date
templates.env.filters["format_currency"] = format_currency
templates.env.filters["nl2br"] = nl2br
templates.env.filters["truncate_words"] = truncate_words
```

### マクロ

```html
<!-- templates/macros/forms.html -->
{% macro input(name, label, type="text", value="", required=false, error=none) %}
<div class="form-group {% if error %}has-error{% endif %}">
  <label for="{{ name }}">{{ label }}</label>
  <input type="{{ type }}"
         id="{{ name }}"
         name="{{ name }}"
         value="{{ value }}"
         {% if required %}required{% endif %}>
  {% if error %}
    <span class="error-message">{{ error }}</span>
  {% endif %}
</div>
{% endmacro %}

{% macro select(name, label, options, selected=none, required=false) %}
<div class="form-group">
  <label for="{{ name }}">{{ label }}</label>
  <select id="{{ name }}" name="{{ name }}" {% if required %}required{% endif %}>
    <option value="">選択してください</option>
    {% for value, text in options %}
      <option value="{{ value }}" {% if value == selected %}selected{% endif %}>
        {{ text }}
      </option>
    {% endfor %}
  </select>
</div>
{% endmacro %}

{% macro button(text, type="submit", variant="primary") %}
<button type="{{ type }}" class="btn btn-{{ variant }}">
  {{ text }}
</button>
{% endmacro %}
```

```html
<!-- マクロの使用 -->
{% from "macros/forms.html" import input, select, button %}

<form hx-post="/api/markets" hx-target="#result">
  {{ input("name", "マーケット名", required=true, error=errors.get("name")) }}
  {{ input("description", "説明", type="textarea") }}
  {{ select("category", "カテゴリ", categories, selected=market.category) }}
  {{ button("作成") }}
</form>
```

## Alpine.jsパターン

### 基本的な状態管理

```html
<!-- トグル -->
<div x-data="{ open: false }">
  <button @click="open = !open">メニュー</button>
  <div x-show="open" x-transition>
    メニューの内容
  </div>
</div>

<!-- カウンター -->
<div x-data="{ count: 0 }">
  <button @click="count--">-</button>
  <span x-text="count"></span>
  <button @click="count++">+</button>
</div>
```

### フォームバリデーション

```html
<form x-data="{
  name: '',
  email: '',
  errors: {},
  validate() {
    this.errors = {}
    if (!this.name) this.errors.name = '名前は必須です'
    if (!this.email) this.errors.email = 'メールは必須です'
    if (this.email && !this.email.includes('@')) {
      this.errors.email = '有効なメールアドレスを入力してください'
    }
    return Object.keys(this.errors).length === 0
  },
  submit() {
    if (this.validate()) {
      this.$refs.form.submit()
    }
  }
}" x-ref="form" @submit.prevent="submit">
  <div>
    <input type="text" x-model="name" placeholder="名前">
    <span x-show="errors.name" x-text="errors.name" class="error"></span>
  </div>
  <div>
    <input type="email" x-model="email" placeholder="メール">
    <span x-show="errors.email" x-text="errors.email" class="error"></span>
  </div>
  <button type="submit">送信</button>
</form>
```

### タブコンポーネント

```html
<div x-data="{ activeTab: 'overview' }">
  <div class="tabs">
    <button @click="activeTab = 'overview'"
            :class="{ 'active': activeTab === 'overview' }">
      概要
    </button>
    <button @click="activeTab = 'details'"
            :class="{ 'active': activeTab === 'details' }">
      詳細
    </button>
    <button @click="activeTab = 'history'"
            :class="{ 'active': activeTab === 'history' }">
      履歴
    </button>
  </div>

  <div x-show="activeTab === 'overview'">概要の内容</div>
  <div x-show="activeTab === 'details'">詳細の内容</div>
  <div x-show="activeTab === 'history'"
       x-init="$watch('activeTab', value => {
         if (value === 'history') {
           htmx.trigger($el, 'load-history')
         }
       })"
       hx-get="/history"
       hx-trigger="load-history">
    履歴を読み込み中...
  </div>
</div>
```

### htmxとの連携

```html
<!-- htmxリクエスト中のローディング状態 -->
<div x-data="{ loading: false }"
     @htmx:before-request="loading = true"
     @htmx:after-request="loading = false">

  <button hx-get="/api/data" hx-target="#result" :disabled="loading">
    <span x-show="!loading">データを取得</span>
    <span x-show="loading">読み込み中...</span>
  </button>

  <div id="result"></div>
</div>

<!-- 確認ダイアログ -->
<button x-data
        @click="if(confirm('削除しますか？')) htmx.trigger($el, 'confirmed')"
        hx-delete="/api/items/123"
        hx-trigger="confirmed">
  削除
</button>
```

## CSSパターン

### ユーティリティクラス（Tailwind風）

```css
/* static/css/utilities.css */

/* Flexbox */
.flex { display: flex; }
.flex-col { flex-direction: column; }
.items-center { align-items: center; }
.justify-between { justify-content: space-between; }
.gap-2 { gap: 0.5rem; }
.gap-4 { gap: 1rem; }

/* Spacing */
.p-2 { padding: 0.5rem; }
.p-4 { padding: 1rem; }
.m-2 { margin: 0.5rem; }
.m-4 { margin: 1rem; }
.mt-4 { margin-top: 1rem; }
.mb-4 { margin-bottom: 1rem; }

/* Typography */
.text-sm { font-size: 0.875rem; }
.text-lg { font-size: 1.125rem; }
.font-bold { font-weight: bold; }
.text-center { text-align: center; }

/* Colors */
.text-gray-500 { color: #6b7280; }
.text-red-500 { color: #ef4444; }
.bg-white { background-color: white; }
.bg-gray-100 { background-color: #f3f4f6; }

/* Borders */
.rounded { border-radius: 0.25rem; }
.rounded-lg { border-radius: 0.5rem; }
.border { border: 1px solid #e5e7eb; }

/* Shadow */
.shadow { box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.shadow-lg { box-shadow: 0 10px 15px rgba(0,0,0,0.1); }
```

### コンポーネントスタイル

```css
/* static/css/components.css */

/* ボタン */
.btn {
  display: inline-flex;
  align-items: center;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background-color: #3b82f6;
  color: white;
}

.btn-primary:hover {
  background-color: #2563eb;
}

.btn-danger {
  background-color: #ef4444;
  color: white;
}

/* カード */
.card {
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  padding: 1.5rem;
}

.card-header {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 1rem;
}

/* フォーム */
.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-group.has-error input {
  border-color: #ef4444;
}

.error-message {
  color: #ef4444;
  font-size: 0.875rem;
  margin-top: 0.25rem;
}

/* モーダル */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
}

.modal {
  background: white;
  border-radius: 0.5rem;
  padding: 1.5rem;
  max-width: 500px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
}
```

### htmx固有のスタイル

```css
/* htmxリクエスト中のスタイル */
.htmx-request {
  opacity: 0.5;
  pointer-events: none;
}

.htmx-request .loading-indicator {
  display: inline-block;
}

/* スワップアニメーション */
.htmx-swapping {
  opacity: 0;
  transition: opacity 0.2s ease-out;
}

.htmx-settling {
  opacity: 1;
  transition: opacity 0.2s ease-in;
}

/* 追加されたコンテンツのアニメーション */
.htmx-added {
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}
```

## FastAPIでのテンプレートレンダリング

```python
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

app = FastAPI()

# 静的ファイルとテンプレートの設定
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# カスタムフィルターを登録
templates.env.filters["format_date"] = format_date


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "pages/home.html",
        {"request": request, "title": "ホーム"}
    )


@app.get("/markets", response_class=HTMLResponse)
async def markets_page(request: Request, db: DbSession):
    markets = await market_service.get_all(db)
    return templates.TemplateResponse(
        "pages/markets.html",
        {"request": request, "markets": markets}
    )


# htmx用の部分テンプレート
@app.get("/markets/search", response_class=HTMLResponse)
async def search_markets(request: Request, q: str, db: DbSession):
    markets = await market_service.search(db, q)
    return templates.TemplateResponse(
        "partials/market_list.html",
        {"request": request, "markets": markets}
    )


# htmxリクエストの検出
@app.get("/data", response_class=HTMLResponse)
async def get_data(request: Request):
    is_htmx = request.headers.get("HX-Request") == "true"

    if is_htmx:
        # 部分テンプレートを返す
        return templates.TemplateResponse(
            "partials/data.html",
            {"request": request, "data": data}
        )
    else:
        # フルページを返す
        return templates.TemplateResponse(
            "pages/data.html",
            {"request": request, "data": data}
        )
```

## ベストプラクティス

### 1. プログレッシブエンハンスメント
- JavaScriptなしでも基本機能が動作するように設計
- htmxは機能拡張として追加

### 2. テンプレート構成
- ベーステンプレートで共通レイアウトを定義
- 部分テンプレートで再利用可能なコンポーネントを作成
- マクロでフォーム要素を標準化

### 3. パフォーマンス
- 部分テンプレートで必要な部分のみ更新
- 遅延読み込みで初期読み込みを高速化
- 適切なキャッシュヘッダーを設定

### 4. アクセシビリティ
- セマンティックなHTML要素を使用
- ARIA属性を適切に設定
- キーボードナビゲーションをサポート

**覚えておくこと**: htmx + Jinja2 + Alpine.jsの組み合わせは、シンプルで保守性の高いフロントエンドを実現します。複雑なSPAフレームワークなしで、インタラクティブなUIを構築できます。
