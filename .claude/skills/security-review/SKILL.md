---
name: security-review
description: 認証の追加、ユーザー入力の処理、シークレットの取り扱い、APIエンドポイントの作成、支払い/機密機能の実装時にこのスキルを使用。包括的なセキュリティチェックリストとパターンを提供。
---

# セキュリティレビュースキル

このスキルは、すべてのコードがセキュリティベストプラクティスに従い、潜在的な脆弱性を特定することを確保します。

## 有効化タイミング

- 認証または認可の実装
- ユーザー入力またはファイルアップロードの処理
- 新しいAPIエンドポイントの作成
- シークレットまたは認証情報の取り扱い
- 支払い機能の実装
- 機密データの保存または送信
- サードパーティAPIの統合

## セキュリティチェックリスト

### 1. シークレット管理

#### 絶対にしてはいけないこと
```python
# ハードコードされたシークレット
api_key = "sk-proj-xxxxx"
db_password = "password123"
```

#### 常にすべきこと
```python
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    anthropic_api_key: str
    secret_key: str

    class Config:
        env_file = ".env"

settings = Settings()

# シークレットが存在することを確認
if not settings.anthropic_api_key:
    raise ValueError("ANTHROPIC_API_KEYが設定されていません")
```

#### 確認ステップ
- [ ] ハードコードされたAPIキー、トークン、パスワードなし
- [ ] すべてのシークレットが環境変数に
- [ ] `.env`が.gitignoreに
- [ ] git履歴にシークレットなし
- [ ] 本番シークレットがホスティングプラットフォームに

### 2. 入力検証

#### 常にユーザー入力を検証
```python
from pydantic import BaseModel, Field, EmailStr, field_validator

class CreateUserSchema(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)
    age: int = Field(..., ge=0, le=150)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if "<script>" in v.lower():
            raise ValueError("無効な文字が含まれています")
        return v

# FastAPIでの使用
@router.post("/users")
async def create_user(user: CreateUserSchema, db: DbSession):
    # Pydanticが自動的に検証
    return await user_service.create(db, user)
```

#### ファイルアップロード検証
```python
from fastapi import UploadFile, HTTPException

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

async def validate_file_upload(file: UploadFile) -> None:
    """ファイルアップロードを検証"""
    # サイズチェック
    contents = await file.read()
    await file.seek(0)

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(400, "ファイルが大きすぎます（最大5MB）")

    # タイプチェック
    if file.content_type not in ["image/jpeg", "image/png", "image/gif"]:
        raise HTTPException(400, "無効なファイルタイプです")

    # 拡張子チェック
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, "無効なファイル拡張子です")
```

#### 確認ステップ
- [ ] すべてのユーザー入力がPydanticスキーマで検証済み
- [ ] ファイルアップロードが制限済み（サイズ、タイプ、拡張子）
- [ ] クエリでユーザー入力を直接使用していない
- [ ] ホワイトリスト検証（ブラックリストではない）
- [ ] エラーメッセージが機密情報を漏洩しない

### 3. SQLインジェクション防止

#### 絶対にSQL連結しない
```python
# 危険 - SQLインジェクション脆弱性
query = f"SELECT * FROM users WHERE email = '{user_email}'"
await session.execute(text(query))
```

#### 常にパラメータ化クエリを使用
```python
from sqlalchemy import select, text

# SQLAlchemy ORM（安全）
stmt = select(User).where(User.email == user_email)
result = await session.execute(stmt)

# 生SQL（パラメータ化）
stmt = text("SELECT * FROM users WHERE email = :email")
result = await session.execute(stmt, {"email": user_email})
```

#### 確認ステップ
- [ ] すべてのデータベースクエリがパラメータ化クエリを使用
- [ ] SQLで文字列連結なし
- [ ] SQLAlchemyが正しく使用されている

### 4. 認証・認可

#### JWT認証
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

def create_access_token(user_id: str, role: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=24)
    payload = {"sub": user_id, "role": role, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="認証情報が無効です",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await db.get(User, user_id)
    if user is None:
        raise credentials_exception
    return user
```

#### ロールベースアクセス制御
```python
from enum import Enum
from functools import wraps

class Role(str, Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"

def require_role(required_role: Role):
    """ロールチェックデコレーター"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            if current_user.role != required_role and current_user.role != Role.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="権限がありません"
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

# 使用例
@router.delete("/{id}")
@require_role(Role.ADMIN)
async def delete_user(id: str, current_user: User = Depends(get_current_user)):
    ...
```

#### 確認ステップ
- [ ] JWTトークンが適切に検証されている
- [ ] 機密操作前の認可チェック
- [ ] ロールベースアクセス制御が実装済み
- [ ] セッション管理が安全

### 5. XSS防止

#### HTMLをサニタイズ
```python
import bleach
from markupsafe import Markup

ALLOWED_TAGS = ["b", "i", "em", "strong", "p", "br"]
ALLOWED_ATTRIBUTES = {}

def sanitize_html(content: str) -> str:
    """ユーザー提供のHTMLをサニタイズ"""
    return bleach.clean(
        content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )

# Jinja2テンプレートでの使用
# 自動エスケープはデフォルトで有効
{{ user_input }}  # 自動的にエスケープ
{{ user_input | safe }}  # 信頼できるHTMLのみに使用
```

#### セキュリティヘッダー
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://unpkg.com; "
            "style-src 'self' 'unsafe-inline';"
        )
        return response

app = FastAPI()
app.add_middleware(SecurityHeadersMiddleware)
```

#### 確認ステップ
- [ ] ユーザー提供HTMLがサニタイズ済み
- [ ] セキュリティヘッダーが設定済み
- [ ] Jinja2の自動エスケープが有効

### 6. CSRF保護

#### CSRFトークン
```python
from fastapi_csrf_protect import CsrfProtect
from pydantic import BaseModel

class CsrfSettings(BaseModel):
    secret_key: str = settings.secret_key

@CsrfProtect.load_config
def get_csrf_config():
    return CsrfSettings()

# ルートでの使用
@router.post("/submit")
async def submit_form(
    request: Request,
    csrf_protect: CsrfProtect = Depends()
):
    await csrf_protect.validate_csrf(request)
    # フォーム処理
```

#### 確認ステップ
- [ ] 状態変更操作でCSRFトークン
- [ ] すべてのクッキーでSameSite属性設定

### 7. レート制限

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.get("/api/search")
@limiter.limit("10/minute")
async def search(request: Request, q: str):
    ...

@router.post("/api/login")
@limiter.limit("5/minute")
async def login(request: Request, credentials: LoginSchema):
    ...
```

#### 確認ステップ
- [ ] すべてのAPIエンドポイントでレート制限
- [ ] 高コスト操作でより厳しい制限
- [ ] IPベースレート制限

### 8. 機密データ露出

#### ログ
```python
import logging

logger = logging.getLogger(__name__)

# 間違い: 機密データをログ
logger.info(f"ユーザーログイン: {email}, パスワード: {password}")

# 正しい: 機密データを編集
logger.info(f"ユーザーログイン: {email}")
```

#### エラーメッセージ
```python
# 間違い: 内部詳細を露出
@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "traceback": traceback.format_exc()}
    )

# 正しい: 一般的なエラーメッセージ
@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    logger.exception("内部エラー")
    return JSONResponse(
        status_code=500,
        content={"error": "エラーが発生しました。再試行してください。"}
    )
```

#### 確認ステップ
- [ ] ログにパスワード、トークン、シークレットなし
- [ ] ユーザー向けエラーメッセージは一般的
- [ ] 詳細エラーはサーバーログのみ

### 9. 依存関係セキュリティ

```bash
# 脆弱性をチェック
pip-audit

# 依存関係を更新
pip install --upgrade -r requirements.txt

# セキュリティ更新のみ
safety check
```

#### 確認ステップ
- [ ] 依存関係が最新
- [ ] 既知の脆弱性なし
- [ ] 定期的なセキュリティ更新

## セキュリティテスト

### 自動セキュリティテスト
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_auth_required(client: AsyncClient):
    """認証が必要"""
    response = await client.get("/api/protected")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_admin_role_required(client: AsyncClient, user_token: str):
    """管理者ロールが必要"""
    response = await client.delete(
        "/api/users/123",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_rejects_invalid_input(client: AsyncClient):
    """無効な入力を拒否"""
    response = await client.post(
        "/api/users",
        json={"email": "not-an-email"}
    )
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_rate_limiting(client: AsyncClient):
    """レート制限を強制"""
    for _ in range(11):
        response = await client.get("/api/search?q=test")

    assert response.status_code == 429
```

## デプロイ前セキュリティチェックリスト

本番デプロイメント前に必須:

- [ ] **シークレット**: ハードコードされたシークレットなし、すべて環境変数に
- [ ] **入力検証**: すべてのユーザー入力がPydanticで検証済み
- [ ] **SQLインジェクション**: すべてのクエリがパラメータ化済み
- [ ] **XSS**: ユーザーコンテンツがサニタイズ済み
- [ ] **CSRF**: 保護が有効
- [ ] **認証**: JWT検証が適切
- [ ] **認可**: ロールチェックが実装済み
- [ ] **レート制限**: すべてのエンドポイントで有効
- [ ] **HTTPS**: 本番で強制
- [ ] **セキュリティヘッダー**: CSP、X-Frame-Optionsが設定済み
- [ ] **エラーハンドリング**: エラーに機密データなし
- [ ] **ログ**: 機密データがログされていない
- [ ] **依存関係**: 最新、脆弱性なし

## リソース

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPIセキュリティ](https://fastapi.tiangolo.com/tutorial/security/)
- [Webセキュリティアカデミー](https://portswigger.net/web-security)

---

**覚えておくこと**: セキュリティはオプションではありません。一つの脆弱性がプラットフォーム全体を危険にさらす可能性があります。疑わしい場合は、慎重な側に立ってください。
