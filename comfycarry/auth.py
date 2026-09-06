"""
ComfyCarry — 认证模块 (Login/Logout + check_auth 中间件)
"""

import logging

from flask import Blueprint, request, jsonify, redirect, session
from flask.sessions import SecureCookieSessionInterface, SecureCookieSession
from itsdangerous import BadSignature

from . import config

auth_bp = Blueprint("auth", __name__)
_auth_log = logging.getLogger("comfycarry.auth")


def _err(key: str, status: int = 400, /, *, _extra: dict | None = None, **params):
    """错误响应。前端按 `auth.err.<key>` 翻译; _extra 是响应体的附加顶层字段。"""
    body = {"error_key": f"auth.err.{key}", "error_params": params}
    if _extra:
        body.update(_extra)
    return jsonify(body), status


# ── 自定义 Session Interface ─────────────────────────────────
# 容忍 NTP 时钟回调导致的 "future timestamp" (Signature age < 0)
class DebugSessionInterface(SecureCookieSessionInterface):
    def open_session(self, app, req):
        s = self.get_signing_serializer(app)
        if s is None:
            return None
        val = req.cookies.get(self.get_cookie_name(app))
        if not val:
            return self.session_class()
        max_age = int(app.permanent_session_lifetime.total_seconds())
        try:
            data = s.loads(val, max_age=max_age)
            return self.session_class(data)
        except BadSignature as e:
            # NTP clock skew: cookie signed slightly in the future
            # HMAC is valid, only the timestamp check fails — safe to accept
            if "< 0 seconds" in str(e):
                try:
                    data = s.loads(val)  # skip age check
                    _auth_log.info("session accepted despite clock skew: %s", e)
                    return self.session_class(data)
                except BadSignature:
                    pass
            _auth_log.warning(
                "session BadSignature on %s %s | error=%s cookie_len=%d cookie_prefix=%s",
                req.method, req.path, e, len(val), val[:32],
            )
            return self.session_class()


@auth_bp.route("/login", methods=["POST"])
def login():
    pw = (request.get_json(silent=True) or {}).get("password", "")
    if pw == config.DASHBOARD_PASSWORD:
        session.permanent = True
        session["authed"] = True
        return jsonify(ok=True)
    return _err("invalid_password", 401)


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


def register_auth_middleware(app):
    """注册全局认证中间件到 Flask app"""

    # Setup 阶段额外放行的精确路由 (集中维护)
    _SETUP_OPEN_ROUTES = {
        "/api/settings/import-config",  # 配置导入
        "/api/tunnel/validate",         # Tunnel 验证 (Wizard Step 2)
        "/api/llm/models",              # LLM 模型列表 (Wizard Step 6)
    }

    # 部署完成后**不再**免鉴权的 setup 路由 —— 它们会改写向导状态、
    # 拉起部署或代面板发外部请求, 部署完成后没有合法用途。
    # 正常的重新部署路径是先调 /api/settings/reinitialize (需鉴权) 删掉
    # setup state, 那之后 _is_setup_complete() 为假, 这里自然重新放行。
    # /api/setup/state 与 /api/setup/log_stream 仍始终放行: 只读, 且部署
    # 完成的瞬间向导页还在轮询它们显示结果。
    _SETUP_PRIVILEGED_ROUTES = {
        "/api/setup/save",
        "/api/setup/deploy",
        "/api/setup/preview_remotes",
    }

    @app.before_request
    def check_auth():
        """全局鉴权与 Setup Wizard 路由"""
        # Setup 相关路由: 部署未完成时全部放行 (此时还没有密码);
        # 已完成则把写/触发类路由交回正常鉴权, 只读的继续放行。
        if request.path.startswith("/api/setup/") or request.path == "/setup":
            if not (config._is_setup_complete()
                    and request.path in _SETUP_PRIVILEGED_ROUTES):
                return
        # Setup 阶段额外放行的路由
        if not config._is_setup_complete() and request.path in _SETUP_OPEN_ROUTES:
            return
        if request.path in ("/login", "/favicon.ico", "/api/version"):
            return
        # Companion 客户端连接: 仅凭面板密码换 API Key, 自身做密码校验,
        # 在鉴权前放行 (此时客户端无任何凭据)。仅放行该单一 POST 端点。
        if request.method == "POST" and request.path == "/api/companion/connect":
            return
        if (
            request.path.startswith("/static/")
            or request.path.startswith("/assets/")
            or request.path.startswith("/fonts/")
            or request.path in (
                "/apple-touch-icon.png", "/logo.png", "/logo-small.png",
                "/logo-mark.svg", "/logo-tile.svg",
            )
        ):
            return
        # 如果尚未完成部署向导, 重定向到向导页
        if not config._is_setup_complete():
            if request.path.startswith("/api/"):
                return _err("setup_required", 503, _extra={"setup_required": True})
            if request.path != "/":
                return redirect("/")
            return  # 让 index() 处理向导页渲染
        # 正常鉴权
        if not config.DASHBOARD_PASSWORD:
            return
        if session.get("authed"):
            return
        # API Key 认证 (X-API-Key header 或 Authorization: Bearer)
        api_key = request.headers.get("X-API-Key") or ""
        if not api_key:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                api_key = auth_header[7:]
        if api_key and api_key == config.API_KEY:
            return
        if request.path.startswith("/api/"):
            cookie_name = app.config.get("SESSION_COOKIE_NAME", "")
            _auth_log.warning(
                "401 %s | cookie_present=%s",
                request.path,
                cookie_name in request.cookies,
            )
            return _err("unauthorized", 401)
        return redirect("/login")
