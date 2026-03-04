from services.react_agent import ReactAgent


async def run_agent(filepath):
    agent = ReactAgent(filepath)
    return await agent.run()
