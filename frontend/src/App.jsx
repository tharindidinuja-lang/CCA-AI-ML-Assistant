import React, { useState } from 'react';
import FileUpload from './components/FileUpload';
import ChatWindow from './components/ChatWindow';
import ChatInput from './components/ChatInput';

export default function App() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSendMessage = async (question) => {
    // Append user message immediately
    const userMsg = { sender: 'user', text: question };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, top_k: 3 }),
      });

      const data = await response.json();

      if (response.ok) {
        const botMsg = {
          sender: 'bot',
          text: data.answer,
          citations: data.citations || [],
        };
        setMessages((prev) => [...prev, botMsg]);
      } else {
        setMessages((prev) => [
          ...prev,
          { sender: 'bot', text: `Error: ${data.detail || 'Could not fetch answer.'}` },
        ]);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { sender: 'bot', text: 'Failed to communicate with server backend.' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-gray-900 text-gray-100">
      {/* Sidebar for document operations */}
      <aside className="w-80 border-r border-gray-800 p-4 flex flex-col gap-4 bg-gray-800">
        <div className="mb-2">
          <h1 className="text-lg font-bold text-white">CCA AI Assistant</h1>
          <p className="text-xs text-gray-400">University Handbook RAG System</p>
        </div>
        <FileUpload />
      </aside>

      {/* Main Chat Interface */}
      <main className="flex-1 flex flex-col h-full bg-gray-900">
        <ChatWindow messages={messages} loading={loading} />
        <ChatInput onSendMessage={handleSendMessage} disabled={loading} />
      </main>
    </div>
  );
}