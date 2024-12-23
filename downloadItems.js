import minecraftData from 'minecraft-data';
import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';

const mcdata = minecraftData('1.20.4');

function getAllItems(ignore = []) {
    let items = [];
    for (const itemId in mcdata.items) {
        const item = mcdata.items[itemId];
        if (!ignore.includes(item.name)) {
            items.push(item);
        }
    }
    return items;
}

function formatWikiName(name) {
    return name.split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join('_');
}

async function downloadAllItemImages() {
    const items = getAllItems();
    const totalItems = items.length;
    const outputDir = './minecraft_item_images';
    
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir);
    }
    
    console.log(`Starting download of ${totalItems} items...`);

    // Launch browser
    const browser = await puppeteer.launch({
        headless: false, // Set to true for production
        defaultViewport: null
    });
    
    const page = await browser.newPage();
    let processedCount = 0;

    // Set up response interceptor to save images
    page.on('response', async response => {
        const url = response.url();
        if (url.includes('Invicon_') && url.endsWith('.png')) {
            try {
                const buffer = await response.buffer();
                const itemName = url.split('Invicon_')[1].split('.png')[0];
                const originalName = items.find(item => 
                    formatWikiName(item.name) === itemName
                )?.name;
                
                if (originalName) {
                    const filepath = path.join(outputDir, `${originalName}.png`);
                    if (!fs.existsSync(filepath)) {
                        fs.writeFileSync(filepath, buffer);
                    }
                }
            } catch (error) {
                console.error(`Failed to save image: ${error.message}`);
            }
        }
    });

    // Process each item
    for (const item of items) {
        try {
            const wikiName = formatWikiName(item.name);
            const filepath = path.join(outputDir, `${item.name}.png`);

            if (fs.existsSync(filepath)) {
                processedCount++;
                const percentage = ((processedCount / totalItems) * 100).toFixed(2);
                process.stdout.write(`\rProcessed ${processedCount}/${totalItems} items (${percentage}%)`);
                continue;
            }

            const url = `https://minecraft.wiki/images/Invicon_${wikiName}.png`;
            
            await page.goto(url, { waitUntil: 'networkidle0' });
            
            // Use setTimeout instead of non-existent waitForTimeout
            await new Promise(resolve => setTimeout(resolve, 10));
        } catch (error) {
            console.error(`Failed to process ${item.name}: ${error.message}`);
        } finally {
            processedCount++;
            const percentage = ((processedCount / totalItems) * 100).toFixed(2);
            process.stdout.write(`\rProcessed ${processedCount}/${totalItems} items (${percentage}%)`);
        }
    }

    await browser.close();
    console.log('\nDownload process completed!');
}

// Run the download process
downloadAllItemImages().catch(console.error);