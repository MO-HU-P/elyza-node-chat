const express = require("express");
const axios = require("axios");
const path = require("path");

const app = express();
const PORT = 3000;

// リクエストのログ記録
app.use((req, res, next) => {
    console.log(`${new Date().toISOString()} ${req.method} ${req.url}`);
    next();
});

app.use(express.static(path.join(__dirname, "public")));
app.use(express.json());

app.post("/api/send-message", async (req, res) => {
    console.log("Received message:", req.body.message); // デバッグログ

    try {
        const response = await axios.post("http://localhost:8501/api/chat", {
            message: req.body.message
        }, {
            headers: {
                'Content-Type': 'application/json'
            }
        });

        console.log("Response from Python backend:", response.data); // デバッグログ
        res.json(response.data);

    } catch (error) {
        console.error("Error details:", {
            message: error.message,
            code: error.code,
            response: error.response?.data
        });
        
        if (error.code === 'ECONNREFUSED') {
            res.status(503).json({ error: "Python バックエンドに接続できません。" });
        } else {
            res.status(500).json({ error: "エラーが発生しました。" });
        }
    }
});

app.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}`);
});