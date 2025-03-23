export class WebSocketService {
    constructor(url) {
      this.socket = new WebSocket(url);
    }
  
    // Open WebSocket connection
    connect(onMessageCallback) {
      this.socket.onopen = () => {
        console.log("WebSocket connected");
      };
  
      this.socket.onmessage = (message) => {
        onMessageCallback(message.data);
      };
  
      this.socket.onclose = () => {
        console.log("WebSocket disconnected");
      };
  
      this.socket.onerror = (error) => {
        console.log("WebSocket error", error);
      };
    }
  
    // Send message through WebSocket
    sendMessage(message) {
      if (this.socket.readyState === WebSocket.OPEN) {
        this.socket.send(message);
      } else {
        console.log("WebSocket is not open.");
      }
    }
  }
  