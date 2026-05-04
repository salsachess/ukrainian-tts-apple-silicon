const { client } = require("@gradio/client");

async function testPredict() {
    try {
        const c2 = await client("patriotyk/ukrainian-accentor-transformer");
        const result = await c2.predict("/predict", ["Привіт світ"]);
        console.log("Predict result:", result.data);
    } catch(e) {
        console.error("Predict error:", e);
    }
}

testPredict();
