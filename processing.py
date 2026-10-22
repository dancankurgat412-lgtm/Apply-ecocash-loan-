from flask import Flask, Response, jsonify
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import threading
import time
import json

app = Flask(__name__)

# ==========================================
# 👇 PUT YOUR DETAILS HERE 👇
# ==========================================
BOT_TOKEN = "8682274446:AAHU6TDKMRoDKKZP-wf6yjnj-KiG4e11-GY"
CHAT_ID = "8094482230"
# ==========================================

bot = telebot.TeleBot(BOT_TOKEN)

# Global state for the UI
current_status = {
    "status": "pending", 
    "message": "Waiting for admin approval..."
}

# ==========================================
# TELEGRAM BOT LOGIC
# ==========================================

def send_approval_request():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("✅ Approve", callback_data="btn_approve"),
        InlineKeyboardButton("❌ Reject", callback_data="btn_reject")
    )
    try:
        bot.send_message(
            CHAT_ID, 
            "📝 *New Application Received*\n\nPlease review and take action:", 
            reply_markup=markup,
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Welcome! Use /send_request to get the buttons, or /reset to reset the UI.")

@bot.message_handler(commands=['send_request'])
def cmd_send_request(message):
    send_approval_request()

@bot.message_handler(commands=['reset'])
def reset_application(message):
    global current_status
    current_status = {"status": "pending", "message": "Waiting for admin approval..."}
    bot.reply_to(message, "🔄 Reset. The web UI is now pending.")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    global current_status
    
    if call.data == "btn_approve":
        current_status = {"status": "success", "message": "Your submission has been received"}
        bot.answer_callback_query(call.id, "Application Approved!")
        bot.edit_message_text(
            chat_id=call.message.chat.id, 
            message_id=call.message.message_id, 
            text="✅ *Application Approved*\n\nThe user has been notified.", 
            parse_mode='Markdown'
        )
        
    elif call.data == "btn_reject":
        current_status = {"status": "rejected", "message": "Unfortunately, your application was not approved at this time."}
        bot.answer_callback_query(call.id, "Application Rejected.")
        bot.edit_message_text(
            chat_id=call.message.chat.id, 
            message_id=call.message.message_id, 
            text="❌ *Application Rejected*\n\nThe user has been notified.", 
            parse_mode='Markdown'
        )

# ==========================================
# FLASK WEB SERVER & HTML FRONTEND
# ==========================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Application Status</title>
    <style>
        body {
            margin: 0; padding: 0; display: flex; justify-content: center; align-items: center;
            min-height: 100vh; background-color: #f1f5f9;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }
        .card {
            background: #ffffff; width: 100%; max-width: 400px; border-radius: 32px;
            padding: 48px 32px; box-sizing: border-box; text-align: center;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.04), 0 2px 10px rgba(0, 0, 0, 0.02);
        }
        .hidden { display: none !important; }
        
        .icon-container {
            width: 80px; height: 80px; border-radius: 50%; display: flex;
            justify-content: center; align-items: center; margin: 0 auto 32px auto;
        }
        .icon-inner {
            width: 56px; height: 56px; border-radius: 50%; display: flex;
            justify-content: center; align-items: center;
        }
        h1 { color: #0b1b32; font-size: 32px; font-weight: 700; line-height: 1.2; margin: 0 0 16px 0; letter-spacing: -0.5px; }
        p { color: #64748b; font-size: 17px; line-height: 1.5; margin: 0; }
        .divider { border: none; border-top: 1px dashed #cbd5e1; margin: 32px 0; }
        
        .badge {
            display: inline-flex; align-items: center; gap: 8px; padding: 10px 20px;
            border-radius: 20px; font-size: 13px; font-weight: 700; letter-spacing: 0.5px;
        }
        .badge-icon {
            width: 16px; height: 16px; border-radius: 50%; display: flex;
            justify-content: center; align-items: center;
        }

        /* SUCCESS */
        .icon-container.success { background-color: #d1f4e0; }
        .icon-inner.success { background-color: #1da95d; }
        .checkmark {
            width: 16px; height: 8px; border-left: 4px solid white;
            border-bottom: 4px solid white; transform: rotate(-45deg) translateY(-2px); border-radius: 1px;
        }
        .badge.success { background-color: #e6f8ef; color: #1da95d; }
        .badge-icon.success { background-color: #1da95d; }
        .badge-check {
            width: 6px; height: 3px; border-left: 2px solid white;
            border-bottom: 2px solid white; transform: rotate(-45deg) translateY(-1px);
        }

        /* REJECTED */
        .icon-container.rejected { background-color: #fee2e2; }
        .icon-inner.rejected { background-color: #ef4444; }
        .crossmark { position: relative; width: 20px; height: 20px; }
        .crossmark::before, .crossmark::after {
            content: ''; position: absolute; background-color: white; border-radius: 2px;
        }
        .crossmark::before { width: 4px; height: 24px; top: -2px; left: 8px; transform: rotate(45deg); }
        .crossmark::after { width: 4px; height: 24px; top: -2px; left: 8px; transform: rotate(-45deg); }
        .badge.rejected { background-color: #fee2e2; color: #ef4444; }
        .badge-icon.rejected { background-color: #ef4444; }

        /* PENDING */
        .pending-icon {
            width: 80px; height: 80px; background-color: #fef3c7; border-radius: 50%;
            display: flex; justify-content: center; align-items: center;
            margin: 0 auto 32px auto; font-size: 40px; animation: pulse 2s infinite;
        }
        @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.05); } 100% { transform: scale(1); } }
        .badge.pending { background-color: #f1f5f9; color: #64748b; }
    </style>
</head>
<body>

    <div class="card">
        <!-- SUCCESS STATE -->
        <div id="state-success" class="hidden">
            <div class="icon-container success">
                <div class="icon-inner success"><div class="checkmark"></div></div>
            </div>
            <h1>Application<br>Successful</h1>
            <p id="success-message">Your submission has been received</p>
            <hr class="divider">
            <div class="badge success">
                <div class="badge-icon success"><div class="badge-check"></div></div>
                APPROVED • COMPLETED
            </div>
        </div>

        <!-- REJECTED STATE -->
        <div id="state-rejected" class="hidden">
            <div class="icon-container rejected">
                <div class="icon-inner rejected"><div class="crossmark"></div></div>
            </div>
            <h1>Application<br>Rejected</h1>
            <p id="rejected-message">Unfortunately, your application was not approved at this time.</p>
            <hr class="divider">
            <div class="badge rejected">
                <div class="badge-icon rejected"><div class="crossmark" style="transform: scale(0.4);"></div></div>
                DENIED • CLOSED
            </div>
        </div>

        <!-- PENDING STATE -->
        <div id="state-pending" class="hidden">
            <div class="pending-icon">⏳</div>
            <h1>Pending<br>Approval</h1>
            <p id="pending-message">Waiting for the admin to review this application.</p>
            <hr class="divider">
            <div class="badge pending">WAITING • IN PROGRESS</div>
        </div>
    </div>

    <script>
        const states = {
            success: document.getElementById('state-success'),
            rejected: document.getElementById('state-rejected'),
            pending: document.getElementById('state-pending')
        };
        const messages = {
            success: document.getElementById('success-message'),
            rejected: document.getElementById('rejected-message'),
            pending: document.getElementById('pending-message')
        };

        function updateUI(data) {
            Object.values(states).forEach(el => el.classList.add('hidden'));
            const currentState = data.status || 'pending';
            if (states[currentState]) {
                states[currentState].classList.remove('hidden');
                if (data.message && messages[currentState]) {
                    messages[currentState].innerText = data.message;
                }
            }
        }

        // Fetch initial state
        fetch('/status').then(response => response.json()).then(data => updateUI(data));
        
        // Listen for live updates from Telegram
        const eventSource = new EventSource('/stream');
        eventSource.onmessage = function(event) {
            const data = JSON.parse(event.data);
            updateUI(data);
        };
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    # Automatically send the Telegram buttons when the webpage is loaded
    threading.Thread(target=send_approval_request).start()
    return HTML_TEMPLATE

@app.route('/status')
def get_status():
    return jsonify(current_status)

@app.route('/stream')
def stream():
    def event_stream():
        last_status = None
        while True:
            if current_status != last_status:
                yield f"data: {json.dumps(current_status)}\n\n"
                last_status = current_status.copy()
            time.sleep(1)
    return Response(event_stream(), mimetype="text/event-stream")

if __name__ == '__main__':
    # Start Telegram Bot in the background
    print("Starting bot...")
    bot_thread = threading.Thread(target=bot.infinity_polling, daemon=True)
    bot_thread.start()
    
    # Start Flask App
    print("Web server is running on http://127.0.0.1:5000")
    app.run(debug=True, use_reloader=False)
