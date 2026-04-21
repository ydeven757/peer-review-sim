#!/bin/bash
# Run the Peer Review Simulator Streamlit app

cd "$(dirname "$0")"

# Set PYTHONPATH so 'app' module resolves correctly
export PYTHONPATH="$(pwd)"

# Check for API key
if [[ -z "$ANTHROPIC_API_KEY" && -z "$OPENAI_API_KEY" ]]; then
    echo "WARNING: No ANTHROPIC_API_KEY or OPENAI_API_KEY set."
    echo "The app will fail to generate reviews without an API key."
    echo ""
    echo "To set your API key:"
    echo "  export ANTHROPIC_API_KEY='your-key-here'"
    echo "  # OR"
    echo "  export OPENAI_API_KEY='your-key-here'"
    echo ""
fi

echo "Starting Peer Review Simulator..."
echo "Open http://localhost:8501 in your browser"
echo ""

streamlit run app/main.py --server.headless true --browser.gatherUsageStats false
