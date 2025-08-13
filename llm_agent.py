from langchain_openai import ChatOpenAI

def get_llm_response(prompt: str, code_only: bool = False) -> str:
    """
    Queries the local Ollama LLM and returns a structured, controlled response.
    
    Parameters:
    - prompt: user input string.
    - code_only: if True, return only raw code (no markdown or explanations).
    
    Returns:
    - str: LLM's output (cleaned).
    """
    try:
        # System instructions tailored for agent obedience
        if code_only:
            system_instruction = (
                "Respond with code only. No markdown, no triple backticks, no explanations. "
                "Only output raw code. Assume the user needs ready-to-run scripts."
            )
        else:
            system_instruction = (
                "You are  Linux agent Developed by Team Singularity. Do NOT use tool names like `wifi_status()` â€” "
                "use tool names exactly like `wifi_status`. Do not use parentheses for tool calls.\n"
                "When answering, think step-by-step. Be precise and strict with tool syntax.\n"
                "When user asks for code, generate only whatâ€™️s necessary. Avoid assumptions.\n"
                "Stay in character: you are a powerful assistant, not a chatbot. Keep answers professional."
            )
        # Initialize LLM with custom behavior
        llm = ChatOpenAI(
            model="openai/gpt-oss-20b:free",
            temperature=0.4,
            openai_api_key= "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",
            openai_api_base="https://openrouter.ai/api/v1",
            #system=system_instruction
        )
        # Make the request
        response = llm.invoke(prompt.strip())

        return response.content.strip()

    except Exception as e:
        return f"Failed to contact LLM: {e}"
