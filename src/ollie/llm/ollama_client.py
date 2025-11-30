import ollama
from typing import Generator, List, Dict, Any

class OllamaClient:
    def __init__(self, model: str = "llama3.1:8b", host: str = "http://localhost:11434"):
        """
        Initialize the Ollama client.
        
        Args:
            model: Name of the model to use
            host: URL of the Ollama instance
        """
        self.client = ollama.Client(host=host)
        self.model = model

    def generate_response(
        self, 
        prompt: str, 
        context: List[Dict[str, str]] = None, 
        system_prompt: str = None
    ) -> Generator[str, None, None]:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: User query
            context: History of conversation (list of messages)
            system_prompt: System instruction
            
        Returns:
            Generator yielding response chunks
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
            
        if context:
            messages.extend(context)
            
        messages.append({"role": "user", "content": prompt})

        stream = self.client.chat(
            model=self.model,
            messages=messages,
            stream=True,
        )

        for chunk in stream:
            yield chunk['message']['content']

    def check_connection(self) -> bool:
        """Check if Ollama is reachable."""
        try:
            self.client.list()
            return True
        except Exception:
            return False

