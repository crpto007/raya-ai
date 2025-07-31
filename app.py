from flask import Flask, request
import os
import openai
import requests
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Load environment variables
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "your_verify_token")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN", "your_page_access_token")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your_openai_api_key")

openai.api_key = OPENAI_API_KEY

# ---------------------- Webhook Verification ----------------------
@app.route('/webhook', methods=['GET'])
def verify():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if token == VERIFY_TOKEN:
        return challenge, 200
    else:
        return "Invalid verification token", 403

# ---------------------- Webhook for WhatsApp Messages ----------------------
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print("🔔 Incoming webhook data:", json.dumps(data, indent=2))

    try:
        if data.get("object") == "whatsapp_business_account":
            for entry in data.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    messages = value.get("messages", [])
                    if messages:
                        phone_number_id = value["metadata"]["phone_number_id"]
                        from_number = messages[0]["from"]
                        msg_body = messages[0]["text"]["body"]

                        print(f"📩 Received message from {from_number}: {msg_body}")

                        # AI Response
                        reply = ask_openai(msg_body)

                        # Send back response
                        send_whatsapp_message(phone_number_id, from_number, reply)
        return "ok", 200

    except Exception as e:
        print("❌ Error in webhook:", str(e))
        return "error", 500

# ---------------------- Send Message to WhatsApp ----------------------
def send_whatsapp_message(phone_id, to_number, message):
    url = f"https://graph.facebook.com/v18.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {PAGE_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": message}
    }

    response = requests.post(url, headers=headers, json=payload)
    print(f"📤 Sent to {to_number}: {message}")
    print("✅ WhatsApp API Response:", response.status_code, response.text)

# ---------------------- Get OpenAI Reply ----------------------
def ask_openai(prompt):
    try:
        print("🧠 Asking OpenAI:", prompt)
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        reply = response.choices[0].message['content'].strip()
        return reply
    except Exception as e:
        print("❌ OpenAI Error:", str(e))
        return "Sorry, AI is not available right now. Please try again later."

# ---------------------- Run the Flask App ----------------------
if __name__ == '__main__':
    print("🚀 Flask WhatsApp bot running...")
    app.run(host='0.0.0.0', port=5000)
