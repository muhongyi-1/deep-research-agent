
import argparse
import asyncio

from dotenv import load_dotenv

from app.workflow import run_research


load_dotenv()


async def main():

    parser = argparse.ArgumentParser(
        description="Deep Research Agent"
    )

    # 是否忽略历史检查点重新研究
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="删除对应问题的检查点，重新执行研究",
    )

    args = parser.parse_args()

    print("\n========== Deep Research Agent ==========\n")

    query = input(
        "请输入你的研究问题：\n"
    ).strip()

    if not query:
        print("研究问题不能为空")
        return

    report = await run_research(
        query=query,
        force_new=args.fresh,
    )

    print(
        "\n========== Final Result ==========\n"
    )

    print(report)


if __name__ == "__main__":
    asyncio.run(main())
