'use client';

import { useState, useRef, useEffect } from 'react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMsg: Message = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');

    try {
      const res = await fetch('http://127.0.0.1:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input }),
      });

      if (!res.ok) throw new Error('FastAPIからの応答がありません');
      const data = await res.json();

      const aiMsg: Message = { role: 'assistant', content: data.reply };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (error) {
      console.error(error);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'サーバーとの通信でエラーが発生しました。' },
      ]);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-white text-gray-800 font-sans">
      {/* ヘッダー */}
      <header className="border-b border-gray-200 py-4 px-6 text-center font-semibold text-lg sticky top-0 bg-white z-10">
        AIパーソナルトレーナー
      </header>

      {/* チャットエリア */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${
              msg.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`px-4 py-3 rounded-2xl max-w-[75%] text-sm leading-relaxed shadow-sm ${
                msg.role === 'user'
                  ? 'bg-gray-200 text-gray-900 rounded-br-none'
                  : 'bg-white border border-gray-200 text-gray-800 rounded-bl-none'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
        <div ref={chatEndRef} />
      </div>

      {/* 入力エリア */}
      <div className="border-t border-gray-200 bg-white px-4 py-3 flex items-center">
        <input
          type="text"
          placeholder="AIトレーナーに質問..."
          className="flex-1 border border-gray-300 rounded-2xl px-4 py-2 mr-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 transition"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
        />
        <button
          onClick={handleSend}
          className="bg-gray-900 text-white px-5 py-2 rounded-2xl text-sm hover:bg-gray-800 transition"
        >
          送信
        </button>
      </div>
    </div>
  );
}
