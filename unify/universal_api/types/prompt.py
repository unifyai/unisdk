from typing import Optional


class Prompt:

    def __init__(
        self,
        user_message: Optional[str] = None,
        system_message: Optional[str] = None,
        **kwargs,
    ):
        """
        Create Prompt instance.

        Args:
            user_message: The user message, optional.

            system_message: The system message, optional.

            kwargs: All fields expressed in the pydantic type.

        Returns:
            The pydantic Prompt instance.
        """
        if "messages" not in kwargs:
            kwargs["messages"] = list()
        if system_message:
            kwargs["messages"] = [
                {"content": system_message, "role": "system"},
            ] + kwargs["messages"]
        if user_message:
            kwargs["messages"] += [{"content": user_message, "role": "user"}]
        if not kwargs["messages"]:
            kwargs["messages"] = None
        self.kwargs = kwargs
