import { useRef, useEffect } from "react";
import './TypingIndicator.css';
import ReactMarkdown from 'react-markdown';
import remarkGfm from "remark-gfm";
import VideoCard from "./VideoCard";

interface Message {
    sender: 'user' | 'bot';
    text: string;
}

interface ChatMessageProps {
    messages: Message[];
    isBotTyping?: boolean;
}

const isYouTubeUrl = (url: string): boolean => {
  const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+/;
  return youtubeRegex.test(url);
};

function ChatMessage({ messages, isBotTyping }: ChatMessageProps) {

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }

  useEffect(() => {
    scrollToBottom();
  }, [messages, isBotTyping]);

  return (
    <div className="chat-messages-container w-75 mx-auto">
      {messages.map((msg, index) => (
        <div
          key={index}
          className={`chat-bubble ${msg.sender === 'user' ? 'user' : 'bot'}`}
        >
          <ReactMarkdown 
            remarkPlugins={[remarkGfm]}
            components={{
              a: ({ node, ...props }) => {
                const url = props.href || '';
                
                // 4. Check if it's a bot message and a YouTube link
                if (msg.sender === 'bot' && isYouTubeUrl(url)) {
                  // Render our custom card
                  return <VideoCard url={url} />;
                }
                
                return <a {...props} target="_blank" rel="noopener noreferrer" />;
              }
            }}
            >{msg.text}</ReactMarkdown>
        </div>
      ))}

      {isBotTyping && (
        <div className="chat-bubble bot">
          <div className="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      )}
      <div ref={messagesEndRef} />
    </div>
  );
}

export default ChatMessage;