import httpx

from openai import OpenAI
from typing import Literal
from collections.abc import Callable, Generator
from message.code import Code
from twisted.plugins.twisted_reactors import asyncio
from pathlib import Path
from jinja2 import Template
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import AgentCard

dir_path = Path(__file__).parent

with Path(dir_path / 'decide.jinja').open('r', encoding='utf-8') as f:
    decide_template = Template(f.read())

with Path(dir_path / 'agent_answer.jinja').open('r', encoding='utf-8') as f:
    agent_answer_template = Template(f.read())

def llm_chat(base_url,apikey,name,message,prompt,mode) -> str | None:
    client = OpenAI(base_url=base_url, api_key=apikey)
    response = client.chat.completions.create(
        model=name,
        messages=[
            {"role": "user", "content": message},
            {"role": "system", "content": prompt}
        ],
        stream=(mode == 'stream')
    )
    return response.choices[0].message.content

class Agent:
    def __init__(
            self,
            mode :Literal['complete','stream'] = 'stream',
            token_stream_callback: Callable[[str], None] | None = None,
            agent_urls: list[str] | None = None,
    ):
        self.mode = mode
        self.token_stream_callback = token_stream_callback
        self.agent_urls = agent_urls
        self.agents_registry: dict[str, AgentCard] = {}

    async def get_agents(self) -> dict[str, AgentCard]:
        """
        从所有代理 URL 检索agent_card并返回信息
        :return: agent_card信息
        """
        async with httpx.AsyncClient() as httpx_client:
            card_resolvers = [
                A2ACardResolver(httpx_client,url) for url in self.agent_urls
            ]
            agent_cards = await asyncio.gather(
                *[
                    card_resolver.get_agent_card()
                    for card_resolver in card_resolvers
                ]
            )
            agents_registry = {
                agent_card.name: agent_card for agent_card in agent_cards
            }
            return agents_registry

    def call_llm(
            self,
            base_url: str,
            apikey: str,
            name: str,
            message: str,
            prompt: str,
    ) -> str | Generator[str, None] | None:
        """
        根据prompt调用远程模型
        :param base_url: 访问地址 比如 https://api.deepseek.com
        :param apikey: api密钥 比如 sk-xxxx
        :param name: 模型名称 比如 gpt-3.5-turbo，deepseek-chat
        :param message: 用户输入
        :param prompt: 系统提示词
        :return: 返回结果
        """
        if self.mode == 'complete':
            response = llm_chat(base_url,apikey,name,message,prompt,self.mode)
            return response
        elif self.mode == 'stream':
            response = llm_chat(base_url,apikey,name,message,prompt,self.mode)
            if response is None:
                return None
            for token in response.split():
                if self.token_stream_callback:
                    self.token_stream_callback(token + ' ')
                yield token + ' '
        else:
            raise Code(500, '不支持的模式').json()

    async def decide(
            self,
            question: str,
            agents_prompt: str,
            called_agents: list[dict] | None = None,
    ) -> Generator[str,None]:
        """
        决策调用哪个模型
        :param question: 用户问题
        :param agents_prompt: 系统提示词
        :param called_agents: 已调用的模型列表
        :return: 返回结果
        """
        if called_agents:
            call_agent_prompt = agent_answer_template.render(
                called_agents=called_agents
            )
        else:
            call_agent_prompt = " "
        prompt = decide_template.render(
            question=question,
            agents_prompt=agents_prompt,
            call_agent_prompt=call_agent_prompt,
        )
        response = self.call_llm(
            base_url="https://api.deepseek.com",
            apikey="sk-xxxx",
            name="deepseek-chat",
            message=question,
            prompt=prompt,
        )
        if response is None:
            yield "抱歉，无法获取决策结果。"
            return
        if isinstance(response, str):
            yield response

if __name__ == "__main__":
    import asyncio

    async def main():
        agent = Agent(
            mode='stream',
            token_stream_callback=lambda token: print(token, end='', flush=True),
            agent_urls=[
                "http://localhost:8000",
                "http://localhost:8001",
            ],
        )
        agents = await agent.get_agents()
        print(agents)

    asyncio.run(main())