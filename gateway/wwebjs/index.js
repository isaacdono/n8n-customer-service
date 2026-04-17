const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const express = require('express');
const axios = require('axios');

const app = express();
app.use(express.json());

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://fastapi-service:8000';
const PORT = process.env.PORT || 3000;

const client = new Client({
    authStrategy: new LocalAuth(), // Saves the session in a .wwebjs_auth/ folder
    puppeteer: { 
        args: ['--no-sandbox', '--disable-setuid-sandbox'] 
    }
});

// Event: Emit QR Code for login
client.on('qr', (qr) => {
    qrcode.generate(qr, { small: true });
    console.log('SCAN THE QR CODE ABOVE TO LOG IN (or check container logs)');
});

// Event: WhatsApp Client Ready
client.on('ready', () => {
    console.log('WhatsApp Client is READY! Listening for messages...');
});

// Event: Receive messages from WhatsApp
client.on('message', async msg => {
    // Ignore internal broadcast statuses
    if (msg.from === 'status@broadcast') return;

    const payload = {
        sender_id: msg.from,
        body: msg.body,
        sender_name: msg._data.notifyName || 'Unknown',
        timestamp: msg.timestamp
    };

    console.log(`[WTS -> API] Sending msg from ${payload.sender_id}: ${payload.body.substring(0, 30)}...`);

    try {
        await axios.post(`${FASTAPI_URL}/webhook/whatsapp`, payload);
    } catch (error) {
        console.error('[Error] Failed to forward message to FastAPI:', error.message);
    }
});

// ======== HTTP SERVER FOR FASTAPI / N8N ========

// Endpoint to send messages out to WhatsApp
app.post('/send', async (req, res) => {
    const { to, message } = req.body;
    
    if (!to || !message) {
        return res.status(400).json({ error: 'Missing "to" or "message" in body' });
    }

    try {
        await client.sendMessage(to, message);
        console.log(`[API -> WTS] Sent msg to ${to}`);
        res.status(200).json({ status: 'sent', to });
    } catch (error) {
        console.error('[Error] Sending message via wwebjs:', error.message);
        res.status(500).json({ error: error.message });
    }
});

client.initialize();
app.listen(PORT, () => {
    console.log(`Node.js WWebJS Gateway internal server listening on port ${PORT}`);
});
