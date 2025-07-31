from flask import Flask, request
import os
import openai
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

# ---------------------- Webhook verification ----------------------
@app.route('/webhook', methods=['GET'])
def verify():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if token == VERIFY_TOKEN:
        return challenge, 200
    else:
        return "Invalid verification token", 403

# ---------------------- Handle Messages ----------------------
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()

    if data.get("object") == "whatsapp_business_account":
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])
                if messages:
                    phone_number_id = value["metadata"]["phone_number_id"]
                    from_number = messages[0]["from"]
                    msg_body = messages[0]["text"]["body"]

                    # 🧠 AI Response
                    reply = ask_openai(msg_body)

                    # 📤 Send back reply
                    send_whatsapp_message(phone_number_id, from_number, reply)

    return "ok", 200

# ---------------------- Send Message Function ----------------------
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
    requests.post(url, headers=headers, json=payload)

# ---------------------- OpenAI Response Function ----------------------
def ask_openai(prompt):
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return completion.choices[0].message['content'].strip()
    except Exception as e:
        return "Sorry, AI is busy. Please try again later."

if __name__ == '__main__':
    app.run()
