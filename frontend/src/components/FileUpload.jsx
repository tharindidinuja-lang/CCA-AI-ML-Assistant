import React, { useState } from 'react';

export default function FileUpload({ onUploadSuccess }) {
  const [uploading, setUploading] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    setUploading(true);
    setStatusMessage('Processing PDF...');

    try {
      const res = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();
      if (res.ok) {
        setStatusMessage(`Uploaded! (${data.chunks_created} chunks created)`);
        if (onUploadSuccess) onUploadSuccess(data);
      } else {
        setStatusMessage(`Error: ${data.detail || 'Upload failed'}`);
      }
    } catch (err) {
      setStatusMessage('Failed to connect to backend server.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="p-4 bg-gray-800 rounded-xl border border-gray-700 shadow-md">
      <h3 className="text-sm font-semibold text-gray-300 mb-2">Upload Document</h3>
      <label className="flex flex-col items-center justify-center w-full h-24 border-2 border-dashed border-gray-600 rounded-lg cursor-pointer hover:border-blue-500 hover:bg-gray-750 transition-all">
        <span className="text-xs text-gray-400">
          {uploading ? 'Processing...' : 'Click or drop PDF here'}
        </span>
        <input 
          type="file" 
          accept=".pdf" 
          onChange={handleFileChange} 
          disabled={uploading} 
          className="hidden" 
        />
      </label>
      {statusMessage && (
        <p className="mt-2 text-xs text-blue-400 text-center font-medium">{statusMessage}</p>
      )}
    </div>
  );
}