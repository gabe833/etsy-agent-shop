from agents.printify_helper import printify_get

BLUEPRINT_ID = 12
PRINT_PROVIDER_ID = 29

variants = printify_get(
    f"/catalog/blueprints/{BLUEPRINT_ID}/print_providers/{PRINT_PROVIDER_ID}/variants.json"
)

print("Available variants:")
for variant in variants.get("variants", []):
    print(
        "Variant ID:", variant.get("id"),
        "| Title:", variant.get("title"),
        "| Options:", variant.get("options"),
        "| Enabled:", variant.get("is_enabled")
    )