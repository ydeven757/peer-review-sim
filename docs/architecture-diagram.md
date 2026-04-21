%%{ init: { "theme": "dark", "themeVariables": {
  "primaryColor": "#1e3a5f",
  "primaryTextColor": "#e2e8f0",
  "primaryBorderColor": "#22d3ee",
  "lineColor": "#64748b",
  "secondaryColor": "#064e3b",
  "tertiaryColor": "#4c1d95"
} } }%%

flowchart TB
    %% ── External actors ───────────────────────────────────────────
    User(["👤 User<br/><small>Browser</small>"])

    subgraph frontend["🔵 FRONTEND"]
        UI["app/main.py<br/><small>Streamlit UI</small>"]
        Input["Paper Input<br/><small>Paste / DOCX / PDF</small>"]
        Config["Config<br/><small>Venue + Personas</small>"]
    end

    subgraph pipeline["🟢 PROCESSING PIPELINE"]
        direction LR

        Loader["app/paper_loader.py<br/><small>python-docx · pdfplumber</small>"]
        Prompts["app/prompts/<br/>system_prompt.py<br/>reviewer_prompts.py<br/>meta_review_prompt.py"]
        ConfigMod["app/config.py<br/><small>VENUES · PERSONAS<br/>DIMENSIONS</small>"]

        subgraph llm["app/llm_client.py"]
            direction TB
            getclient["get_client()<br/><small>provider priority</small>"]
            ollama["Ollama<br/><small>localhost:11434 · llama3</small>"]
            anthropic["Anthropic<br/><small>Claude Sonnet 4</small>"]
            openai["OpenAI<br/><small>GPT-4o · API</small>"]
        end

        ReviewerEngine["app/reviewer_engine.py<br/><small>generate_review()</small>"]
        MetaReview["app/meta_review.py<br/><small>synthesize_meta_review()</small>"]
        AvgScores["compute_average_scores()"]
        Export["app/export/pdf_export.py<br/><small>reportlab · A4 PDF</small>"]
    end

    subgraph llm_providers["🟡 LLM PROVIDERS (auto-detected)"]
        OllamaSvr["🐑 Ollama Server<br/><small>ollama serve · :11434</small>"]
        AnthropicAPI["🤖 Anthropic API<br/><small>api.anthropic.com</small>"]
        OpenAIAPI["🤖 OpenAI API<br/><small>api.openai.com</small>"]
    end

    subgraph outputs["🔵 OUTPUTS"]
        Display["📊 Streamlit UI Display<br/><small>Score cards · Verdicts<br/>Expander reviews · Meta-review</small>"]
        PDF["📄 PDF Report<br/><small>Cover · Scores · Meta-review<br/>Individual Reviews</small>"]
    end

    %% ── Frontend connections ───────────────────────────────────────
    User --> UI
    UI --> Input
    UI --> Config
    Input -->|"paper_text"| Loader
    Config -->|"venue + persona info"| ReviewerEngine
    Config -->|"venue + persona info"| MetaReview

    %% ── Pipeline data flow ─────────────────────────────────────────
    Loader -->|"paper_text"| ReviewerEngine
    ReviewerEngine -->|"ReviewResult[]"| MetaReview
    ReviewerEngine -->|"ReviewResult[]"| AvgScores
    MetaReview -->|"meta_review dict"| Export
    AvgScores -->|"avg_scores dict"| Export
    Prompts -->|"prompt strings"| ReviewerEngine
    Prompts -->|"prompt strings"| MetaReview

    %% ── LLM calls ─────────────────────────────────────────────────
    ReviewerEngine -.->|"complete(prompt)"| getclient
    MetaReview -.->|"complete(prompt)"| getclient
    getclient -.->|"priority: Ollama → Anthropic → OpenAI"| ollama
    getclient -.-> anthropic
    getclient -.-> openai

    ollama -.-> OllamaSvr
    anthropic -.-> AnthropicAPI
    openai -.-> OpenAIAPI

    %% ── Output connections ─────────────────────────────────────────
    ReviewerEngine -->|"results"| Display
    MetaReview -->|"meta_review"| Display
    Export -->|"PDF file"| PDF
    PDF -->|"st.download_button"| Display

    %% ── Style classes ─────────────────────────────────────────────
    classDef frontendBox fill:#0e3a4a,stroke:#22d3ee,stroke-width:2px
    classDef pipelineBox fill:#064e3b,stroke:#34d399,stroke-width:2px
    classDef llmBox fill:#312e81,stroke:#a78bfa,stroke-width:2px
    classDef providerBox fill:#451a03,stroke:#fbbf24,stroke-width:2px
    classDef outputBox fill:#0e3a4a,stroke:#22d3ee,stroke-width:2px
    classDef arrowData stroke:#34d399,stroke-width:2px
    classDef arrowLLM stroke:#fbbf24,stroke-width:1.5px,stroke-dasharray:5,5
    classDef arrowConfig stroke:#fbbf24,stroke-width:1px,stroke-dasharray:3,3

    class UI,Input,Config frontendBox
    class Loader,ReviewerEngine,MetaReview,AvgScores,Export,llm pipelineBox
    class Prompts,ConfigMod llmBox
    class OllamaSvr,AnthropicAPI,OpenAIAPI providerBox
    class Display,PDF outputBox
