import { useState, useRef, useEffect, ChangeEvent, KeyboardEvent } from "react";

interface ChatInputProps {
  onSendMessage: (message: string) => void;
}

function ChatInput({ onSendMessage }: ChatInputProps) {
  const [inputValue, setInputValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      const scrollHeight = textarea.scrollHeight;
      const maxHeight = window.innerHeight * 0.35;

      if (scrollHeight > maxHeight) {
        textarea.style.height = `${maxHeight}px`;
        textarea.style.overflowY = "auto";
      } else {
        textarea.style.height = `${scrollHeight}px`;
        textarea.style.overflowY = "hidden";
      }
    }
  }, [inputValue]);

  const handleChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    setInputValue(e.target.value);
  };

  const handleSend = () => {
    if (inputValue.trim() === "") return;
    onSendMessage(inputValue.trim());
    setInputValue("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault(); 
      handleSend();       
    }
  };

  return (
    <div
      className="input-container w-75 mx-auto"
      style={{ 
        bottom: "2rem"
      }}
    >
      <div className="d-flex flex-column p-2 border rounded-3 bg-white shadow-sm w-100">
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
          }}
          aria-label="Chat input"
        />

        <div className="d-flex justify-content-end pt-2">
          <button
            className="chat-send-button"
            onClick={handleSend}
            style={{
              width: '2.5rem',  
              height: '2.5rem',
              padding: 0,
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              backgroundColor: 'transparent', 
              border: 'none',
              borderRadius: '50%',
              cursor: 'pointer',
              outline: 'none',
            }}
          >
            <i className="bi bi-arrow-up-circle-fill"
            style={{ color: '#ffffff', fontSize: '2.5rem' }}></i>
          </button>
        </div>
      </div>
    </div>
  );
}

export default ChatInput;