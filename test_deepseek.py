import asyncio

from agents import Agent, Runner

from app.config import deepseek_model


async def main():

    agent = Agent(
        name="Test Agent",
        model=deepseek_model,
        instructions="你是一个测试助手。",
    )

    result = await Runner.run(
        agent,
        "请回答：1+1等于多少？"
    )

    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())