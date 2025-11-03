import { useState } from 'react';
import './App.css'; 
import ChatInput from './components/ChatInput';
import TextHeading from './components/TextHeading';
import ChatMessages from './components/ChatMessage';

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
  
  const handleSendMessage = async (text: string) => {
    const newUserMessage: Message = { text, sender: 'user' };
    setMessages(prevMessages => [...prevMessages, newUserMessage]);

    setIsBotTyping(true);

    // fetch bot response
    try {

      const response = await fetch("http://localhost:8000/chat", {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_prompt: text,
          messages: messagedict,
          flag: flag
        }),
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
        text: "Sorry, I'm having trouble connecting.",
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