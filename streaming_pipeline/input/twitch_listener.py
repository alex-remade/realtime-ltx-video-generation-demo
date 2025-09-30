import threading
import time
import socket
from queue import Queue, Empty
from typing import List, Dict, Any
import sys
import os
from dataclasses import dataclass
from typing import Optional
from streaming_pipeline.models import Monitorable

@dataclass
class TwitchComment:
    username: str
    message: str
    timestamp: float
    user_id: Optional[str] = None
    badges: Optional[List[str]] = None
    emotes: Optional[Dict] = None


class TwitchChatListener(Monitorable):
    def __init__(self, channel_name: str, oauth_token: str = None):
        self.channel_name = channel_name.lower()
        self.oauth_token = oauth_token  # Not needed for anonymous
        self.comment_queue = Queue(maxsize=100)
        self.is_listening = False
        self._thread = None
        
    def start_listening(self):
        """Start listening to Twitch chat"""
        if self.is_listening:
            return
            
        self.is_listening = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        print(f"Started listening to Twitch chat: #{self.channel_name} (anonymous)")
    
    def stop_listening(self):
        """Stop listening to Twitch chat"""
        self.is_listening = False
        if self._thread:
            self._thread.join(timeout=2.0)  # Don't block forever
            if self._thread.is_alive():
                print("⚠️ Twitch listener thread didn't stop gracefully")
        print("Stopped listening to Twitch chat")
    
    def _listen_loop(self):
        """Background loop for Twitch chat listening"""
        while self.is_listening:
            try:
                self._connect_and_listen()
            except Exception as e:
                print(f"Connection error: {e}")
                if self.is_listening:
                    print("Reconnecting in 5 seconds...")
                    time.sleep(5)
    
    def _connect_and_listen(self):
        """Connect to Twitch IRC and listen for messages (anonymous)"""
        sock = socket.socket()
        sock.connect(('irc.chat.twitch.tv', 6667))
        
        # Anonymous connection - no authentication needed
        sock.send(f"NICK justinfan{int(time.time())}\n".encode('utf-8'))  # Random anonymous nick
        sock.send(f"JOIN #{self.channel_name}\n".encode('utf-8'))
        
        buffer = ""
        
        try:
            while self.is_listening:
                response = sock.recv(1024).decode('utf-8')
                buffer += response
                
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    self._process_message(line.strip())
                    
        finally:
            sock.close()
    
    def _process_message(self, message: str):
        """Process incoming Twitch IRC message"""
        # Skip empty messages
        if not message.strip():
            return
            
        # Handle PING to keep connection alive
        if message.startswith('PING'):
            return
            
        # Only process chat messages
        if 'PRIVMSG' not in message:
            return
            
        try:
            # Parse Twitch IRC message
            # Format: :username!username@username.tmi.twitch.tv PRIVMSG #channel :message
            parts = message.split(':', 2)
            if len(parts) < 3:
                return
                
            user_part = parts[1].split('!')[0]
            chat_message = parts[2]
            
            comment = TwitchComment(
                username=user_part,
                message=chat_message,
                timestamp=time.time()
            )
            
            # Add to queue
            if not self.comment_queue.full():
                self.comment_queue.put(comment)
                # print(f"[{user_part}]: {chat_message}")  # Comment this out
                
        except Exception as e:
            print(f"Error processing message: {e}")
    
    def get_recent_comments(self, count: int = 10) -> List[TwitchComment]:
        """Get recent comments from the queue"""
        comments = []
        
        # Get up to 'count' comments from queue
        while not self.comment_queue.empty() and len(comments) < count:
            try:
                comment = self.comment_queue.get_nowait()
                comments.append(comment)
            except Empty:
                break
        
        return comments
    
    def get_queue_size(self) -> int:
        """Get current queue size"""
        return self.comment_queue.qsize()
    
    def get_status(self) -> Dict[str, Any]:
        """Get component status for monitoring"""
        return {
            "channel": self.channel_name,
            "is_listening": self.is_listening,
            "queue_size": self.get_queue_size()
        }

