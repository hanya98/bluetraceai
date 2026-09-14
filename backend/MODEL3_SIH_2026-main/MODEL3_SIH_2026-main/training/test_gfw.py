from gfw_client import search_vessel

result = search_vessel("7831410")

print("API SUCCESS")
print("Total:", result.get("total"))

for vessel in result.get("entries", [])[:3]:
    print(vessel)