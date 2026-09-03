import React from 'react';

export default function ChatWindow({ messages, loading }) {
  return (
    <div className="flex-1 p-4 overflow-y-auto space-y-4">
      {messages.length === 0 && (
        <div className="text-center text-gray-500 mt-20">
          <p className="text-lg font-medium">Welcome to CCA AI Assistant</p>
          <p className="text-sm">Upload a handbook PDF or ask a question to start.</p>
        </div>
      )}

      {messages.map((msg, idx) => (
        <div
          key={idx}
          className={`flex flex-col ${
            msg.sender === 'user' ? 'items-end' : 'items-start'
          }`}
        >
          <div
            className={`max-w-xl p-3 rounded-lg text-sm ${
              msg.sender === 'user'
                ? 'bg-blue-600 text-white rounded-br-none'
                : 'bg-gray-800 text-gray-200 border border-gray-700 rounded-bl-none'
            }`}
          >
            <p className="whitespace-pre-wrap">{msg.text}</p>
          </div>

          {/* Render Citations if available */}
          {msg.citations && msg.citations.length > 0 && (
            <div className="mt-2 text-xs text-gray-400 bg-gray-800 p-2 rounded border border-gray-700">
              <span className="font-semibold text-blue-400">Sources:</span>
              <ul className="list-disc list-inside mt-1 space-y-0.5">
                {msg.citations.map((cite, cIdx) => (
                  <li key={cIdx}>
                    Page {cite.page_number || cite.page || cite.page_no || 'N/A'}{' '}
                    {cite.source_file || cite.source ? `(${cite.source_file || cite.source})` : ''}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ))}

      {loading && (
        <div className="text-gray-400 text-sm italic animate-pulse">
          CCA Assistant is searching documents...
        </div>
      )}
    </div>
  );
}