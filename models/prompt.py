from typing import List, Dict, Any, Optional


class PromptBuilder:
    """A simple builder class for constructing chat-based prompts.

    This class helps build chat prompts as lists of message dictionaries
    with 'role' and 'content' keys, following the OpenAI API format.
    """

    def __init__(self):
        """Initialize the prompt builder with an optional system message.

        Args:
            system_message: Optional initial system message to start the prompt
        """
        self.prompt: List[Dict[str, str]] = []

    def add_system(self, content: str):
        """Add a system message to the prompt.

        Args:
            content: The content of the system message

        Returns:
            self for method chaining
        """
        self.prompt.append({"role": "system", "content": content})

    def add_user(self, content: str):
        """Add a user message to the prompt.

        Args:
            content: The content of the user message

        Returns:
            self for method chaining
        """
        self.prompt.append({"role": "user", "content": content})

    def add_assistant(self, content: str):
        """Add an assistant message to the prompt.

        Args:
            content: The content of the assistant message

        Returns:
            self for method chaining
        """
        self.prompt.append({"role": "assistant", "content": content})

    def extend(self, messages: List[Dict[str, str]]) -> "PromptBuilder":
        """Extend the current prompt with a list of messages.

        Args:
            messages: List of message dictionaries to add

        Returns:
            self for method chaining

        Raises:
            ValueError: If any message is missing 'role' or 'content' keys
        """
        for msg in messages:
            if not all(k in msg for k in ("role", "content")):
                raise ValueError("Each message must have 'role' and 'content' keys")
        self.prompt.extend(messages)
        return self

    def clear(self) -> None:
        """Clear all messages from the prompt."""
        self.prompt = []

    def get(self) -> List[Dict[str, str]]:
        """Get the current prompt as a list of messages.

        Returns:
            List of message dictionaries
        """
        return self.prompt

    def __len__(self) -> int:
        """Return the number of messages in the prompt."""
        return len(self.prompt)

    def __str__(self) -> str:
        """Return a string representation of the prompt."""
        return f"<PromptBuilder with {len(self)} messages>"
