from agents.printify_helper import printify_get

blueprints = printify_get("/catalog/blueprints.json")

print("First 20 Printify blueprints:")
for item in blueprints[:20]:
    print(item.get("id"), "-", item.get("title"), "-", item.get("brand"))