// src/components/ChatInput.tsx
import { useState, useRef, useEffect, ChangeEvent, KeyboardEvent } from "react";

interface ChatInputProps {
  onSendMessage: (message: string, files: File[]) => void;
}

function ChatInput({ onSendMessage }: ChatInputProps) {
  const [inputValue, setInputValue] = useState("");
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${Math.min(textarea.scrollHeight, window.innerHeight * 0.35)}px`;
    }
  }, [inputValue]);

  const handleChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    setInputValue(e.target.value);
  };

  const handleSend = () => {
    if (inputValue.trim() === "" && selectedFiles.length === 0) return;
    onSendMessage(inputValue.trim(), selectedFiles);
    setInputValue("");
    setSelectedFiles([]);
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handlePaperclipClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.value = ''; // CRITICAL: Reset to allow same-file selection
      fileInputRef.current.click();
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      // CRITICAL: Append new files to existing ones
      setSelectedFiles(prev => [...prev, ...Array.from(files)]);
    }
  };

  const removeFile = (indexToRemove: number) => {
    setSelectedFiles(prev => prev.filter((_, index) => index !== indexToRemove));
  };

  return (
    <div className="input-container w-75 mx-auto">
      <div className="d-flex flex-column p-2 border rounded-3 bg-white shadow-sm w-100">
        <input
          type="file"
          multiple // CRITICAL: Allows multiple selection in dialog
          ref={fileInputRef}
          onChange={handleFileChange}
          style={{ display: 'none' }}
        />
        
        {/* File Chips Container */}
        {selectedFiles.length > 0 && (
          <div className="file-chips-container">
            {selectedFiles.map((file, index) => (
              // The Chip Box
              <div key={index} className="file-chip">
                {/* Left side: File Details (two rows) */}
                <div className="file-details">
                  <div className="file-name-top">{file.name}</div>
                  <div className="file-type-bottom">
                     {/* Using a specific filled PDF icon for the look */}
                    <i className="bi bi-file-earmark-pdf-fill file-icon-red"></i>
                    <span className="file-type-text">PDF</span>
                  </div>
                </div>
                {/* Right side: Close button */}
                <button onClick={() => removeFile(index)} className="btn-close-file-absolute">
                  <i className="bi bi-x"></i>
                </button>
              </div>
            ))}
          </div>
        )}

        <textarea
          ref={textareaRef}
          className="form-control border-0 shadow-none p-2"
          placeholder="Ask anything"
          value={inputValue}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          rows={1}
          style={{
            resize: "none",
            backgroundColor: "transparent",
            flexGrow: 1,
            color: 'var(--input-text)',
            maxHeight: '35vh',
            overflowY: 'auto'
          }}
        />

        <div className="d-flex justify-content-between align-items-center pt-2">
           <button className="chat-file-button" onClick={handlePaperclipClick} style={{ backgroundColor: 'transparent', border: 'none', padding: 0, cursor: 'pointer', width: '2.5rem', height: '2.5rem', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
             <i className="bi bi-paperclip" style={{ fontSize: '1.5rem', color: '#888888' }}></i>
           </button>
           <button className="chat-send-button" onClick={handleSend} style={{ width: '2.5rem', height: '2.5rem', padding: 0, display: 'flex', justifyContent: 'center', alignItems: 'center', backgroundColor: 'transparent', border: 'none', borderRadius: '50%', cursor: 'pointer', outline: 'none' }}>
             <i className="bi bi-arrow-up-circle-fill" style={{ color: '#ffffffff', fontSize: '2.5rem' }}></i>
           </button>
        </div>
      </div>
    </div>
  );
}

export default ChatInput;