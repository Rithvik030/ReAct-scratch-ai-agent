from Backend.agent import Agent

agent = Agent()

while True:
    query = input("\nAsk something (type 'exit' to quit): ")

    if query.lower() == "exit":
        break

    if not query:
        print("Please enter a valid question.")
        continue

    result = agent.run(query)

    print("\nAgent:", result)