from typing import List, Dict, Optional
from openai import OpenAI

class PolishArtExpertRAG:
    def __init__(
        self,
        rag_system,
        openai_api_key: str,
        model: str = "gpt-4o-mini",
        max_context_length: int = 40000
    ):
        self.rag_system = rag_system
        self.client = OpenAI(api_key=openai_api_key)
        self.model = model
        self.max_context_length = max_context_length

        self.base_system_prompt = (
            "Jesteś ekspertem w dziedzinie sztuki, który zawsze odpowiada w języku polskim. \n"
            "Korzystaj z dostarczonych fragmentów kontekstu, aby udzielić dokładnej odpowiedzi.\n"
            "Jeśli informacja nie znajduje się w kontekście, bazuj na swojej wiedzy ogólnej.\n"
            "Zawsze zachowuj przyjazny i profesjonalny ton wypowiedzi.\n\n"
            "Ważne zasady:\n"
            "1. Odpowiadaj tylko po polsku\n"
            "2. Zachowaj spójność i płynność wypowiedzi\n"
            "3. Obecnym dziekanem Wydziału Sztuki Mediów jest dr Piotr Kucia\n"
            "4. Jesteśmy na wystawie z okazji piętnastolecia Wydziału Sztuki Mediów, która odbywa się w Pałacu Czapskich Krakowskie Przedmieście 5 Galeria -1\n"
            "5. Wystawa trwa od 28 lutego 2025 do 27 marca 2025"
            "6. Nie wspominaj bezpośrednio o kontekście\n"
            "7. Dzisiaj jest 28.02.2025\n"
            "8. Nazywasz się Art Chat"
        )

    def _prepare_context(self, query: str, num_results: int = 3, token_limit: int = 10000) -> (str, list):
        # initial_results = self.rag_system.search(query=query, top_k=5, include_metadata=True)
        # Rerank these results using the cross-encoder
        reranked_results = self.rag_system.search(query=query, top_k=3)  # self.rag_system.rerank(query, initial_results, top_k=num_results)

        fragments = []
        context_parts = []
        for i, result in enumerate(reranked_results, 1):
            filename = result.get('metadata', {}).get('filename', 'Brak źródła')
            fragment = (
                f"Fragment {i} (Źródło: {filename}):\n"
                f"{result['text']}\n"
            )
            context_parts.append(fragment)
            fragments.append(fragment)
        full_context = "\n".join(context_parts)

        # A very simple tokenization based on whitespace:
        tokens = full_context.split()
        truncated_context = " ".join(tokens[:token_limit]) if len(tokens) > token_limit else full_context

        return truncated_context, fragments

    def get_response(self, user_query: str, conversation_history: Optional[List[Dict]] = None, temperature: float = 0.7) -> dict:
        """
        Zwraca słownik zawierający:
          - "assistant_response": odpowiedź modelu
          - "fragments": lista fragmentów pobranych z FAISS
        """
        truncated_context, fragments = self._prepare_context(user_query, num_results=3, token_limit=16000)
        print(truncated_context)
        messages = [
            {
                "role": "system",
                "content": self.base_system_prompt
            }
        ]
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({
            "role": "user",
            "content": f"{user_query}\n\nKONTEKST:\n{truncated_context}"
        })
        print(messages)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=16000
            )
            assistant_response = response.choices[0].message.content
        except Exception as e:
            assistant_response = f"Przepraszamy, wystąpił błąd: {str(e)}"

        return {"assistant_response": assistant_response, "fragments": fragments}