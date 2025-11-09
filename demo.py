import asyncio
import os
from dotenv import load_dotenv

from agents import Tavily_agent, wiki_agent, arxiv_agent
from langchain_groq import ChatGroq
from langgraph_supervisor import create_supervisor
from langgraph.types import interrupt
from prompts import supervisor_prompt

# ---------------------------------------------------------------------
# Load environment and model
# ---------------------------------------------------------------------
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

llm = ChatGroq(api_key=groq_api_key, model="qwen/qwen3-32b", temperature=0)

# ---------------------------------------------------------------------
# Utility: back to supervisor
# ---------------------------------------------------------------------
def transfer_back_to_supervisor(content):
    return content

# ---------------------------------------------------------------------
# Pre-model Hook — simple and fast
# ---------------------------------------------------------------------
def pre_model_hook(state):
    """Decide which agent should handle the query and trim history."""
    messages = state.get("messages", [])
    if not messages:
        return state

    query = messages[-1].content.lower()

    # Simple keyword-based routing
    if any(k in query for k in ["latest", "breaking", "today"]):
        state["handoff_to"] = "tavily_agent"
    elif any(k in query for k in ["history", "biography", "define", "who", "what"]):
        state["handoff_to"] = "wiki_agent"
    elif any(k in query for k in ["research", "paper", "study", "arxiv"]):
        state["handoff_to"] = "arxiv_agent"
    else:
        state["handoff_to"] = None

    # Keep only last few messages for speed
    state["messages"] = state["messages"][-5:]
    return state

# ---------------------------------------------------------------------
# Post-model Hook — simple attribution & uncertainty check
# ---------------------------------------------------------------------
def post_model_hook(state):
    """Add attribution and trigger human review if uncertain."""
    last_msg = state["messages"][-1]
    content = last_msg.content.lower()

    # If output looks uncertain → human review
    if any(word in content for word in ["not sure", "maybe", "uncertain", "i think"]):
        print("⚠️ Human review required.")
        return interrupt("Awaiting human approval.")

    # Otherwise just append attribution
    last_msg.content += "\n\n(Source: Tavily, Wikipedia, or Arxiv)"
    state["messages"][-1] = last_msg
    return state

# ---------------------------------------------------------------------
# Create Supervisor
# ---------------------------------------------------------------------
workflow = create_supervisor(
    agents=[Tavily_agent, wiki_agent, arxiv_agent],
    model=llm,
    prompt=supervisor_prompt,
    output_mode="full_history",
    pre_model_hook=pre_model_hook,
    post_model_hook=post_model_hook,
)

app = workflow.compile(name="simple_supervisor")

# ---------------------------------------------------------------------
# Async Runner
# ---------------------------------------------------------------------
async def run_agent():
    print("Multi-Agent Research System\n(Type 'exit' to quit)\n")

    while True:
        query = input("Ask me anything: ")
        if query.lower() == "exit":
            print("👋 Goodbye!")
            break

        try:
            result = app.invoke({
            "messages": [
                {
                    "role": "user",
                    "content": query
                }
            ],
            "tools":["transfer_back_to_supervisor"],
            "max_tokens": 1000
            })
            for m in result['messages']:
                m.pretty_print()

        except Exception as e:
            if "Awaiting human approval" in str(e):
                print("\n🚨 Model paused for human review.")
                human_text = input("Enter approved or corrected response: ")
                result = await app.ainvoke({
                    "messages": [{"role": "user", "content": human_text}],
                    "tools": ["transfer_back_to_supervisor"],
                })
                msgs = result.get("messages", [])
                if msgs:
                    print("\n🧠 Final (Human-Reviewed) Answer:\n")
                    print(msgs[-1].content if hasattr(msgs[-1], "content") else msgs[-1]["content"])
            else:
                raise

# ---------------------------------------------------------------------
#  Entry Point
# ---------------------------------------------------------------------
if __name__ == "__main__":
    asyncio.run(run_agent())
