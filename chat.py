# chat.py
import time
from datetime import datetime


class ChatSystem:
    def __init__(self, max_messages=100):
        self.messages = []
        self.max_messages = max_messages

    def add_message(self, sender, message, timestamp=None):
        if timestamp is None:
            timestamp = datetime.now().strftime("%H:%M:%S")

        self.messages.append({
            'sender': sender,
            'message': message,
            'timestamp': timestamp
        })

        if len(self.messages) > self.max_messages:
            self.messages.pop(0)

    def get_messages(self, count=20):
        return self.messages[-count:]

    def format_messages(self, count=10):
        formatted = []
        for msg in self.get_messages(count):
            formatted.append(f"[{msg['timestamp']}] {msg['sender']}: {msg['message']}")
        return formatted