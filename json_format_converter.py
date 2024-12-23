import json

# Load the input JSON data
def convert_recipes_to_graph(input_file, output_file):
    with open(input_file, 'r') as f:
        recipes = json.load(f)

    # Initialize nodes and links
    nodes = []
    links = []

    # Create a mapping of item names to node IDs
    item_to_id = {}
    for i, item in enumerate(recipes.keys(), start=1):
        item_to_id[item] = str(item)
        nodes.append({"id": str(item)})

    # Build links based on ingredients
    for item, details in recipes.items():
        current_id = item_to_id[item]
        for ingredient, count in details.get("ingredients", {}).items():
            if ingredient in item_to_id:
                ingredient_id = item_to_id[ingredient]
                label = f"{count}x{details.get('craftedCount', 1)}"
                links.append({
                    "source": ingredient_id,
                    "target": current_id,
                    "weight": count,
                    "label": label
                })

    # Combine nodes and links into the final graph
    graph = {
        "nodes": nodes,
        "links": links
    }

    # Save the graph to the output file
    with open(output_file, 'w') as f:
        json.dump(graph, f, indent=2)

# Specify input and output file paths
input_file = "recipes.json"
output_file = "graph.json"

# Convert recipes to graph
convert_recipes_to_graph(input_file, output_file)

print(f"Graph saved to {output_file}")