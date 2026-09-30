from ollama import Client


class OllamaClient:
    def __init__(
        self,
        model: str = "qwen2.5:7b-instruct",
        host: str = "http://localhost:11434",
    ) -> None:
        self.model = model
        self.client = Client(host=host)

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        response = self.client.chat(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            format="json",
            options={
                "temperature": 0,
            },
        )

        return response["message"]["content"]
