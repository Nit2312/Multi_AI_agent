from agents import Tavily_agent, wiki_agent, arxiv_agent, llm
from langgraph_supervisor import create_supervisor

def transfer_back_to_supervisor(content):
    # This is the mechanism by which each agent sends its final result to the supervisor
    return content

workflow = create_supervisor(
    [Tavily_agent, wiki_agent, arxiv_agent],
    model=llm,
    prompt=(
        "You are a high-level reasoning and coordination agent. "
        "Your job is to understand the user’s question deeply, reason step-by-step, and delegate "
        "the task to the most appropriate specialized agents: Tavily Agent, Wikipedia Agent, or Arxiv Agent.\n\n"

        "### Capabilities:\n"
        "- **Tavily Agent:** Handles live or recent web data, news, and real-time topics.\n"
        "- **Wikipedia Agent:** Handles general factual or encyclopedic knowledge.\n"
        "- **Arxiv Agent:** Handles scientific and academic paper-related queries.\n\n"

        "### Guidelines:\n"
        "1. First, **analyze the intent** of the user's query and **reason explicitly** about what type of knowledge is required.\n"
        "2. **Select** one or multiple agents accordingly. You may chain them — e.g., use Tavily for current context, then Wikipedia to verify facts.\n"
        "3. If multiple agents are used, **synthesize and summarize** their responses into one coherent, well-structured final answer.\n"
        "4. Use reasoning and verification to ensure factual accuracy.\n"
        "5. If uncertain, explain your reasoning and assumptions clearly.\n\n"

        "### Example Thought Process:\n"
        "- 'What’s the combined employees laid off by FAANG companies in 2025?' → Requires recent data → Use Tavily Agent.\n"
        "- 'Summarize the latest Transformer architecture paper from 2024' → Arxiv Agent.\n"
        "- 'Who is the founder of OpenAI?' → Wikipedia Agent.\n\n"

        "Think step-by-step. Only after reasoning clearly should you decide which agent(s) to delegate to. "
        "After collecting responses, synthesize and return a concise, accurate, and insightful final answer."
        "Your goal is to answer efficiently and avoid recursion, make few calls to agents as possible and provide accurate information."
    ),
    output_mode="full_history"
)

app = workflow.compile(name="supervisor_workflow")


    
def run_agent():
    print("Multi-Source Research Agent")
    print("Type 'exit' to quit\n")
    while True:
        user_input = input("Ask me anything: ")
        if user_input.lower() == "exit":
            print("Bye")
            break
        result = app.invoke({
            "messages": [
                {
                    "role": "user",
                    "content": user_input
                }
            ],
            "tools":["transfer_back_to_supervisor"],
            "max_tokens": 1000
        })
        for m in result['messages']:
            m.pretty_print()
        
    
if __name__ == "__main__":
    run_agent()