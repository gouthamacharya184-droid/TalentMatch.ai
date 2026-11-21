import React, { useState, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import {
  Sparkles,
  Bot,
  Send,
  X,
  Minus,
  RotateCcw,
  Copy,
  Check,
  ChevronDown
} from 'lucide-react';
import { chatbotApi } from '../services/api';
import { useAuth } from '../context/AuthContext';
import type { ChatbotMessage } from '../types';

const getInitialDynamicWelcome = (userFullName?: string): string => {
  const hour = new Date().getHours();
  const timeGreeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';
  const name = userFullName?.trim() ? userFullName.trim().split(' ')[0] : 'Alex';
  const salutation = `${timeGreeting}, ${name}!`;

  return `${salutation} I'm your TalentMatch AI Copilot, connected live to your recruitment database. I can assist with resume analysis, explain scoring algorithms, highlight top candidates, or answer platform questions.\n\nHow can I assist your recruitment workflow today?`;
};

export const ChatbotWidget: React.FC = () => {
  const location = useLocation();
  const { user } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string>(() => `conv_${Date.now()}`);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const [messages, setMessages] = useState<ChatbotMessage[]>(() => [
    {
      id: 'welcome_1',
      role: 'assistant',
      content: getInitialDynamicWelcome(user?.full_name),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      mode: 'dynamic',
    }
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to latest message
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen && !isMinimized) {
      scrollToBottom();
    }
  }, [messages, isOpen, isMinimized, isLoading]);

  // Focus textarea when opened
  useEffect(() => {
    if (isOpen && !isMinimized) {
      setTimeout(() => textareaRef.current?.focus(), 150);
    }
  }, [isOpen, isMinimized]);

  // Dynamically load live database-grounded greeting when chat is fresh
  useEffect(() => {
    if (messages.length === 1 && messages[0].id.startsWith('welcome')) {
      chatbotApi
        .getWelcomeMessage({ page_context: location.pathname })
        .then((res) => {
          if (res?.welcome_message) {
            setMessages([
              {
                id: messages[0].id,
                role: 'assistant',
                content: res.welcome_message,
                timestamp: res.timestamp || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                mode: 'dynamic',
                relevant_data: res.stats ? { stats: res.stats } : undefined,
              }
            ]);
          }
        })
        .catch(() => {
          // Keep instant dynamic greeting if network error
        });
    }
  }, [isOpen, location.pathname, user?.full_name]);

  const handleSendMessage = async (textToSend?: string) => {
    const text = (textToSend || inputMessage).trim();
    if (!text || isLoading) return;

    const userMsgId = `user_${Date.now()}`;
    const userMessage: ChatbotMessage = {
      id: userMsgId,
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const pageContext = `Page: ${location.pathname} (TalentMatch AI)`;
      const res = await chatbotApi.sendMessage({
        message: text,
        conversation_id: conversationId,
        page_context: pageContext
      });

      const assistantMsg: ChatbotMessage = {
        id: `assistant_${Date.now()}`,
        role: 'assistant',
        content: res.assistant_message,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        mode: res.mode,
        relevant_data: res.relevant_data,
      };

      if (res.conversation_id) {
        setConversationId(res.conversation_id);
      }

      setMessages((prev) => [...prev, assistantMsg]);
    } catch {
      const errorMsg: ChatbotMessage = {
        id: `err_${Date.now()}`,
        role: 'assistant',
        content: 'I apologize, but I encountered an issue connecting to the recruitment service. Please try again.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        error: true
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleClear = async () => {
    try {
      await chatbotApi.clearConversation(conversationId);
    } catch {
      // ignore
    }
    const newCid = `conv_${Date.now()}`;
    setConversationId(newCid);
    const welcomeId = `welcome_${Date.now()}`;

    // Set immediate dynamic welcome greeting
    setMessages([
      {
        id: welcomeId,
        role: 'assistant',
        content: getInitialDynamicWelcome(user?.full_name),
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        mode: 'dynamic',
      }
    ]);

    // Fetch live backend metrics
    chatbotApi
      .getWelcomeMessage({ page_context: location.pathname })
      .then((res) => {
        if (res?.welcome_message) {
          setMessages([
            {
              id: welcomeId,
              role: 'assistant',
              content: res.welcome_message,
              timestamp: res.timestamp || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
              mode: 'dynamic',
              relevant_data: res.stats ? { stats: res.stats } : undefined,
            }
          ]);
        }
      })
      .catch(() => { });
  };

  // Helper to format basic markdown (bold, lists, headers, code, tables)
  const renderFormattedContent = (content: string) => {
    const lines = content.split('\n');
    return (
      <div className="space-y-1.5 text-xs sm:text-[13px] leading-relaxed">
        {lines.map((line, idx) => {
          // Headers
          if (line.startsWith('### ')) {
            return (
              <h4 key={idx} className="font-bold text-slate-900 text-sm mt-2 mb-1">
                {line.replace('### ', '')}
              </h4>
            );
          }
          if (line.startsWith('## ')) {
            return (
              <h3 key={idx} className="font-bold text-slate-900 text-sm mt-2.5 mb-1">
                {line.replace('## ', '')}
              </h3>
            );
          }
          // Blockquote
          if (line.startsWith('> ')) {
            return (
              <div key={idx} className="border-l-2 border-blue-500 pl-2.5 py-0.5 text-slate-600 italic bg-blue-50/50 rounded-r my-1">
                {line.replace('> ', '')}
              </div>
            );
          }
          // Bullet point
          if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
            const raw = line.trim().replace(/^[-*]\s+/, '');
            return (
              <div key={idx} className="flex items-start gap-1.5 pl-1 my-0.5">
                <span className="text-blue-500 font-bold shrink-0">•</span>
                <span dangerouslySetInnerHTML={{ __html: formatInline(raw) }} />
              </div>
            );
          }
          // Numbered list
          if (/^\d+\.\s+/.test(line.trim())) {
            const raw = line.trim().replace(/^\d+\.\s+/, '');
            const match = line.trim().match(/^(\d+)\./);
            const num = match ? match[1] : '1';
            return (
              <div key={idx} className="flex items-start gap-1.5 pl-1 my-0.5">
                <span className="text-blue-600 font-bold shrink-0">{num}.</span>
                <span dangerouslySetInnerHTML={{ __html: formatInline(raw) }} />
              </div>
            );
          }
          // Table separator or pipe line
          if (line.trim().startsWith('|')) {
            if (line.includes('---')) return null; // skip markdown divider
            const cells = line.split('|').map((c) => c.trim()).filter((_, i, arr) => i > 0 && i < arr.length - 1);
            return (
              <div key={idx} className="grid grid-cols-3 sm:grid-cols-4 gap-1 py-1 border-b border-slate-200/60 text-[11px]">
                {cells.map((cell, ci) => (
                  <span key={ci} className="font-medium text-slate-700 truncate" dangerouslySetInnerHTML={{ __html: formatInline(cell) }} />
                ))}
              </div>
            );
          }
          // Normal line
          if (!line.trim()) {
            return <div key={idx} className="h-1" />;
          }
          return (
            <p key={idx} dangerouslySetInnerHTML={{ __html: formatInline(line) }} />
          );
        })}
      </div>
    );
  };

  const formatInline = (text: string) => {
    let t = text;
    // Bold **text**
    t = t.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-slate-900">$1</strong>');
    // Code `code`
    t = t.replace(/`([^`]+)`/g, '<code class="bg-blue-50 text-blue-700 px-1 py-0.5 rounded text-[11px] font-mono border border-blue-200/50">$1</code>');
    return t;
  };

  return (
    <>
      {/* ── 1. Floating Launch Button ── */}
      {!isOpen && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-3">
          {/* Subtle greeting pill on initial page load */}
          <div className="hidden md:flex items-center gap-2 bg-white/95 backdrop-blur-md px-3.5 py-2 rounded-full shadow-lg border border-slate-200 text-xs font-medium text-slate-700 animate-fade-in pointer-events-none">
            <Sparkles className="w-3.5 h-3.5 text-blue-600 animate-pulse" />
            <span>Ask TalentMatch AI</span>
          </div>

          <button
            onClick={() => {
              setIsOpen(true);
              setIsMinimized(false);
            }}
            className="w-14 h-14 rounded-full bg-gradient-to-tr from-blue-700 via-blue-600 to-blue-500 text-white shadow-xl shadow-blue-500/35 hover:shadow-2xl hover:scale-105 active:scale-95 transition-all duration-200 flex items-center justify-center relative group focus:outline-none focus:ring-4 focus:ring-blue-300"
            aria-label="Open TalentMatch AI Assistant"
          >
            <Sparkles className="w-6 h-6 transition-transform group-hover:rotate-12" />
            {/* Online Pulse Indicator */}
            <span className="absolute top-0 right-0 w-3.5 h-3.5 rounded-full bg-emerald-500 border-2 border-white shadow-sm flex items-center justify-center">
              <span className="w-1.5 h-1.5 rounded-full bg-white animate-ping opacity-75"></span>
            </span>
          </button>
        </div>
      )}

      {/* ── 2. Chatbot Window ── */}
      {isOpen && (
        <div
          className={`fixed bottom-6 right-6 z-50 flex flex-col bg-white/95 backdrop-blur-xl border border-slate-200/80 shadow-2xl rounded-2xl overflow-hidden transition-all duration-300 ${isMinimized
              ? 'w-80 h-16'
              : 'w-[92vw] sm:w-[420px] h-[590px] max-h-[calc(100vh-6rem)]'
            }`}
          style={{ boxShadow: '0 20px 45px -10px rgba(15, 23, 42, 0.18)' }}
        >
          {/* Header */}
          <div className="h-16 px-4 bg-gradient-to-r from-blue-900 via-blue-800 to-blue-700 text-white flex items-center justify-between shrink-0 select-none">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-white/10 backdrop-blur-md border border-white/20 flex items-center justify-center text-white shadow-inner">
                <Sparkles className="w-5 h-5 text-blue-200" />
              </div>
              <div>
                <div className="flex items-center gap-1.5">
                  <h3 className="font-bold text-sm tracking-tight text-white">TalentMatch AI Assistant</h3>
                </div>
                <div className="flex items-center gap-1.5 text-[11px] text-blue-200/90 font-medium">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                  <span>Online • Decision Support</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-1 text-white/80">
              <button
                onClick={handleClear}
                title="Clear conversation"
                className="p-1.5 hover:text-white hover:bg-white/10 rounded-lg transition"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
              <button
                onClick={() => setIsMinimized(!isMinimized)}
                title={isMinimized ? 'Expand' : 'Minimize'}
                className="p-1.5 hover:text-white hover:bg-white/10 rounded-lg transition"
              >
                {isMinimized ? <ChevronDown className="w-4 h-4" /> : <Minus className="w-4 h-4" />}
              </button>
              <button
                onClick={() => setIsOpen(false)}
                title="Close chatbot"
                className="p-1.5 hover:text-white hover:bg-white/10 rounded-lg transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Body (hidden when minimized) */}
          {!isMinimized && (
            <>
              {/* Message Feed */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50/50">
                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
                  >
                    <div
                      className={`max-w-[88%] rounded-2xl px-4 py-3 shadow-xs relative group ${msg.role === 'user'
                          ? 'bg-gradient-to-r from-blue-700 to-blue-600 text-white rounded-tr-xs'
                          : 'bg-white border border-slate-200/80 text-slate-800 rounded-tl-xs'
                        }`}
                    >
                      {/* Message Content */}
                      {msg.role === 'user' ? (
                        <p className="text-xs sm:text-[13px] whitespace-pre-wrap leading-relaxed">
                          {msg.content}
                        </p>
                      ) : (
                        renderFormattedContent(msg.content)
                      )}

                      {/* AI Response Tools */}
                      {msg.role === 'assistant' && (
                        <div className="mt-2.5 pt-2 border-t border-slate-100 flex items-center justify-between text-[10px] text-slate-400">
                          <span className="flex items-center gap-1 font-medium">
                            <Bot className="w-3 h-3 text-blue-500" />
                            {msg.mode === 'llm'
                              ? 'TalentMatch AI • Gemini'
                              : msg.mode === 'dynamic'
                                ? 'TalentMatch AI • Live Intelligence'
                                : 'TalentMatch Copilot'}
                          </span>
                          <button
                            onClick={() => handleCopy(msg.id, msg.content)}
                            className="flex items-center gap-1 text-slate-400 hover:text-slate-700 px-1.5 py-0.5 rounded hover:bg-slate-100 transition"
                            title="Copy response"
                          >
                            {copiedId === msg.id ? (
                              <>
                                <Check className="w-3 h-3 text-emerald-600" />
                                <span className="text-emerald-600">Copied</span>
                              </>
                            ) : (
                              <>
                                <Copy className="w-3 h-3" />
                                <span>Copy</span>
                              </>
                            )}
                          </button>
                        </div>
                      )}
                    </div>

                    <span className="text-[10px] text-slate-400 mt-1 px-1">
                      {msg.timestamp}
                    </span>
                  </div>
                ))}

                {/* Loading / Typing indicator */}
                {isLoading && (
                  <div className="flex items-start gap-2 animate-fade-in">
                    <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-xs px-4 py-3 shadow-xs flex items-center gap-2">
                      <Sparkles className="w-3.5 h-3.5 text-blue-600 animate-spin" />
                      <span className="text-xs text-slate-500 font-medium">TalentMatch AI is thinking</span>
                      <span className="flex items-center gap-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-600 animate-bounce [animation-delay:-0.3s]"></span>
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-600 animate-bounce [animation-delay:-0.15s]"></span>
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-600 animate-bounce"></span>
                      </span>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Input Area */}
              <div className="p-3 bg-white border-t border-slate-200/80">
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleSendMessage();
                  }}
                  className="flex items-end gap-2"
                >
                  <div className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-transparent transition">
                    <textarea
                      ref={textareaRef}
                      value={inputMessage}
                      onChange={(e) => setInputMessage(e.target.value)}
                      onKeyDown={handleKeyDown}
                      placeholder="Ask TalentMatch AI anything..."
                      rows={1}
                      className="w-full bg-transparent resize-none text-xs sm:text-[13px] text-slate-800 placeholder-slate-400 focus:outline-none max-h-24 leading-relaxed"
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={!inputMessage.trim() || isLoading}
                    className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-700 to-blue-600 text-white flex items-center justify-center shrink-0 shadow-md shadow-blue-500/20 hover:from-blue-800 hover:to-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition"
                    title="Send message"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </form>

                <div className="mt-2 flex items-center justify-between text-[10px] text-slate-400 px-1">
                  <span>Press Enter to send, Shift+Enter for new line</span>
                  <span className="flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-500"></span>
                    Verified Against Real DB
                  </span>
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </>
  );
};

