# エラーハンドリング設計

## 5.1 例外階層設計

### 5.1.1 統一入力例外体系

```python
class InputSystemError(Exception):
    """統一入力システム例外の基底クラス"""
    
    def __init__(self, message: str, event: Optional[InputEvent] = None, cause: Optional[Exception] = None):
        super().__init__(message)
        self.event = event
        self.cause = cause
        self.timestamp = time.time()
    
    def get_error_details(self) -> Dict[str, Any]:
        """詳細エラー情報の取得"""
        return {
            "error_type": self.__class__.__name__,
            "message": str(self),
            "timestamp": self.timestamp,
            "event": self.event.to_dict() if self.event else None,
            "cause": str(self.cause) if self.cause else None,
        }

# 第2レベル: カテゴリ別例外
class InputHandlerError(InputSystemError):
    """入力ハンドラ関連エラー"""
    pass

class InputEventError(InputSystemError):
    """入力イベント関連エラー"""
    pass

class InputSystemConfigError(InputSystemError):
    """システム設定関連エラー"""
    pass

class FallbackError(InputSystemError):
    """フォールバック処理関連エラー"""
    pass

# 第3レベル: 具体的例外
class HandlerNotSetError(InputHandlerError):
    """入力ハンドラ未設定エラー"""
    def __init__(self, event: InputEvent):
        super().__init__(
            f"No input handler configured for {event.get_display_name()}",
            event
        )

class HandlerExecutionError(InputHandlerError):
    """ハンドラ実行エラー"""
    def __init__(self, message: str, event: InputEvent, cause: Exception):
        super().__init__(message, event, cause)

class HandlerTimeoutError(InputHandlerError):
    """ハンドラタイムアウトエラー"""
    def __init__(self, timeout_seconds: float, event: InputEvent):
        super().__init__(
            f"Handler timeout after {timeout_seconds}s for {event.get_display_name()}",
            event
        )
        self.timeout_seconds = timeout_seconds

class InvalidInputTypeError(InputEventError):
    """不正な入力タイプエラー"""
    def __init__(self, input_type: str):
        super().__init__(f"Invalid input type: {input_type}")
        self.input_type = input_type

class InvalidParameterError(InputEventError):
    """不正なパラメータエラー"""
    def __init__(self, parameter_name: str, parameter_value: Any, event: InputEvent):
        super().__init__(
            f"Invalid parameter {parameter_name}={parameter_value} for {event.get_display_name()}",
            event
        )
        self.parameter_name = parameter_name
        self.parameter_value = parameter_value

class FallbackNotSetError(FallbackError):
    """フォールバック未設定エラー"""
    def __init__(self, event: InputEvent):
        super().__init__(
            f"No fallback stream configured for {event.get_display_name()}",
            event
        )

class FallbackExecutionError(FallbackError):
    """フォールバック実行エラー"""
    def __init__(self, message: str, event: InputEvent, cause: Exception):
        super().__init__(message, event, cause)

class UnsupportedInputTypeError(InputSystemError):
    """未サポート入力タイプエラー"""
    def __init__(self, input_type: str, supported_types: Set[str]):
        super().__init__(
            f"Input type '{input_type}' not supported. Supported: {supported_types}"
        )
        self.input_type = input_type
        self.supported_types = supported_types
```

### 5.1.2 エラーコード定義

```python
class ErrorCode:
    """統一入力システムエラーコード"""
    
    # ハンドラ関連 (1000番台)
    HANDLER_NOT_SET = 1001
    HANDLER_EXECUTION_FAILED = 1002
    HANDLER_TIMEOUT = 1003
    HANDLER_INVALID_RETURN = 1004
    
    # イベント関連 (2000番台)
    INVALID_INPUT_TYPE = 2001
    INVALID_PARAMETER = 2002
    EVENT_CREATION_FAILED = 2003
    
    # システム設定関連 (3000番台)
    SYSTEM_NOT_INITIALIZED = 3001
    INVALID_CONFIGURATION = 3002
    
    # フォールバック関連 (4000番台)
    FALLBACK_NOT_SET = 4001
    FALLBACK_EXECUTION_FAILED = 4002
    UNSUPPORTED_FALLBACK_TYPE = 4003
    
    # 一般エラー (9000番台)
    UNKNOWN_ERROR = 9001
    SYSTEM_ERROR = 9002

class InputSystemError(Exception):
    def __init__(self, message: str, error_code: int = None, **kwargs):
        super().__init__(message)
        self.error_code = error_code or ErrorCode.UNKNOWN_ERROR
        # その他の属性...
```

### 5.1.3 エラーメッセージ仕様

```python
class ErrorMessages:
    """多言語対応エラーメッセージ"""
    
    _messages = {
        "en": {
            ErrorCode.HANDLER_NOT_SET: "No input handler is configured. Set a handler using set_input_handler().",
            ErrorCode.HANDLER_EXECUTION_FAILED: "Input handler execution failed: {cause}",
            ErrorCode.HANDLER_TIMEOUT: "Input handler timed out after {timeout}s",
            ErrorCode.INVALID_INPUT_TYPE: "Invalid input type '{input_type}'. Expected one of: {valid_types}",
            ErrorCode.FALLBACK_NOT_SET: "No fallback stream configured and handler failed",
        },
        "ja": {
            ErrorCode.HANDLER_NOT_SET: "入力ハンドラが設定されていません。set_input_handler()でハンドラを設定してください。",
            ErrorCode.HANDLER_EXECUTION_FAILED: "入力ハンドラの実行が失敗しました: {cause}",
            ErrorCode.HANDLER_TIMEOUT: "入力ハンドラが{timeout}秒でタイムアウトしました",
            ErrorCode.INVALID_INPUT_TYPE: "不正な入力タイプ'{input_type}'です。有効なタイプ: {valid_types}",
            ErrorCode.FALLBACK_NOT_SET: "フォールバックストリームが設定されておらず、ハンドラも失敗しました",
        }
    }
    
    @classmethod
    def get_message(cls, error_code: int, language: str = "en", **format_args) -> str:
        """エラーメッセージの取得"""
        messages = cls._messages.get(language, cls._messages["en"])
        template = messages.get(error_code, "Unknown error (code: {error_code})")
        return template.format(error_code=error_code, **format_args)

# 使用例
class HandlerNotSetError(InputHandlerError):
    def __init__(self, event: InputEvent, language: str = "en"):
        message = ErrorMessages.get_message(ErrorCode.HANDLER_NOT_SET, language)
        super().__init__(message, ErrorCode.HANDLER_NOT_SET, event)
```

## 5.2 エラー処理フロー

### 5.2.1 ハンドラ例外処理

```python
class UnifiedInputSystem:
    def _execute_handler(self, event: InputEvent) -> Optional[str]:
        """ハンドラ実行（例外処理込み）"""
        with self._handler_lock:
            current_handler = self._handler
        
        if not current_handler:
            raise HandlerNotSetError(event)
        
        try:
            # タイムアウト設定
            timeout = event.get_arg("timeout_seconds", self._default_timeout)
            
            if timeout > 0:
                result = self._execute_with_timeout(current_handler, event, timeout)
            else:
                result = current_handler.handle_input_request(event)
            
            # 戻り値検証
            self._validate_handler_result(result, event)
            return result
        
        except HandlerTimeoutError:
            # タイムアウトはそのまま再発生
            raise
        
        except Exception as e:
            # その他の例外をシステム例外に変換
            raise HandlerExecutionError(
                f"Handler {current_handler.__class__.__name__} failed",
                event,
                e
            )
    
    def _execute_with_timeout(self, handler: InputHandler, event: InputEvent, timeout: float) -> Optional[str]:
        """タイムアウト付きハンドラ実行"""
        import signal
        
        def timeout_handler(signum, frame):
            raise HandlerTimeoutError(timeout, event)
        
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(timeout))
        
        try:
            return handler.handle_input_request(event)
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    
    def _validate_handler_result(self, result: Any, event: InputEvent) -> None:
        """ハンドラ戻り値の検証"""
        if result is not None and not isinstance(result, str):
            raise HandlerExecutionError(
                f"Handler returned invalid type {type(result)}. Expected str or None.",
                event,
                TypeError(f"Invalid return type: {type(result)}")
            )
```

### 5.2.2 フォールバック時の例外

```python
class UnifiedInputSystem:
    def _execute_fallback(self, event: InputEvent) -> Optional[str]:
        """フォールバック実行（例外処理込み）"""
        if not self._fallback_stream:
            raise FallbackNotSetError(event)
        
        try:
            # 入力タイプ別フォールバック処理
            if event.input_type == InputType.CHAR:
                result = self._fallback_stream.read_char()
            elif event.input_type == InputType.LINE:
                result = self._fallback_stream.read_line()
            else:
                # 未サポートタイプ
                supported_types = {InputType.CHAR, InputType.LINE}
                raise UnsupportedInputTypeError(event.input_type, supported_types)
            
            self._logger.info(f"Fallback successful for {event.get_display_name()}")
            return result
        
        except UnsupportedInputTypeError:
            # 未サポートはそのまま再発生
            raise
        
        except Exception as e:
            # フォールバックストリームの例外をシステム例外に変換
            raise FallbackExecutionError(
                f"Fallback stream {self._fallback_stream.__class__.__name__} failed",
                event,
                e
            )
```

### 5.2.3 システム例外処理

```python
class UnifiedInputSystem:
    def request_input(self, input_type: str, predicate_name: str, **kwargs) -> Optional[str]:
        """統一入力要求（最上位例外処理）"""
        try:
            # 入力検証
            if not self._validate_input_type(input_type):
                raise InvalidInputTypeError(input_type)
            
            # イベント生成
            event = self._create_event(input_type, predicate_name, kwargs)
            
            # 履歴記録
            self._record_event(event)
            
            # ハンドラ実行
            try:
                result = self._execute_handler(event)
                if result is not None:
                    self._record_success(event, result)
                    return result
            except InputHandlerError as e:
                # ハンドラエラーをログ記録してフォールバックへ
                self._logger.warning(f"Handler failed: {e}")
                self._record_handler_failure(event, e)
            
            # フォールバック実行
            try:
                result = self._execute_fallback(event)
                self._record_fallback_success(event, result)
                return result
            except FallbackError as e:
                # フォールバックも失敗
                self._record_fallback_failure(event, e)
                raise
        
        except InputSystemError:
            # システム例外はそのまま再発生
            raise
        
        except Exception as e:
            # 予期しない例外をシステム例外に変換
            self._logger.error(f"Unexpected error in input system: {e}")
            raise InputSystemError(
                f"Unexpected system error: {e}",
                ErrorCode.SYSTEM_ERROR
            ) from e
```

## 5.3 復旧・リトライ機構

### 5.3.1 自動復旧戦略

```python
class RecoveryStrategy:
    """自動復旧戦略"""
    
    def __init__(self, max_retries: int = 3, backoff_factor: float = 1.0):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
    
    def should_retry(self, error: Exception, attempt: int) -> bool:
        """リトライ判定"""
        if attempt >= self.max_retries:
            return False
        
        # リトライ可能な例外タイプ
        retryable_errors = (
            HandlerExecutionError,
            HandlerTimeoutError,
            FallbackExecutionError,
        )
        
        return isinstance(error, retryable_errors)
    
    def get_wait_time(self, attempt: int) -> float:
        """待機時間計算（指数バックオフ）"""
        return self.backoff_factor * (2 ** attempt)

class UnifiedInputSystem:
    def __init__(self):
        # 既存の初期化...
        self.recovery_strategy = RecoveryStrategy()
        self.enable_auto_recovery = True
    
    def request_input_with_recovery(self, input_type: str, predicate_name: str, **kwargs) -> Optional[str]:
        """復旧機能付き入力要求"""
        if not self.enable_auto_recovery:
            return self.request_input(input_type, predicate_name, **kwargs)
        
        last_error = None
        for attempt in range(self.recovery_strategy.max_retries + 1):
            try:
                return self.request_input(input_type, predicate_name, **kwargs)
            
            except Exception as e:
                last_error = e
                
                if not self.recovery_strategy.should_retry(e, attempt):
                    break
                
                wait_time = self.recovery_strategy.get_wait_time(attempt)
                self._logger.info(f"Retrying after {wait_time}s (attempt {attempt + 1})")
                time.sleep(wait_time)
        
        # 全リトライ失敗
        raise last_error
```

### 5.3.2 リトライポリシー

```python
class RetryPolicy:
    """リトライポリシー設定"""
    
    def __init__(self):
        self.policies = {}
    
    def set_policy(self, error_type: type, max_retries: int, backoff: str = "exponential"):
        """エラータイプ別リトライポリシー設定"""
        self.policies[error_type] = {
            "max_retries": max_retries,
            "backoff": backoff
        }
    
    def get_policy(self, error: Exception) -> Dict[str, Any]:
        """エラーに対するポリシー取得"""
        error_type = type(error)
        return self.policies.get(error_type, {
            "max_retries": 1,
            "backoff": "fixed"
        })

# デフォルトポリシー設定
def setup_default_retry_policies(unified_system: UnifiedInputSystem):
    """デフォルトリトライポリシーの設定"""
    policy = RetryPolicy()
    
    # ハンドラタイムアウト: 少ないリトライ
    policy.set_policy(HandlerTimeoutError, max_retries=1, backoff="fixed")
    
    # ハンドラ実行エラー: 中程度のリトライ
    policy.set_policy(HandlerExecutionError, max_retries=3, backoff="exponential")
    
    # フォールバックエラー: リトライしない
    policy.set_policy(FallbackExecutionError, max_retries=0, backoff="none")
    
    unified_system.retry_policy = policy
```

### 5.3.3 フェイルオーバー設計

```python
class FailoverHandler(InputHandler):
    """フェイルオーバー対応ハンドラ"""
    
    def __init__(self, primary_handler: InputHandler, backup_handlers: List[InputHandler]):
        self.primary_handler = primary_handler
        self.backup_handlers = backup_handlers
        self.current_handler_index = 0  # 0=primary, 1+=backup
    
    def handle_input_request(self, event: InputEvent) -> Optional[str]:
        """プライマリ→バックアップの順でフェイルオーバー実行"""
        handlers = [self.primary_handler] + self.backup_handlers
        
        for i, handler in enumerate(handlers):
            try:
                result = handler.handle_input_request(event)
                
                # 成功した場合
                if i != self.current_handler_index:
                    self._logger.info(f"Failover to handler {i}: {handler.__class__.__name__}")
                    self.current_handler_index = i
                
                return result
            
            except Exception as e:
                self._logger.warning(f"Handler {i} failed: {e}")
                
                # 最後のハンドラも失敗した場合は例外を再発生
                if i == len(handlers) - 1:
                    raise
        
        return None

# 使用例
primary_handler = GUIInputHandler()
backup1 = ConsoleInputHandler()  
backup2 = MockInputHandler({"char": "x", "line": "backup"})

failover_handler = FailoverHandler(primary_handler, [backup1, backup2])
runtime.io_manager.set_input_handler(failover_handler)
```

**ヘルスチェック機能:**
```python
class HealthCheckableHandler(InputHandler):
    """ヘルスチェック対応ハンドラ"""
    
    def health_check(self) -> bool:
        """ハンドラの健全性確認"""
        return True  # 実装依存
    
    def handle_input_request(self, event: InputEvent) -> Optional[str]:
        if not self.health_check():
            raise HandlerExecutionError("Handler health check failed", event, None)
        
        # 通常処理
        return self._do_handle_input(event)
    
    def _do_handle_input(self, event: InputEvent) -> Optional[str]:
        # 実際の入力処理
        pass

class AutoFailoverSystem:
    """自動フェイルオーバーシステム"""
    
    def __init__(self, unified_system: UnifiedInputSystem):
        self.unified_system = unified_system
        self.health_check_interval = 30  # 30秒間隔
        self.health_check_thread = None
        self.running = False
    
    def start_health_monitoring(self):
        """ヘルスモニタリング開始"""
        self.running = True
        self.health_check_thread = threading.Thread(target=self._health_check_loop)
        self.health_check_thread.start()
    
    def _health_check_loop(self):
        """ヘルスチェックループ"""
        while self.running:
            handler = self.unified_system.get_input_handler()
            if isinstance(handler, HealthCheckableHandler):
                if not handler.health_check():
                    self._trigger_failover()
            
            time.sleep(self.health_check_interval)
    
    def _trigger_failover(self):
        """フェイルオーバー発動"""
        self._logger.warning("Health check failed, triggering failover")
        # フェイルオーバー処理の実装
```