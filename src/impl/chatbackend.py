# chatbackend/chatbackend.py
"""High‑level chat backend with flexible caching, hooks, and optional LLM integration.

Run demo:
    python -m chatbackend.chatbackend
The demo feeds three static user prompts; an auto‑reply hook invokes the LLM and prints the exchange.
"""
from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, Callable, Dict, List, Optional

from impl.schemes import ChatMessage 
from impl.myllmservice import MyLLMService


class ChatBackend:
    """In‑memory chat store that can optionally generate AI responses."""
     
    # ------------------------------------------------------------------ #
    # Construction
    # ------------------------------------------------------------------ #
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        hook: Optional[Callable[["ChatBackend", ChatMessage], None]] = None,
        my_llm_service: Optional[MyLLMService] = None,
    ) -> None:
        self.config: Dict[str, Any] = config or {}
        self._messages: List[ChatMessage] = []
        self._next_id: int = 1

        self.last_message: Optional[ChatMessage] = None
        self.last_ai_message: Optional[ChatMessage] = None

        self._hook: Optional[Callable[["ChatBackend", ChatMessage], None]] = hook
        self.llm: MyLLMService = my_llm_service or MyLLMService()

        self.system_prompt: Optional[str] = self.config.get("system_prompt")
        init_time = datetime.now(timezone.utc)
        self.chatbackend_init_time: str = init_time.strftime("%Y-%m-%d__%H:%M:%S")
        self.session_name: str = f"session_{self.chatbackend_init_time}"
    
    # ------------------------------------------------------------------ #
    # Message helpers
    # ------------------------------------------------------------------ #
    
    def bring_last_n_messages(self, *, n: int = 4) -> List[ChatMessage]:
        """Return the last *n* messages (oldest → newest)."""
        if n <= 0:
            return []
        return self._messages[-n:]

    def compile_chat_messages_to_string(self, chat_messages: List[ChatMessage]) -> str:
        """Convert a list of ChatMessage objects into a single text block."""
        custom_formatter = self.config.get("history_formatter")
        if callable(custom_formatter):
            return custom_formatter(chat_messages)

        return "\n".join(
            f"{m.user_type.lower()}|{m.user_name}: {m.message}" for m in chat_messages
        )

    def generate_chat_history(self, *, n: int = 4) -> str:
        """Return the last *n* messages as a formatted string for the LLM."""
        return self.compile_chat_messages_to_string(self.bring_last_n_messages(n=n))

    def produce_ai_response(self, *, history_count: int = 4) -> str:
        """Generate and store an assistant reply using the configured LLM service."""
        if not self.last_message or self.last_message.user_type.lower() != "user":
            return "I don’t know"

        history = self.generate_chat_history(n=history_count)


        print("history:", history) 


        generation_response = self.llm.generate_ai_answer(
            chat_history=history,
            user_msg=self.last_message.message,
            # system_prompt=self.system_prompt,
        )


        print("generaion success:", generation_response.success) 

        print("content:", generation_response.content) 

        ai_text = (
            generation_response.content if getattr(generation_response, "success", False) else "unknown error"
        )

        # Persist assistant reply
        self.add_message(
            user_id=0,
            user_name="AI",
            user_type="assistant",
            message=ai_text,
            message_type="text",
        )
        return ai_text

    # ------------------------------------------------------------------ #
    # Core storage methods
    # ------------------------------------------------------------------ #
    
    def add_message(
        self,
        *,
        user_id: int,
        user_name: str,
        user_type: str,
        message: str,
        message_type: str = "text",
        userData: Optional[Dict[str, Any]] = None,
        chatContextNotes: Optional[List[str]] = None,
        coachContext: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ) -> ChatMessage:
        ts = timestamp or datetime.now(timezone.utc)
        msg = ChatMessage(
            user_id=user_id,
            user_name=user_name,
            user_type=user_type,
            id=self._next_id,
            message=message,
            message_type=message_type,
            timestamp=ts,
            userData=userData or {},
            chatContextNotes=chatContextNotes or [],
            coachContext=coachContext or {},
        )
        self._messages.append(msg)
        self._next_id += 1

        self.last_message = msg
        if user_type.lower() == "assistant":
            self.last_ai_message = msg

        # Invalidate caches
        self.get_messages.cache_clear()
        self.get_messages_by_user.cache_clear()

        # Execute hook (if any)
        if self._hook is not None:
            self._hook(self, msg)

        return msg
    
    @lru_cache(maxsize=128)
    def get_messages(self) -> List[ChatMessage]:
        """Return all messages in chronological order."""
        return list(self._messages)

    @lru_cache(maxsize=128)
    def get_messages_by_user(self, user_id: int) -> List[ChatMessage]:
        """Return all messages for a specific user."""
        return [m for m in self._messages if m.user_id == user_id]

    def clear_history(self) -> None:
        """Delete all messages and reset counters."""
        self._messages.clear()
        self._next_id = 1
        self.last_message = None
        self.last_ai_message = None
        self.get_messages.cache_clear()
        self.get_messages_by_user.cache_clear()

    # ------------------------------------------------------------------ #
    # Hooks
    # ------------------------------------------------------------------ #

    def run_custom_logic_after_each_message(
        self, func: Callable[["ChatBackend", ChatMessage], None]
    ) -> None:
        """Replace the current post‑message hook."""
        self._hook = func


# ------------------------------------------------------------------ #
# CLI entry‑point
# ------------------------------------------------------------------ #


def main() -> None:  # pragma: no cover
    """Static demo using a post‑message hook instead of manual calls."""

    backend = ChatBackend()

    # ------------------------------------------------------------------ #
    # Hook: auto‑generate AI reply when a user speaks
    # ------------------------------------------------------------------ #

    def autoresponder(bk: ChatBackend, msg: ChatMessage) -> None:
        if msg.user_type.lower() == "user":
            ai_text = bk.produce_ai_response()
            print(f"User: {msg.message}         AI: {ai_text}")

    backend.run_custom_logic_after_each_message(autoresponder)

    # ------------------------------------------------------------------ #
    # Feed static prompts — hook will handle replies & printing
    # ------------------------------------------------------------------ #
    
    static_messages = [
        "Hello there!",
        "Can you briefly explain what this backend does?",
        "What exactly can you provide help with?",
    ]

    for prompt in static_messages:
        backend.add_message(
            user_id=1,
            user_name="User",
            user_type="user",
            message=prompt,
        )


if __name__ == "__main__":
    main()
