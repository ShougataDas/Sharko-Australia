"use client";

import { useState, useRef, useEffect } from "react";
import { Send, X, Bot, User } from "lucide-react";

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
}

interface AIAssistantProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function AIAssistant({ isOpen, onClose }: AIAssistantProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  // Chat history in RAG-friendly tuple format: ["user" | "ai", message]
  const [chatHistory, setChatHistory] = useState<
    Array<["user" | "ai", string]>
  >([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const maxMessages = 5;

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  const handleSendMessage = async () => {
    if (!inputText.trim() || messages.length >= maxMessages * 2) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputText.trim(),
      isUser: true,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    // Update chat history with the latest user message
    const updatedHistory: Array<["user" | "ai", string]> = [
      ...chatHistory,
      ["user", userMessage.text],
    ];
    setChatHistory(updatedHistory);
    setInputText("");
    setIsTyping(true);

    // POST to API with required payload shape
    try {
      // Replace with your backend endpoint
      const response = await fetch(
        "https://midul914-sharo-rag-agent.hf.space/ask",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            context: updatedHistory,
            question: userMessage.text,
          }),
        }
      );
      const message = await response.json();
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        text: message.response,
        isUser: false,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiResponse]);
      // Append AI response to chat history
      setChatHistory((prev) => [...prev, ["ai", aiResponse.text]]);
      setIsTyping(false);
    } catch (err) {
      // Non-blocking: log and continue local response simulation
      // eslint-disable-next-line no-console
      console.warn("AI assistant POST failed:", err);
    }

    // Simulate AI response delay
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const canSendMessage = messages.length < maxMessages * 2 && inputText.trim();

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[3000] flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl shadow-2xl w-[90%] max-w-md h-[600px] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-white/20">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-green-500/30 to-emerald-500/20 border border-green-400/40 flex items-center justify-center">
              <Bot className="w-5 h-5 text-green-300" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">AI Assistant</h3>
              <p className="text-xs text-green-300/80">
                {maxMessages -
                  messages.filter((message) => message.isUser).length}{" "}
                messages remaining
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg bg-white/10 hover:bg-white/20 border border-white/20 transition-all duration-300"
          >
            <X className="w-5 h-5 text-white" />
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-white/60 text-sm">
              <Bot className="w-8 h-8 mx-auto mb-2 text-green-400/60" />
              <p>Ask me anything about the shark data!</p>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 ${
                message.isUser ? "justify-end" : "justify-start"
              }`}
            >
              {!message.isUser && (
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-green-500/30 to-emerald-500/20 border border-green-400/40 flex items-center justify-center flex-shrink-0">
                  <Bot className="w-4 h-4 text-green-300" />
                </div>
              )}

              <div
                className={`max-w-[80%] p-3 rounded-2xl ${
                  message.isUser
                    ? "bg-green-500/30 border border-green-400/40 text-white"
                    : "bg-white/10 border border-white/20 text-white"
                }`}
              >
                <p className="text-sm leading-relaxed">{message.text}</p>
                <p className="text-xs opacity-60 mt-1">
                  {message.timestamp.toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </p>
              </div>

              {message.isUser && (
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500/30 to-cyan-500/20 border border-blue-400/40 flex items-center justify-center flex-shrink-0">
                  <User className="w-4 h-4 text-blue-300" />
                </div>
              )}
            </div>
          ))}

          {isTyping && (
            <div className="flex gap-3 justify-start">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-green-500/30 to-emerald-500/20 border border-green-400/40 flex items-center justify-center flex-shrink-0">
                <Bot className="w-4 h-4 text-green-300" />
              </div>
              <div className="bg-white/10 border border-white/20 rounded-2xl p-3">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-bounce"></div>
                  <div
                    className="w-2 h-2 bg-green-400 rounded-full animate-bounce"
                    style={{ animationDelay: "0.1s" }}
                  ></div>
                  <div
                    className="w-2 h-2 bg-green-400 rounded-full animate-bounce"
                    style={{ animationDelay: "0.2s" }}
                  ></div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-4 border-t border-white/20">
          {messages.filter((message) => message.isUser).length >=
          maxMessages ? (
            <div className="text-center text-white/60 text-sm py-2">
              <p>
                Message limit reached. Close and reopen to start a new
                conversation.
              </p>
            </div>
          ) : (
            <div className="flex gap-2">
              <input
                ref={inputRef}
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask about shark data..."
                className="flex-1 p-3 bg-white/20 backdrop-blur-md border border-white/30 rounded-xl text-sm text-black placeholder-white/70 focus:outline-none focus:ring-2 focus:ring-green-500/50 focus:bg-white/30 transition-all duration-300"
                disabled={
                  messages.filter((message) => message.isUser).length >=
                  maxMessages
                }
              />
              <button
                onClick={handleSendMessage}
                disabled={!canSendMessage}
                className="p-3 bg-green-500/30 hover:bg-green-500/50 disabled:bg-white/10 disabled:cursor-not-allowed border border-green-400/40 rounded-xl transition-all duration-300"
              >
                <Send className="w-5 h-5 text-white" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
