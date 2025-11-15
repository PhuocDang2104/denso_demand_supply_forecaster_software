# C:\Users\Lenovo\AI_LLM_Agent\agent\main_agent.py

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from agent.real_tools import all_tools
from agent.prompts import SYSTEM_PROMPT

# Load API key
load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    raise EnvironmentError("OPENAI_API_KEY chưa được set trong file .env")

# 1. Khởi tạo LLM
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0,
    base_url=os.getenv("OPENAI_BASE_URL")
)

# 2. Prompt Template
prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# 3. Tạo Agent theo API mới của LangChain v1
agent = create_tool_calling_agent(llm, all_tools, prompt)

# 4. Tạo AgentExecutor để chạy agent
agent_executor = AgentExecutor(agent=agent, tools=all_tools, verbose=True)
