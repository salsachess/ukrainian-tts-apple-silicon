const { client } = require("@gradio/client");

async function testSpaces() {
    try {
        console.log("Testing patriotyk/stressifier-byt5-g2p-model...");
        const c1 = await client("patriotyk/stressifier-byt5-g2p-model");
        console.log("Success c1");
    } catch(e) {
        console.error("Error c1:", e.message);
    }
    
    try {
        console.log("Testing patriotyk/ukrainian-accentor-transformer...");
        const c2 = await client("patriotyk/ukrainian-accentor-transformer");
        console.log("Success c2");
    } catch(e) {
        console.error("Error c2:", e.message);
    }
}

testSpaces();
