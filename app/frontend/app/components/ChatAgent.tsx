'use client';

import { useState, useRef, useEffect } from 'react';
import { useHealthScan } from '../context/HealthScanContext';
import { API_BASE_URL } from '../lib/api';
import type { PrescriptionInfo } from '../lib/types';
import MedicalDisclaimer from './MedicalDisclaimer';
import TrustIndicators from './TrustIndicators';
import PrescriptionCard from './PrescriptionCard';
import EmptyState from './EmptyState';
import MedicalLoading from './MedicalLoading';
import MedicalError from './MedicalError';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  image?: string; // Base64 preview
  timestamp: Date;
  prescriptionData?: PrescriptionInfo; // For prescription cards
}

export default function ChatAgent() {
  const {
    prescriptionData,
    setPrescriptionData,
    interactionResult,
    setInteractionResult,
    dietData,
    setDietData,
  } = useHealthScan();

  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: `🏥 **Welcome to HealthScan - Your AI Healthcare Assistant**

I help you understand your medications and health information through three key features:

📋 **1. Prescription Extraction**
   → Upload prescription images to extract medication details

💊 **2. Drug Interaction Checking**  
   → Upload multiple prescriptions to check for interactions

🥗 **3. Diet Recommendations**
   → Get personalized diet plans based on your medical condition

**How to use:**
1. Upload a prescription image (or multiple for interaction checking)
2. I'll analyze and explain what I find
3. Ask me questions about your medications, interactions, or diet
4. I'll guide you through the HealthScan workflow

⚠️ **Important**: I'm a healthcare assistant, not a replacement for professional medical advice. Always consult your doctor for medical decisions.

What would you like to start with?`,
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [images, setImages] = useState<File[]>([]);
  const [imagePreviews, setImagePreviews] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Auto-check interactions if multiple images uploaded (after processing)
  // This will be triggered after prescription extraction completes

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) {
      setImages(prev => [...prev, ...files]);
      const newPreviews = files.map(file => {
        const reader = new FileReader();
        return new Promise<string>((resolve) => {
          reader.onloadend = () => resolve(reader.result as string);
          reader.readAsDataURL(file);
        });
      });
      Promise.all(newPreviews).then(newPrevs => {
        setImagePreviews(prev => [...prev, ...newPrevs]);
      });
    }
  };

  const checkInteractionsAuto = async () => {
    if (images.length < 2) return;

    setLoading(true);

    try {
      const formData = new FormData();
      images.forEach((file) => {
        formData.append('files', file);
      });

      const response = await fetch(`${API_BASE_URL}/check-prescription-interactions`, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        setInteractionResult({
          warnings: data.warnings || data.interactions || { major: [], moderate: [], minor: [] },
          prescription_details: data.prescription_details || data.prescriptions || [],
        });

        const hasInteractions = data.has_interactions;
        const majorCount = (data.interactions?.major?.length || data.warnings?.major?.length || 0);
        const moderateCount = (data.interactions?.moderate?.length || data.warnings?.moderate?.length || 0);
        const minorCount = (data.interactions?.minor?.length || data.warnings?.minor?.length || 0);

        let message = `💊 **Drug Interaction Analysis Complete**\n\n`;
        
        if (hasInteractions) {
          message += `⚠️ **Interactions Found:**\n`;
          message += `- Major: ${majorCount}\n`;
          message += `- Moderate: ${moderateCount}\n`;
          message += `- Minor: ${minorCount}\n\n`;
          message += `**Important**: Please review these interactions carefully. For major interactions, consult your doctor immediately.\n\n`;
        } else {
          message += `✅ **No Drug Interactions Detected**\n\n`;
          message += `Your medications appear to be safe to take together. However, always consult your healthcare provider for final confirmation.\n\n`;
        }
        
        message += `💡 **Next Steps:**\n`;
        message += `1️⃣ Ask me to explain specific interactions in detail\n`;
        message += `2️⃣ Get diet recommendations based on your medications\n`;
        message += `3️⃣ Ask questions about your prescriptions\n\n`;
        message += `What would you like to know?`;

        addMessage('assistant', message);
      } else {
        addMessage('assistant', '❌ Failed to check interactions. Please try uploading the images again.');
      }
    } catch (err) {
      addMessage('assistant', '❌ Failed to check interactions. Please check your connection and try again.');
    } finally {
      setLoading(false);
    }
  };

  const addMessage = (role: 'user' | 'assistant' | 'system', content: string, image?: string, prescriptionData?: PrescriptionInfo) => {
    // Generate unique ID using timestamp + random to avoid duplicates
    const uniqueId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const newMessage: Message = {
      id: uniqueId,
      role,
      content,
      image,
      prescriptionData,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, newMessage]);
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() && images.length === 0) return;

    const userMessage = input.trim();
    if (userMessage) {
      addMessage('user', userMessage);
      setInput('');
    }

    if (images.length > 0) {
      // Show uploaded images in chat
      images.forEach((img, idx) => {
        if (imagePreviews[idx]) {
          addMessage('user', `📷 Uploaded image ${idx + 1}`, imagePreviews[idx]);
        }
      });
    }

    setLoading(true);

    try {
      // If images uploaded, process them
      if (images.length > 0) {
        // Process first image for prescription extraction
        const firstImage = images[0];
        addMessage('assistant', '🔍 Analyzing your image...');

        const formData = new FormData();
        formData.append('file', firstImage);
        formData.append('stream', 'true');

        const response = await fetch(`${API_BASE_URL}/extract-prescription`, {
          method: 'POST',
          body: formData,
        });

        if (response.ok) {
          const contentType = response.headers.get('content-type');
          if (contentType?.includes('text/event-stream')) {
            // Handle streaming
            const reader = response.body?.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            if (reader) {
              while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                for (const line of lines) {
                  if (line.startsWith('data: ')) {
                    try {
                      const data = JSON.parse(line.slice(6));
                      if (data.step === 'complete' && data.prescription_info) {
                        const info = data.prescription_info;
                        setPrescriptionData({
                          medications: [{
                            medication_name: info.medication_name || '',
                            dosage: info.dosage,
                            frequency: info.frequency,
                            quantity: info.quantity,
                            refills: info.refills,
                            instructions: info.instructions,
                          }],
                          prescriber: info.prescriber,
                          date: info.date,
                        });

                        // Check for errors in the response
                        if (info.medication_name === 'Unknown' && info.instructions?.includes('Error extracting')) {
                          const errorMsg = `**Prescription Extraction Failed**\n\n${info.instructions}\n\nPlease try:\n- Using a clearer, well-lit image\n- Ensuring the prescription text is visible\n- Uploading a different image format (JPG, PNG)\n\nIf the problem persists, please contact support or consult your healthcare provider.`;
                          addMessage('assistant', errorMsg);
                          setLoading(false);
                          return;
                        }

                        // Generate healthcare-focused explanation with prescription card
                        let explanation = `📋 **Prescription Extracted Successfully**\n\n`;
                        
                        // Auto-check interactions if multiple images
                        if (images.length > 1) {
                          explanation += `🔍 **Multiple Prescriptions Detected**\n`;
                          explanation += `I see you uploaded ${images.length} prescription images. Let me automatically check for drug interactions...\n\n`;
                          addMessage('assistant', explanation, undefined, info);
                          // Trigger auto-check after message is added
                          setTimeout(() => checkInteractionsAuto(), 500);
                        } else {
                          explanation += `💡 **Next Steps in HealthScan Workflow:**\n\n`;
                          explanation += `1️⃣ **Check Drug Interactions** - Upload additional prescriptions to check for interactions\n`;
                          explanation += `2️⃣ **Get Diet Recommendations** - I can provide personalized diet advice based on this medication\n`;
                          explanation += `3️⃣ **Ask Questions** - Ask me anything about this medication, side effects, or dietary considerations\n\n`;
                          explanation += `What would you like to do next?`;
                          addMessage('assistant', explanation, undefined, info);
                        }
                      }
                    } catch (e) {
                      // Ignore parse errors
                    }
                  }
                }
              }
            }
          } else {
            const result = await response.json();
            if (result.prescription_info) {
              const info = result.prescription_info;
              setPrescriptionData({
                medications: [{
                  medication_name: info.medication_name || '',
                  dosage: info.dosage,
                  frequency: info.frequency,
                  quantity: info.quantity,
                  refills: info.refills,
                  instructions: info.instructions,
                }],
                prescriber: info.prescriber,
                date: info.date,
              });

              let explanation = `📋 **Prescription Extracted Successfully**\n\n`;
              
              // Auto-check interactions if multiple images
              if (images.length > 1) {
                explanation += `🔍 **Multiple Prescriptions Detected**\n`;
                explanation += `I see you uploaded ${images.length} prescription images. Let me automatically check for drug interactions...\n\n`;
                addMessage('assistant', explanation, undefined, info);
                // Trigger auto-check after message is added
                setTimeout(() => checkInteractionsAuto(), 500);
              } else {
                explanation += `💡 **Next Steps in HealthScan Workflow:**\n\n`;
                explanation += `1️⃣ **Check Drug Interactions** - Upload additional prescriptions\n`;
                explanation += `2️⃣ **Get Diet Recommendations** - Personalized diet advice\n`;
                explanation += `3️⃣ **Ask Questions** - About this medication or health concerns\n\n`;
                explanation += `What would you like to do next?`;
                addMessage('assistant', explanation, undefined, info);
              }
            }
          }
        }
      }

      // Handle text questions
      if (userMessage) {
        // Send to conversational endpoint
        const chatResponse = await fetch(`${API_BASE_URL}/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: userMessage,
            context: {
              prescription_data: prescriptionData,
              interaction_result: interactionResult,
              diet_data: dietData,
            },
          }),
        });

        if (chatResponse.ok) {
          const data = await chatResponse.json();
          addMessage('assistant', data.response || data.message);
        } else {
          addMessage('assistant', 'I understand your question. Let me help you with that based on the information I have.');
        }
      }

      // Clear images after processing
      setImages([]);
      setImagePreviews([]);
      if (fileInputRef.current) fileInputRef.current.value = '';

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An unexpected error occurred';
      let userFriendlyMessage = '❌ **I encountered an error processing your request.**\n\n';
      
      if (errorMessage.includes('Failed to fetch') || errorMessage.includes('Network')) {
        userFriendlyMessage += '**Network Error:** Please check your internet connection and try again.\n\n';
        userFriendlyMessage += 'If the problem persists, this may be a temporary server issue. Please try again in a few moments.';
      } else if (errorMessage.includes('timeout')) {
        userFriendlyMessage += '**Request Timeout:** The request took too long to process.\n\n';
        userFriendlyMessage += 'Please try again with a smaller image or check your connection speed.';
      } else {
        userFriendlyMessage += '**What to do:**\n';
        userFriendlyMessage += '1. Try uploading the image again\n';
        userFriendlyMessage += '2. Ensure the image is clear and readable\n';
        userFriendlyMessage += '3. If the problem continues, contact support\n\n';
        userFriendlyMessage += '**For urgent medical questions, please consult your healthcare provider directly.**';
      }
      
      addMessage('assistant', userFriendlyMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-64px)] md:h-[calc(100vh-80px)] text-slate-800 relative overflow-hidden" role="main" aria-label="HealthScan Chat Assistant">
      {/* Medical Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-sky-50 via-blue-50 to-cyan-50">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(2,132,199,0.05),transparent_50%)]"></div>
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_20%,rgba(6,182,212,0.05),transparent_50%)]"></div>
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_80%,rgba(5,150,105,0.03),transparent_50%)]"></div>
      </div>

      {/* HealthScan Header - Medical Theme */}
      <div className="relative glass-strong border-b border-blue-200/50 px-4 py-3 md:py-4 backdrop-blur-xl z-10 flex-shrink-0">
        <div className="max-w-5xl mx-auto">
          <div className="flex items-center gap-3 md:gap-4 mb-2 md:mb-3">
            <div className="w-10 h-10 md:w-12 md:h-12 rounded-xl md:rounded-2xl bg-gradient-to-br from-blue-500 via-cyan-500 to-teal-500 flex items-center justify-center text-xl md:text-2xl font-bold shadow-lg glow-teal flex-shrink-0">
              🏥
            </div>
            <div className="flex-1 min-w-0">
              <h1 className="text-xl md:text-2xl font-bold gradient-text mb-0.5 truncate">HealthScan</h1>
              <p className="text-xs text-slate-600 font-medium line-clamp-1">AI Healthcare Assistant • Prescription Extraction • Drug Interactions • Diet Recommendations</p>
            </div>
          </div>
          <div className="mt-2">
            <TrustIndicators />
          </div>
        </div>
      </div>

      {/* Chat Messages - Medical Theme */}
      <div className="relative flex-1 overflow-y-auto p-3 md:p-4 lg:p-6 z-10 min-h-0" role="log" aria-live="polite" aria-label="Chat messages">
        <div className="max-w-5xl mx-auto space-y-4">
          {messages.map((msg, idx) => (
            <div
              key={msg.id}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} message-enter`}
              style={{ animationDelay: `${idx * 0.1}s` }}
            >
              <div
                className={`max-w-[90%] sm:max-w-[85%] md:max-w-[75%] rounded-xl md:rounded-2xl p-4 md:p-5 shadow-md ${
                  msg.role === 'user'
                    ? 'bg-gradient-to-br from-blue-500 to-cyan-500 text-white shadow-blue-200/40'
                    : 'medical-card bg-white text-slate-800 border-blue-200 shadow-blue-50'
                }`}
              >
              {msg.image && (
                <div className="mb-3 rounded-xl overflow-hidden border-2 border-blue-100 shadow-md">
                  <img src={msg.image} alt="Uploaded prescription" className="max-w-xs w-full h-auto" />
                </div>
              )}
              {msg.prescriptionData && (
                <div className="mb-4">
                  <PrescriptionCard prescription={msg.prescriptionData} />
                </div>
              )}
              <div className="whitespace-pre-wrap leading-relaxed text-sm md:text-base prose prose-sm max-w-none">
                {msg.content}
              </div>
              <div className={`text-xs mt-3 font-medium opacity-70 ${msg.role === 'user' ? 'text-blue-50' : 'text-slate-500'}`}>
                {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </div>
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <MedicalLoading variant="prescription" message="Analyzing your prescription..." />
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Image Preview - Medical Theme */}
      {images.length > 0 && (
        <div className="relative glass-strong border-t border-blue-200/50 px-3 md:px-4 py-2 md:py-3 backdrop-blur-xl z-10 flex-shrink-0">
          <div className="max-w-5xl mx-auto">
            <p className="text-xs text-slate-600 font-semibold mb-2 uppercase tracking-wide">Prescription Images</p>
            <div className="flex gap-2 md:gap-3 overflow-x-auto pb-2 scrollbar-thin">
              {imagePreviews.map((preview, idx) => (
                <div key={idx} className="relative flex-shrink-0 group">
                  <div className="relative w-16 h-16 md:w-20 md:h-20 lg:w-24 lg:h-24 rounded-lg md:rounded-xl overflow-hidden border-2 border-blue-200 group-hover:border-blue-400 transition-all shadow-md medical-card">
                    <img src={preview} alt={`Prescription ${idx + 1}`} className="w-full h-full object-cover" />
                  </div>
                  <button
                    onClick={() => {
                      setImages(prev => prev.filter((_, i) => i !== idx));
                      setImagePreviews(prev => prev.filter((_, i) => i !== idx));
                    }}
                    className="absolute -top-1 -right-1 md:-top-2 md:-right-2 bg-red-500 hover:bg-red-600 rounded-full w-5 h-5 md:w-6 md:h-6 flex items-center justify-center text-xs font-bold shadow-lg transition-all hover:scale-110 text-white"
                    aria-label="Remove image"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Quick Actions - Medical Theme */}
      {images.length === 0 && messages.length <= 1 && (
        <div className="relative px-3 md:px-4 pb-2 md:pb-3 z-10 flex-shrink-0">
          <div className="max-w-5xl mx-auto">
            <p className="text-xs text-slate-500 mb-2 font-semibold uppercase tracking-wider">Quick Actions</p>
            <div className="flex gap-2 md:gap-3 flex-wrap">
              <button
                onClick={() => fileInputRef.current?.click()}
                className="px-4 md:px-5 py-2 md:py-2.5 rounded-lg md:rounded-xl text-xs md:text-sm font-semibold hover:shadow-xl transition-all flex items-center gap-2 bg-gradient-to-r from-blue-500 to-cyan-500 text-white shadow-lg hover:from-blue-600 hover:to-cyan-600 transform hover:-translate-y-0.5"
              >
                <span className="text-base md:text-lg">📋</span>
                <span className="hidden sm:inline">Upload Prescription</span>
                <span className="sm:hidden">Upload</span>
              </button>
              <button
                onClick={() => {
                  setInput("What can HealthScan help me with?");
                }}
                className="medical-card px-4 md:px-5 py-2 md:py-2.5 rounded-lg md:rounded-xl text-xs md:text-sm font-semibold hover:shadow-lg transition-all flex items-center gap-2 bg-white text-blue-600 border-blue-200 hover:border-blue-400 hover:bg-blue-50"
              >
                <span className="text-base md:text-lg">💡</span>
                <span className="hidden sm:inline">Learn More</span>
                <span className="sm:hidden">Learn</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Input Area - Medical Theme */}
      <div className="relative glass-strong border-t border-blue-200/50 p-3 md:p-4 backdrop-blur-xl z-10 flex-shrink-0">
        <form onSubmit={handleSend} className="flex gap-2 md:gap-3 max-w-5xl mx-auto">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            multiple
            onChange={handleFileSelect}
            className="hidden"
            id="file-input"
          />
          <label
            htmlFor="file-input"
            className="px-3 md:px-4 py-2.5 md:py-3 medical-card rounded-lg md:rounded-xl cursor-pointer flex items-center justify-center hover:shadow-lg transition-all bg-white border-blue-200 hover:border-blue-400 min-w-[44px] md:min-w-[50px] text-blue-600 hover:text-blue-700 flex-shrink-0"
            title="Upload prescription images"
          >
            <span className="text-lg md:text-xl">📷</span>
          </label>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about medications, interactions, diet..."
            className="flex-1 medical-card rounded-lg md:rounded-xl px-3 md:px-4 lg:px-5 py-2.5 md:py-3 text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 border border-blue-200 focus:border-blue-400 transition-all text-sm md:text-base bg-white min-w-0"
            disabled={loading}
            aria-label="Type your health question or message"
            aria-describedby="input-help"
          />
          <span id="input-help" className="sr-only">Enter your health questions or upload prescription images</span>
          <button
            type="submit"
            disabled={loading || (!input.trim() && images.length === 0)}
            className="px-4 md:px-6 lg:px-8 py-2.5 md:py-3 btn-primary rounded-lg md:rounded-xl font-semibold disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:transform-none flex items-center gap-1 md:gap-2 min-w-[80px] md:min-w-[100px] justify-center text-white text-sm md:text-base flex-shrink-0"
          >
            {loading ? (
              <>
                <div className="spinner w-4 h-4 border-2 border-white border-t-transparent"></div>
                <span className="hidden md:inline">Sending...</span>
              </>
            ) : (
              <>
                <span className="hidden sm:inline">Send</span>
                <span className="sm:hidden">→</span>
                <span className="hidden sm:inline text-lg">→</span>
              </>
            )}
          </button>
        </form>
        
        {/* Medical Disclaimer */}
        <div className="px-3 md:px-4 pt-2 pb-1">
          <MedicalDisclaimer variant="compact" />
        </div>
      </div>
    </div>
  );
}

