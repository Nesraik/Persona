import { useRef, useState } from 'react';
import './App.css'; 
import ChatInput from './components/ChatInput';
import TextHeading from './components/TextHeading';
import ChatMessages from './components/ChatMessage';
import { v4 as uuidv4 } from 'uuid';

export interface Message {
  text: string,
  sender: 'user'| 'bot'
}

interface MessageDict{
  role: string,
  content: string
}

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [messagedict, setMessageDict] = useState<MessageDict[]>([]);
  const [isBotTyping, setIsBotTyping] = useState(false);
  const [flag, setFlag] = useState(false);
  const sessionRef = useRef(uuidv4());
  const sessionId = sessionRef.current;
  
  const handleSendMessage = async (text: string, files: File[]) => {
    const newUserMessage: Message = { text, sender: 'user' };
    setMessages(prevMessages => [...prevMessages, newUserMessage]);

    setIsBotTyping(true);

    // fetch bot response
    try {

      const formData = new FormData();

      // append messages and flag to form 
      formData.append('user_prompt', text);
      formData.append('messages', JSON.stringify(messagedict));
      formData.append('flag', String(flag));
      formData.append('session_id', sessionId);

      files.forEach((file) => {
        formData.append('files', file); 
      })

      const response = await fetch("http://localhost:8000/chat", {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const data = await response.json();
      
      // Update messages and flag based on response
      setMessageDict(data.messages);
      setFlag(data.flag);

      const botMessage: Message = {
        text: data.messages[data.messages.length - 1].content,
        sender: 'bot'
      };
      
      setMessages(prevMessages => [...prevMessages, botMessage]);

    } catch (error) {
      console.error("Error fetching bot response:", error);

      const errorMessage: Message = {
        text: "Failed to get response from the server. Please try again.",
        sender: 'bot'
      };
      setMessages(prevMessages => [...prevMessages, errorMessage]);

    } finally {
      
      setIsBotTyping(false);
    }
  };

  return (
    <div className="app-container">
      {messages.length === 0 ? (
        <div className='heading-wrapper'>
          <TextHeading />
        </div>
      ) : (
        <ChatMessages messages={messages} isBotTyping={isBotTyping} />
      )}

      <ChatInput onSendMessage={handleSendMessage} />
    </div>
  )
}

export default App;