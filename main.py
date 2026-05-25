import sys

from agents.research_agent import run_research_agent
from agents.product_agent import run_product_agent
from agents.listing_agent import run_listing_agent
from agents.compliance_agent import run_compliance_agent
from agents.design_agent import run_design_agent
from agents.design_review_agent import run_design_review_agent
from agents.printify_agent import run_printify_agent
from agents.catalog_builder_agent import run_catalog_builder_agent


def print_commands():
    print("Please choose a command.")
    print("Available commands:")
    print("  catalog")
    print("  research")
    print("  product")
    print("  listing")
    print("  compliance")
    print("  design")
    print("  design_review")
    print("  printify")
    print("  pipeline")
    print("  product_pipeline")


def main():
    if len(sys.argv) < 2:
        print_commands()
        return

    command = sys.argv[1]

    if command == "catalog":
        run_catalog_builder_agent()

    elif command == "research":
        run_research_agent()

    elif command == "product":
        run_product_agent()

    elif command == "listing":
        run_listing_agent()

    elif command == "compliance":
        run_compliance_agent()

    elif command == "design":
        run_design_agent()

    elif command == "design_review":
        run_design_review_agent()

    elif command == "printify":
        run_printify_agent()

    elif command == "pipeline":
        run_catalog_builder_agent()
        run_research_agent()
        run_product_agent()
        run_listing_agent()
        run_compliance_agent()

    elif command == "product_pipeline":
        run_design_agent()
        run_design_review_agent()
        run_printify_agent()

    else:
        print(f"Unknown command: {command}")
        print_commands()


if __name__ == "__main__":
    main()