import React, { useState, useEffect, useRef } from 'react';
import { Send, Mic, MicOff, AlertCircle, Bot, User, HelpCircle, Sparkles } from 'lucide-react';
import { API_BASE_URL } from '../config';

export default function AssistantView() {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([
    {
      sender: 'bot',
      text: "Hello! I am the EduLedger AI Financial Assistant. I can help query the database, find outstanding fees, forecast revenue, and retrieve anomalies. What would you like to check today?",
      toolCalls: []
    }
  ]);
  const [loading, setLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(false);
  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);

  // Suggested questions
  const suggestions = [
    "How much fee is pending?",
    "Which class has the highest outstanding amount?",
    "Show today's collections.",
    "Predict this month's revenue.",
    "Any unusual expenses this week?"
  ];

  // Setup Web Speech API
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      setSpeechSupported(true);
      const rec = new SpeechRecognition();
      rec.continuous = false;
      rec.interimResults = false;
      rec.lang = 'en-US';

      rec.onstart = () => {
        setIsListening(true);
      };

      rec.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setQuery(transcript);
      };

      rec.onerror = (e) => {
        console.error('Speech recognition error:', e);
        setIsListening(false);
      };

      rec.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = rec;
    }
  }, []);

  const toggleListening = () => {
    if (!recognitionRef.current) return;

    if (isListening) {
      recognitionRef.current.stop();
    } else {
      recognitionRef.current.start();
    }
  };

  const handleSend = async (textToSend) => {
    const text = textToSend || query;
    if (!text.trim()) return;

    // Add user message
    const userMsg = { sender: 'user', text };
    setMessages(prev => [...prev, userMsg]);
    setQuery('');
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: text })
      });
      const data = await response.json();
      
      const botMsg = {
        sender: 'bot',
        text: data.response || "No response received.",
        isMock: data.mock,
        toolCalls: data.tool_calls || []
      };
      
      setMessages(prev => [...prev, botMsg]);
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, {
        sender: 'bot',
        text: "Sorry, I couldn't reach the AI Assistant backend. Make sure the Flask server is running.",
        toolCalls: []
      }]);
    } finally {
      setLoading(false);
    }
  };

  // Scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-[580px]">
      
      {/* Suggestions Sidebar */}
      <div className="lg:col-span-4 glass-card rounded-xl p-5 flex flex-col justify-between h-full">
        <div>
          <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider mb-4 flex items-center gap-1.5">
            <HelpCircle className="w-4 h-4 text-emerald-600 shrink-0" /> Suggested Queries
          </h3>
          <p className="text-xs text-slate-500 mb-4 leading-relaxed">
            Click any question to query the database. The assistant will parse the query, execute the matching backend function, and summarize the result.
          </p>
          <div className="space-y-2">
            {suggestions.map((s, idx) => (
              <button
                key={idx}
                onClick={() => !loading && handleSend(s)}
                disabled={loading}
                className="w-full p-3 bg-white hover:bg-slate-50 border border-slate-200 hover:border-emerald-300 rounded-lg text-left text-xs text-slate-700 font-semibold transition-all duration-150 block"
              >
                "{s}"
              </button>
            ))}
          </div>
        </div>

        <div className="p-3 bg-emerald-50 border border-emerald-100 rounded-lg text-[10px] text-slate-655 leading-normal space-y-1">
          <div className="flex items-center text-emerald-650 font-bold mb-1">
            <Sparkles className="w-3.5 h-3.5 mr-1" /> Multi-turn Tool Calling
          </div>
          Claude translates questions directly into database query arguments and reports responses conversationally.
        </div>
      </div>

      {/* Chat Workspace */}
      <div className="lg:col-span-8 glass-card rounded-xl p-5 flex flex-col justify-between h-full relative">
        
        {/* Messages Feed */}
        <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-1">
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[85%] rounded-xl p-3.5 space-y-2 text-sm ${
                msg.sender === 'user'
                  ? 'bg-emerald-500 text-white rounded-tr-none'
                  : 'bg-white border border-slate-200 text-slate-800 rounded-tl-none shadow-md'
              }`}>
                {/* Header */}
                <div className="flex items-center space-x-1.5 text-[10px] text-slate-500 font-bold pb-1 border-b border-slate-100">
                  {msg.sender === 'user' ? (
                    <>
                      <User className="w-3 h-3 text-emerald-100" />
                      <span className="text-emerald-100">You</span>
                    </>
                  ) : (
                    <>
                      <Bot className="w-3 h-3 text-emerald-600" />
                      <span className="text-slate-750">EduLedger Financial Assistant</span>
                      {msg.isMock && (
                        <span className="bg-slate-100 text-slate-400 px-1 rounded text-[8px] font-normal font-sans ml-1">OFFLINE MOCK</span>
                      )}
                    </>
                  )}
                </div>

                {/* Text Content */}
                <div className="whitespace-pre-wrap leading-relaxed">
                  {msg.text}
                </div>

                {/* Tool call traces */}
                {msg.toolCalls && msg.toolCalls.length > 0 && (
                  <div className="pt-2 border-t border-slate-100 space-y-1.5">
                    <span className="text-[9px] font-bold text-emerald-650 block uppercase tracking-wider">Executed Backend Tool Call:</span>
                    {msg.toolCalls.map((tool, tIdx) => (
                      <div key={tIdx} className="p-2 rounded bg-slate-50 border border-slate-200 font-mono text-[9px] text-slate-600 flex flex-col">
                        <span className="text-emerald-650 font-bold">fn: {tool.name}()</span>
                        {tool.args && Object.keys(tool.args).length > 0 && (
                          <span className="mt-0.5">args: {JSON.stringify(tool.args)}</span>
                        )}
                        <span className="mt-1 text-[8px] text-slate-400 truncate">Result: {JSON.stringify(tool.result)}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-white border border-slate-200 rounded-xl rounded-tl-none p-3.5 text-xs text-slate-500 flex items-center space-x-2">
                <span className="w-3 h-3 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin"></span>
                <span>Claude is thinking and querying school.db...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Controls */}
        <div className="border-t border-slate-250 pt-4">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-center space-x-2"
          >
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask a school financial question..."
              className="flex-1 px-4 py-3 rounded-lg glass-input text-xs"
              disabled={loading}
            />

            {speechSupported && (
              <button
                type="button"
                onClick={toggleListening}
                className={`p-3 rounded-lg border transition ${
                  isListening
                    ? 'bg-rose-500/20 border-rose-500 text-rose-400 glow-active'
                    : 'bg-white hover:bg-slate-50 border border-slate-200 text-slate-500 hover:text-slate-800'
                }`}
                title={isListening ? 'Stop listening' : 'Start voice transcription (Web Speech API)'}
              >
                {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
              </button>
            )}

            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="p-3 bg-emerald-500 hover:bg-emerald-600 text-white font-bold rounded-lg transition disabled:opacity-50 disabled:hover:bg-emerald-500 flex items-center justify-center shadow-md shadow-emerald-500/10"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>

      </div>
    </div>
  );
}
