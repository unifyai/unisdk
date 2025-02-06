class Prompt:
    def __init__(
        self,
        **components,
    ):
        """
        Create Prompt instance.

        Args:
            components: All components of the prompt.

        Returns:
            The Prompt instance.
        """
        self.components = components
