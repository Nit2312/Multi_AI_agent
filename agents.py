from langgraph_supervisor import create_supervisor
from langgraph.prebuilt import create_react_agent

from langchain_tavily import TavilySearch
from langchain_community.tools import ArxivQueryRun, WikipediaQueryRun
from langchain_community.utilities import ArxivAPIWrapper, WikipediaAPIWrapper
from langchain_groq import ChatGroq
from dotenv import load_dotenv
load_dotenv()
import os

groq_api_key = os.getenv("GROQ_API_KEY")
os.environ["TAVILY_API_KEY"]=os.getenv('TAVILY_API_KEY')

llm = ChatGroq(api_key=groq_api_key, model="qwen/qwen3-32b", temperature=0)
llm


#------------------------ Tools ------------------------

tavily = TavilySearch()

api_wrapper_arxiv=ArxivAPIWrapper(top_k_results=2, doc_content_chars_max=500)
arxiv = ArxivQueryRun(api_wrapper=api_wrapper_arxiv, description="Query arxiv papers")

api_wrapper_wikipedia = WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=500)
wiki = WikipediaQueryRun(api_wrapper=api_wrapper_wikipedia)

#------------------------ Agents ------------------------

Tavily_agent = create_react_agent(
    model = llm,
    tools = [tavily],
    name = "Tavily Agent",
    prompt= "You are a helpful AI agent that uses Tavily to answer user queries related to recent events and web searches."
)

wiki_agent = create_react_agent(
    model = llm,
    tools = [wiki],
    name = "Wikipedia Agent",
    prompt= "You are a helpful AI agent that uses Wikipedia to answer user queries related to general knowledge."
)

arxiv_agent = create_react_agent(
    model = llm,
    tools = [arxiv],
    name = "Arxiv Agent",
    prompt= "You are a helpful AI agent that uses Arxiv to answer user queries related to scientific research papers."
)