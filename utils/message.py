import time, requests
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# 슬랙 토큰과 채널 설정
slack_token = "your-slack_token"
channel_id = "your-slack-channel-id"
client = WebClient(token=slack_token)

def send_slack_message(message):
    try:
        response = client.chat_postMessage(
            channel=channel_id,
            text=message
        )
        print(f"Message sent: {response['message']['text']}")
    except SlackApiError as e:
        print(f"Error sending message: {e.response['error']}")
        
bot_token = "your-telegram-bot-token"
chat_id = "your-telegram-chat-id"

def send_telegram_message(bot_token, chat_id, message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("메시지 전송 성공!")
        else:
            print(f"에러 발생: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"요청 중 에러 발생: {e}")
