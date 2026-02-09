import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2, AlertCircle, CheckCircle2, Package, Wrench, RefreshCw, Calendar, PhoneCall, X, BarChart3, Clock, TrendingUp, Users } from 'lucide-react';

// API Configuration
const API_BASE = 'http://localhost:5000/api';

// Dr. Martens brand colors
const BRAND = {
  yellow: '#FFCC00',
  black: '#000000',
  darkGray: '#1a1a1a',
  lightGray: '#f5f5f5',
};

export default function DrMartensChatbot() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'bot',
      text: "Welcome to Dr. Martens Support! I'm here to help with orders, returns, repairs, and more. What can I assist you with today?",
      timestamp: new Date(),
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentCustomer, setCurrentCustomer] = useState(null);
  const [showKPIs, setShowKPIs] = useState(false);
  const [kpis, setKpis] = useState(null);
  const [actionInProgress, setActionInProgress] = useState(null);
  
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Fetch KPIs
  useEffect(() => {
    if (showKPIs && !kpis) {
      fetch(`${API_BASE}/kpis`)
        .then(res => res.json())
        .then(data => setKpis(data.kpis))
        .catch(err => console.error('Failed to fetch KPIs:', err));
    }
  }, [showKPIs, kpis]);

  // Send message to backend
  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      text: input,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = input;
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: currentInput,
          order_number: currentCustomer?.order_number,
          context: { customer: currentCustomer }
        }),
      });

      const data = await response.json();

      if (data.customer && !currentCustomer) {
        setCurrentCustomer(data.customer);
      }

      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        text: data.response,
        timestamp: new Date(),
        suggestions: data.suggestions,
        classification: data.classification,
        customer: data.customer,
        requiresEscalation: data.requires_escalation,
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        type: 'bot',
        text: "I'm having trouble connecting to our system. Please make sure the backend server is running on port 5000.",
        timestamp: new Date(),
        isError: true,
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  // Execute action (refund, repair, etc.)
  const executeAction = async (actionType, extraData = {}) => {
    if (!currentCustomer) return;
    
    setActionInProgress(actionType);

    try {
      const response = await fetch(`${API_BASE}/action/${actionType}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          order_number: currentCustomer.order_number,
          ...extraData,
        }),
      });

      const data = await response.json();

      const actionMessage = {
        id: Date.now(),
        type: 'bot',
        text: data.message,
        timestamp: new Date(),
        actionResult: data,
        isAction: true,
      };

      setMessages(prev => [...prev, actionMessage]);
    } catch (error) {
      console.error('Action error:', error);
    } finally {
      setActionInProgress(null);
    }
  };

  // Handle suggestion click
  const handleSuggestion = (suggestion) => {
    setInput(suggestion);
    setTimeout(() => {
      const fakeEvent = { key: 'Enter', shiftKey: false, preventDefault: () => {} };
      document.querySelector('input')?.dispatchEvent(new KeyboardEvent('keypress', { key: 'Enter' }));
    }, 100);
  };

  // Handle key press
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="h-screen flex flex-col" style={{ background: BRAND.lightGray, fontFamily: "'Helvetica Neue', Arial, sans-serif" }}>
      
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4" style={{ background: BRAND.black }}>
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-full flex items-center justify-center" style={{ background: BRAND.yellow }}>
            <span className="font-black text-lg" style={{ color: BRAND.black }}>DM</span>
          </div>
          <div>
            <h1 className="text-white font-bold text-lg tracking-tight">Dr. Martens Support</h1>
            <p className="text-gray-400 text-xs">AI-Powered Customer Service</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowKPIs(!showKPIs)}
            className="px-4 py-2 text-sm font-medium rounded-full flex items-center gap-2 transition-all"
            style={{ 
              background: showKPIs ? BRAND.yellow : 'transparent',
              color: showKPIs ? BRAND.black : 'white',
              border: `1px solid ${showKPIs ? BRAND.yellow : '#444'}`
            }}
          >
            <BarChart3 size={16} />
            KPIs
          </button>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        
        {/* Main Chat Area */}
        <main className="flex-1 flex flex-col">
          
          {/* Customer Context Bar */}
          {currentCustomer && (
            <div className="px-6 py-3 border-b flex items-center justify-between" style={{ background: 'white', borderColor: '#e5e5e5' }}>
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-full flex items-center justify-center" style={{ background: BRAND.yellow }}>
                  <User size={20} style={{ color: BRAND.black }} />
                </div>
                <div>
                  <p className="font-semibold text-sm">{currentCustomer.customer_name}</p>
                  <p className="text-xs text-gray-500">
                    Order: {currentCustomer.order_number} • {currentCustomer.product_name}
                  </p>
                </div>
                <span 
                  className="px-3 py-1 rounded-full text-xs font-medium"
                  style={{ 
                    background: currentCustomer.priority_level === 'critical' ? '#fecaca' : 
                               currentCustomer.priority_level === 'high' ? '#fef3c7' : '#e5e5e5',
                    color: currentCustomer.priority_level === 'critical' ? '#b91c1c' : 
                           currentCustomer.priority_level === 'high' ? '#b45309' : '#525252'
                  }}
                >
                  {currentCustomer.priority_level?.toUpperCase()} PRIORITY
                </span>
              </div>
              <button 
                onClick={() => setCurrentCustomer(null)}
                className="p-2 hover:bg-gray-100 rounded-full transition"
              >
                <X size={16} className="text-gray-400" />
              </button>
            </div>
          )}

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-3 ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {message.type === 'bot' && (
                  <div 
                    className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
                    style={{ background: BRAND.yellow }}
                  >
                    <Bot size={18} style={{ color: BRAND.black }} />
                  </div>
                )}
                
                <div className={`max-w-xl ${message.type === 'user' ? 'order-first' : ''}`}>
                  <div
                    className="px-4 py-3 rounded-2xl"
                    style={{
                      background: message.type === 'user' ? BRAND.black : 'white',
                      color: message.type === 'user' ? 'white' : BRAND.black,
                      border: message.type === 'bot' ? '1px solid #e5e5e5' : 'none',
                    }}
                  >
                    <p className="text-sm whitespace-pre-wrap">{message.text}</p>
                    
                    {/* Action Result */}
                    {message.actionResult && (
                      <div className="mt-3 p-3 rounded-lg" style={{ background: '#f0fdf4', border: '1px solid #bbf7d0' }}>
                        <div className="flex items-center gap-2 mb-2">
                          <CheckCircle2 size={16} className="text-green-600" />
                          <span className="text-sm font-medium text-green-800">Action Completed</span>
                        </div>
                        <div className="text-xs text-green-700 space-y-1">
                          {Object.entries(message.actionResult.details || {}).map(([key, value]) => (
                            <p key={key}><span className="font-medium">{key.replace(/_/g, ' ')}:</span> {String(value)}</p>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                  
                  {/* Suggestions */}
                  {message.suggestions && message.type === 'bot' && (
                    <div className="flex flex-wrap gap-2 mt-2">
                      {message.suggestions.map((suggestion, idx) => (
                        <button
                          key={idx}
                          onClick={() => {
                            setInput(suggestion);
                            setTimeout(sendMessage, 100);
                          }}
                          className="px-3 py-1.5 text-xs rounded-full transition-all hover:scale-105"
                          style={{ 
                            background: BRAND.yellow, 
                            color: BRAND.black,
                            fontWeight: 500 
                          }}
                        >
                          {suggestion}
                        </button>
                      ))}
                    </div>
                  )}
                  
                  <p className="text-xs text-gray-400 mt-1 px-1">
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>

                {message.type === 'user' && (
                  <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 bg-gray-200">
                    <User size={18} className="text-gray-600" />
                  </div>
                )}
              </div>
            ))}
            
            {/* Loading indicator */}
            {isLoading && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full flex items-center justify-center" style={{ background: BRAND.yellow }}>
                  <Bot size={18} style={{ color: BRAND.black }} />
                </div>
                <div className="px-4 py-3 rounded-2xl bg-white border border-gray-200">
                  <Loader2 size={20} className="animate-spin text-gray-400" />
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Actions (when customer is loaded) */}
          {currentCustomer && (
            <div className="px-6 py-3 border-t flex items-center gap-2 overflow-x-auto" style={{ background: '#fafafa', borderColor: '#e5e5e5' }}>
              <span className="text-xs text-gray-500 font-medium mr-2">Quick Actions:</span>
              <ActionButton 
                icon={RefreshCw} 
                label="Refund" 
                onClick={() => executeAction('refund')}
                loading={actionInProgress === 'refund'}
              />
              <ActionButton 
                icon={Wrench} 
                label="Repair" 
                onClick={() => executeAction('repair')}
                loading={actionInProgress === 'repair'}
              />
              <ActionButton 
                icon={Package} 
                label="Exchange" 
                onClick={() => executeAction('exchange')}
                loading={actionInProgress === 'exchange'}
              />
              <ActionButton 
                icon={Calendar} 
                label="Appointment" 
                onClick={() => executeAction('appointment')}
                loading={actionInProgress === 'appointment'}
              />
              <ActionButton 
                icon={PhoneCall} 
                label="Escalate" 
                onClick={() => executeAction('escalate', { reason: 'Agent-initiated escalation' })}
                loading={actionInProgress === 'escalate'}
                variant="danger"
              />
            </div>
          )}

          {/* Input Area */}
          <div className="px-6 py-4 border-t" style={{ background: 'white', borderColor: '#e5e5e5' }}>
            <div className="flex items-center gap-3">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your message or enter an order number (DM24...)..."
                className="flex-1 px-4 py-3 rounded-full border border-gray-200 focus:outline-none focus:border-gray-400 text-sm transition"
                disabled={isLoading}
              />
              <button
                onClick={sendMessage}
                disabled={!input.trim() || isLoading}
                className="w-12 h-12 rounded-full flex items-center justify-center transition-all hover:scale-105 disabled:opacity-50 disabled:hover:scale-100"
                style={{ background: BRAND.yellow }}
              >
                <Send size={20} style={{ color: BRAND.black }} />
              </button>
            </div>
            <p className="text-xs text-gray-400 text-center mt-2">
              Try: DM24210432, DM24165432, DM24276543, DM24398765
            </p>
          </div>
        </main>

        {/* KPI Sidebar */}
        {showKPIs && (
          <aside className="w-80 border-l overflow-y-auto p-4" style={{ background: 'white', borderColor: '#e5e5e5' }}>
            <h2 className="font-bold text-lg mb-4 flex items-center gap-2">
              <BarChart3 size={20} />
              Performance Dashboard
            </h2>
            
            {kpis ? (
              <div className="space-y-4">
                <KPICard 
                  icon={TrendingUp}
                  label="Auto-Resolution Rate"
                  value={`${kpis.auto_resolution_rate}%`}
                  subtext={`${kpis.auto_resolved} of ${kpis.total_conversations} conversations`}
                  color="#22c55e"
                />
                <KPICard 
                  icon={Clock}
                  label="Avg Handle Time"
                  value={`${kpis.avg_handle_time}s`}
                  subtext="Target: < 3 seconds"
                  color="#3b82f6"
                />
                <KPICard 
                  icon={AlertCircle}
                  label="Escalation Rate"
                  value={`${kpis.escalation_rate}%`}
                  subtext="Target: < 10%"
                  color="#f59e0b"
                />
                <KPICard 
                  icon={Users}
                  label="CSAT Score"
                  value={kpis.csat_score}
                  subtext="Out of 5.0"
                  color="#8b5cf6"
                />
                
                <div className="mt-6 p-4 rounded-lg" style={{ background: BRAND.lightGray }}>
                  <h3 className="font-semibold text-sm mb-3">Today's Activity</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Conversations</span>
                      <span className="font-medium">{kpis.today.conversations}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Resolved</span>
                      <span className="font-medium text-green-600">{kpis.today.resolved}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Pending</span>
                      <span className="font-medium text-amber-600">{kpis.today.pending}</span>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-40">
                <Loader2 className="animate-spin text-gray-400" />
              </div>
            )}
          </aside>
        )}
      </div>
    </div>
  );
}

// Action Button Component
function ActionButton({ icon: Icon, label, onClick, loading, variant }) {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      className="flex items-center gap-2 px-3 py-2 rounded-full text-xs font-medium transition-all hover:scale-105 disabled:opacity-50"
      style={{
        background: variant === 'danger' ? '#fef2f2' : '#f5f5f5',
        color: variant === 'danger' ? '#b91c1c' : '#525252',
        border: `1px solid ${variant === 'danger' ? '#fecaca' : '#e5e5e5'}`,
      }}
    >
      {loading ? <Loader2 size={14} className="animate-spin" /> : <Icon size={14} />}
      {label}
    </button>
  );
}

// KPI Card Component
function KPICard({ icon: Icon, label, value, subtext, color }) {
  return (
    <div className="p-4 rounded-lg border" style={{ borderColor: '#e5e5e5' }}>
      <div className="flex items-center gap-3">
        <div 
          className="w-10 h-10 rounded-lg flex items-center justify-center"
          style={{ background: `${color}15` }}
        >
          <Icon size={20} style={{ color }} />
        </div>
        <div>
          <p className="text-2xl font-bold" style={{ color }}>{value}</p>
          <p className="text-xs text-gray-500">{label}</p>
        </div>
      </div>
      <p className="text-xs text-gray-400 mt-2">{subtext}</p>
    </div>
  );
}
