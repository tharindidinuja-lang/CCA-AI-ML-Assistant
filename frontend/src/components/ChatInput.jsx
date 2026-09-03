import React, { useState } from 'react';

export default function ChatInput({ onSendMessage, disabled }) {
  const [input, setInput] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    onSendMessage(input);
    setInput('');
  };

  return (
    <form onSubmit={handleSubmit} className="p-4 border-t border-gray-800 flex gap-2 bg-gray-900">
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Ask a question about your handbook..."
        disabled={disabled}
        className="flex-1 px-4 py-2 bg-gray-800 text-white rounded-lg focus:outline-none border border-gray-700"
      />
      <button
        type="submit"
        disabled={disabled}
        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-500 disabled:opacity-50 transition-colors"
      >
        Send
      </button>
    </form>
  );
}