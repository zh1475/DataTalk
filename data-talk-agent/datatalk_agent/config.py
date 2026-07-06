# Configuration settings for the DataTalk Business Data Analysis Agent

# The model to use for all LLM decisions and reports
MODEL_NAME = "gemini-3.1-flash-lite"

# Word threshold for question specificity
MIN_WORDS = 5

# Vague questions that should instantly trigger a clarification request
VAGUE_PHRASES = {
    "analyze this",
    "tell me something",
    "help",
    "do analysis",
    "run",
    "start",
    "go",
    "analyze the data",
    "tell me about this",
    "what is this",
    "what does it show",
}
