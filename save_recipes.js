import fs from 'fs';
import minecraftData from 'minecraft-data';
const mc_version = '1.20.4';
const mcdata = minecraftData(mc_version);

function getItemId(itemName) {
    let item = mcdata.itemsByName[itemName];
    if (item) {
        return item.id;
    }
    return null;
}

function getItemName(itemId) {
    let item = mcdata.items[itemId]
    if (item) {
        return item.name;
    }
    return null;
}

function getAllItems(ignore) {
    if (!ignore) {
        ignore = [];
    }
    let items = []
    for (const itemId in mcdata.items) {
        const item = mcdata.items[itemId];
        if (!ignore.includes(item.name)) {
            items.push(item);
        }
    }
    return items;
}

function getItemCraftingRecipes(itemName) {
    let itemId = getItemId(itemName);
    if (!mcdata.recipes[itemId]) {
        return null;
    }

    let recipes = [];
    for (let r of mcdata.recipes[itemId]) {
        let recipe = {};
        let ingredients = [];
        if (r.ingredients) {
            ingredients = r.ingredients;
        } else if (r.inShape) {
            ingredients = r.inShape.flat();
        }
        for (let ingredient of ingredients) {
            let ingredientName = getItemName(ingredient);
            if (ingredientName === null) continue;
            if (!recipe[ingredientName])
                recipe[ingredientName] = 0;
            recipe[ingredientName]++;
        }
        recipes.push([
            recipe,
            {craftedCount : r.result.count}
        ]);
    }

    return recipes;
}


function saveRecipesToFile(fileName) {
    const allItems = getAllItems();
    const recipes = {};

    for (const item of allItems) {
        const itemRecipes = getItemCraftingRecipes(item.name);

        if (itemRecipes && itemRecipes.length > 0) {
            // Use the first recipe (if multiple exist) as the main one
            const mainRecipe = itemRecipes[0];
            recipes[item.name] = {
                ingredients: mainRecipe[0], // Ingredients object
                craftedCount: mainRecipe[1].craftedCount,
                hasImage: true,
            };
        } else {
            // Base item case
            recipes[item.name] = {
                ingredients: {}, // No ingredients
                craftedCount: 0,
                hasImage: true,
                isBaseItem: true, // Mark as a base item
            };
        }
    }

    fs.writeFile(fileName, JSON.stringify(recipes, null, 2), (err) => {
        if (err) {
            console.error('Error writing recipes to file:', err);
        } else {
            console.log(`Recipes saved successfully to ${fileName}`);
        }
    });
}

// Call the function to save recipes to recipes.json
saveRecipesToFile('recipes.json');
