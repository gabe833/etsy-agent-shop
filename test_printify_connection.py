from agents.printify_helper import printify_get

shops = printify_get("/shops.json")

print("Your Printify shops:")
for shop in shops:
    print("---")
    print("Shop ID:", shop.get("id"))
    print("Title:", shop.get("title"))
    print("Sales Channel:", shop.get("sales_channel"))