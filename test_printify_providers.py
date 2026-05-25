from agents.printify_helper import printify_get

BLUEPRINT_ID = 12

providers = printify_get(f"/catalog/blueprints/{BLUEPRINT_ID}/print_providers.json")

print(f"Print providers for blueprint {BLUEPRINT_ID}:")
for provider in providers:
    print(provider.get("id"), "-", provider.get("title"))