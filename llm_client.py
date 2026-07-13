"""
LLM 客户端 — 多模型支持
=======================

支持多种模型后端，通过环境变量或参数切换：

    Anthropic 原生格式 (Claude):
        python agent_workflow.py --industry "AI算力" --model-backend anthropic

    OpenAI 兼容格式 (DeepSeek / 通义千问 / 豆包 / OpenAI 等):
        export OPENAI_BASE_URL="https://api.deepseek.com/v1"
        export OPENAI_API_KEY="sk-xxx"
        python agent_workflow.py --industry "AI算力" --model-backend openai_compat

无 API key 时自动降级，输出 Prompt 模板供手动使用。
"""

import os
import time
from typing import Optional

import requests

from config import config


class LLMClient:
    """多模型 LLM 客户端。无 key 时自动降级为离线 Prompt 输出模式。"""

    # ── 模型后端配置 ──────────────────────────────────────────

    ANTHROPIC_API_URL = config.ANTHROPIC_API_URL
    ANTHROPIC_VERSION = config.ANTHROPIC_VERSION

    DEFAULT_ANTHROPIC_MODEL = config.DEFAULT_ANTHROPIC_MODEL
    DEFAULT_OPENAI_COMPAT_MODEL = config.DEFAULT_OPENAI_COMPAT_MODEL

    def __init__(
        self,
        model_backend: str = "",
        api_key: str = "",
        base_url: str = "",
        model: str = "",
    ):
        """
        Args:
            model_backend: "anthropic" | "openai_compat"（默认自动检测）
            api_key: API 密钥，优先于环境变量
            base_url: OpenAI 兼容 API 的 base URL
            model: 模型名称，不传则使用后端默认模型
        """
        self.model_backend = model_backend or self._detect_backend()

        if self.model_backend == "openai_compat":
            self.api_key = (
                api_key or os.environ.get("OPENAI_API_KEY", "")
            )
            self.base_url = (
                base_url
                or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
            )
            self.model = (
                model
                or os.environ.get("OPENAI_MODEL", self.DEFAULT_OPENAI_COMPAT_MODEL)
            )
            self.api_url = self.base_url.rstrip("/") + "/chat/completions"
        else:
            # Anthropic 后端：支持 ANTHROPIC_BASE_URL（代理）和 ANTHROPIC_AUTH_TOKEN（Bearer 认证）
            self.api_key = (
                api_key
                or os.environ.get("ANTHROPIC_AUTH_TOKEN")
                or os.environ.get("ANTHROPIC_API_KEY", "")
            )
            self.base_url = (
                base_url
                or os.environ.get("ANTHROPIC_BASE_URL")
                or self.ANTHROPIC_API_URL
            )
            self.model = (
                model
                or os.environ.get("ANTHROPIC_MODEL", self.DEFAULT_ANTHROPIC_MODEL)
            )
            self.api_url = self.base_url.rstrip("/") + "/messages"
            # 是否使用 Bearer Token 认证（ANTHROPIC_AUTH_TOKEN），而非 x-api-key
            self._use_bearer_auth = bool(
                not api_key and os.environ.get("ANTHROPIC_AUTH_TOKEN")
            )

        self._error_shown = False

    @staticmethod
    def _detect_backend() -> str:
        """根据环境变量自动检测后端类型。"""
        if os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_BASE_URL"):
            return "openai_compat"
        if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"):
            return "anthropic"
        return "anthropic"  # 默认尝试 Anthropic

    @property
    def is_available(self) -> bool:
        """是否有有效的 API key。"""
        return bool(self.api_key)

    # ── 核心请求方法 ──────────────────────────────────────────

    def ask(
        self,
        prompt: str,
        system: str = "",
        temperature: float = None,
        max_tokens: int = 4096,
    ) -> Optional[str]:
        """
        发送请求到 LLM，最多重试 3 次。

        Args:
            prompt: 用户消息
            system: 系统提示词
            temperature: 温度参数（分析类任务建议 0.3，默认从 config 读取）
            max_tokens: 最大输出 token 数

        Returns:
            模型输出文本，失败时返回 None
        """
        if not self.is_available:
            return None

        if temperature is None:
            temperature = config.TEMPERATURE

        # 每次调用时重置错误展示标志（避免一次失败后永久静默）
        self._error_shown = False

        for attempt in range(3):
            try:
                if self.model_backend == "openai_compat":
                    return self._ask_openai_compat(
                        prompt, system, temperature, max_tokens
                    )
                else:
                    return self._ask_anthropic(
                        prompt, system, temperature, max_tokens
                    )

            except requests.exceptions.Timeout:
                self._handle_error("网络连接超时", attempt)
                time.sleep(2 ** (attempt + 1))
            except requests.exceptions.ConnectionError:
                self._handle_error("网络连接失败", attempt)
                time.sleep(2)
            except Exception as exc:
                if attempt == 2 and not self._error_shown:
                    print(
                        f"⚠️  API 调用失败: {exc}，已自动降级为离线模式"
                    )
                    self._error_shown = True
                return None

        return None

    def _ask_anthropic(
        self,
        prompt: str,
        system: str,
        temperature: float,
        max_tokens: int,
    ) -> Optional[str]:
        """通过 Anthropic 原生 Messages API 发送请求。

        支持两种认证方式：
        - x-api-key: 标准 Anthropic API key
        - Authorization: Bearer: 本地代理（如 ANTHROPIC_AUTH_TOKEN）
        """
        headers = {
            "anthropic-version": self.ANTHROPIC_VERSION,
            "content-type": "application/json",
        }
        if self._use_bearer_auth:
            headers["Authorization"] = f"Bearer {self.api_key}"
        else:
            headers["x-api-key"] = self.api_key

        resp = requests.post(
            self.api_url,
            headers=headers,
            json={
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "system": system,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=120,
        )

        if resp.status_code == 200:
            text_parts = []
            for block in resp.json().get("content", []):
                if block.get("type") == "text":
                    text_parts.append(block.get("text", ""))
            return "\n".join(text_parts)

        if resp.status_code == 429:
            retry_after = _parse_retry_after(resp.headers)
            time.sleep(retry_after)
            raise ConnectionError("请求频率限制(429)")

        self._handle_error(f"API 错误 {resp.status_code}", 0)
        return None

    def _ask_openai_compat(
        self,
        prompt: str,
        system: str,
        temperature: float,
        max_tokens: int,
    ) -> Optional[str]:
        """通过 OpenAI 兼容 Chat Completions API 发送请求（DeepSeek/通义千问/豆包等）。"""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        resp = requests.post(
            self.api_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout=120,
        )

        if resp.status_code == 200:
            data = resp.json()
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")
            return None

        if resp.status_code == 429:
            retry_after = _parse_retry_after(resp.headers)
            time.sleep(retry_after)
            raise ConnectionError("请求频率限制(429)")

        self._handle_error(f"API 错误 {resp.status_code}", 0)
        return None

    def _handle_error(self, msg: str, attempt: int):
        """控制错误信息的显示频率。"""
        if not self._error_shown and attempt == 0:
            print(f"⚠️  {msg}，已自动降级为离线模式")
            self._error_shown = True

    # ── 带日志的便捷方法 ──────────────────────────────────────

    def ask_with_log(
        self,
        prompt: str,
        system: str = "",
        label: str = "",
        temperature: float = None,
        max_tokens: int = 4096,
    ) -> Optional[str]:
        """发送请求并打印耗时日志。"""
        t0 = time.time()
        response = self.ask(
            prompt, system=system, temperature=temperature, max_tokens=max_tokens
        )
        elapsed = time.time() - t0
        if response:
            backend_label = (
                "Anthropic"
                if self.model_backend == "anthropic"
                else "OpenAI兼容"
            )
            print(
                f"  ✅ [{label}] {backend_label}/{self.model} "
                f"({elapsed:.1f}s, {len(response)} chars)"
            )
        return response

    @classmethod
    def list_available_backends(cls) -> list[str]:
        """列出可用的后端类型。"""
        return ["anthropic", "openai_compat"]


# ── 向后兼容别名 ──────────────────────────────────────────────

# ClaudeClient 保留，指向 LLMClient，方便老代码不报错
ClaudeClient = LLMClient  # type: ignore


def _parse_retry_after(headers: dict) -> float:
    """Parse Retry-After header, return seconds to wait (default 2s)."""
    try:
        value = headers.get("Retry-After", "2")
        return float(value) if value.replace(".", "").isdigit() else 2.0
    except Exception:
        return 2.0
