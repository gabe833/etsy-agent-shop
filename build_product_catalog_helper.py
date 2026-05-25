from agents.printify_helper import printify_get


def show_blueprints():
    blueprints = printify_get("/catalog/blueprints.json")

    print("\nPrintify Blueprints:")
    print("-------------------")

    for item in blueprints:
        title = item.get("title", "")
        brand = item.get("brand", "")
        blueprint_id = item.get("id")

        keywords = ["shirt", "sweatshirt", "mug", "tote", "bag"]

        if any(keyword in title.lower() for keyword in keywords):
            print(f"{blueprint_id} | {title} | {brand}")


def show_providers(blueprint_id):
    providers = printify_get(f"/catalog/blueprints/{blueprint_id}/print_providers.json")

    print(f"\nProviders for blueprint {blueprint_id}:")
    print("--------------------------------------")

    for provider in providers:
        print(f"{provider.get('id')} | {provider.get('title')}")


def show_variants(blueprint_id, provider_id):
    data = printify_get(
        f"/catalog/blueprints/{blueprint_id}/print_providers/{provider_id}/variants.json"
    )

    print(f"\nVariants for blueprint {blueprint_id}, provider {provider_id}:")
    print("------------------------------------------------------------")

    for variant in data.get("variants", []):
        variant_id = variant.get("id")
        title = variant.get("title")
        options = variant.get("options")
        enabled = variant.get("is_enabled")

        print(f"{variant_id} | {title} | {options} | Enabled: {enabled}")


def main():
    print("Choose an option:")
    print("1. Show useful blueprints")
    print("2. Show providers for a blueprint")
    print("3. Show variants for a blueprint/provider")

    choice = input("\nEnter 1, 2, or 3: ").strip()

    if choice == "1":
        show_blueprints()

    elif choice == "2":
        blueprint_id = input("Enter blueprint ID: ").strip()
        show_providers(blueprint_id)

    elif choice == "3":
        blueprint_id = input("Enter blueprint ID: ").strip()
        provider_id = input("Enter provider ID: ").strip()
        show_variants(blueprint_id, provider_id)

    else:
        print("Invalid choice.")


if __name__ == "__main__":
    main()