import { useState, useRef, useEffect } from "react";
import "./ChatInterface.css";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

// API request to the Go Gateway
async function sendToAPI(messages: Message[]): Promise<string> {
  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ messages }),
    });

    // Check if the response is ok (status 200-299)
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Gateway error (${response.status}): ${errorText}`);
    }

    const data = await response.json();
    
    // The gateway sends back {"content": "..."}
    if (!data.content) {
      throw new Error("Gateway returned empty response");
    }

    return data.content;
  } catch (error) {
    console.error("API request failed:", error);
    throw error; // Re-throw so the UI can handle it
  }
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: input.trim(),
    };

    const updated = [...messages, userMsg];
    setMessages(updated);
    setInput("");
    setLoading(true);

    try {
      const reply = await sendToAPI(updated);
      setMessages((prev) => [
        ...prev,
        { id: crypto.randomUUID(), role: "assistant", content: reply },
      ]);
    } catch (error) {
      // Show a friendly error message in the chat
      const errorMsg = error instanceof Error 
        ? error.message 
        : "Something went wrong. Please try again.";
      
      setMessages((prev) => [
        ...prev,
        { 
          id: crypto.randomUUID(), 
          role: "assistant", 
          content: `❌ Error: ${errorMsg}` 
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <header className="chat-header">
        <span>Starling</span>
      </header>

      <div className="chat-messages">
        {messages.map((msg) => (
          <div key={msg.id} className={`message ${msg.role}`}>
            {msg.content}
          </div>
        ))}
        {loading && <div className="message assistant">...</div>}
        <div ref={bottomRef} />
      </div>

      <div className="chat-input">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          placeholder="Type a message..."
          disabled={loading}
        />
        <button onClick={sendMessage} disabled={loading || !input.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}