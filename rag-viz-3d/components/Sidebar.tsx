import React, { useState } from 'react';
import { RagStep, RagData, STEPS, AIProvider } from '../types';
import { ChevronRight, ChevronLeft, Box, Database, Cpu, MessageSquare, FileText, Play, RotateCcw, Loader2, FileUp, Scissors, Layers, Sparkles } from 'lucide-react';

interface SidebarProps {
  currentStep: RagStep;
  setStep: (step: RagStep) => void;
  data: RagData;
  onGenerateScenario: (topic: string, provider?: AIProvider) => void;
  isGenerating: boolean;
  provider: AIProvider;
  setProvider: (provider: AIProvider) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentStep, setStep, data, onGenerateScenario, isGenerating, provider, setProvider }) => {
  const [customTopic, setCustomTopic] = useState("");

  const currentStepIndex = STEPS.findIndex(s => s.id === currentStep);
  const currentInfo = STEPS.find(s => s.id === currentStep) || STEPS[0];

  const handleNext = () => {
    if (currentStepIndex < STEPS.length - 1) {
      setStep(STEPS[currentStepIndex + 1].id);
    } else {
        setStep(RagStep.UPLOAD); // Loop back to upload
    }
  };

  const handlePrev = () => {
    if (currentStepIndex > 0) {
      setStep(STEPS[currentStepIndex - 1].id);
    }
  };

  const handleSubmitTopic = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmedTopic = customTopic.trim();
    if (trimmedTopic && trimmedTopic.length >= 2 && trimmedTopic.length <= 100) {
        onGenerateScenario(trimmedTopic, provider);
        setCustomTopic("");
    }
  };

  // Helper icons for step visualization
  const getStepIcon = (step: RagStep) => {
      switch(step) {
          case RagStep.UPLOAD: return <FileUp className="w-4 h-4" />;
          case RagStep.CHUNKING: return <Scissors className="w-4 h-4" />;
          case RagStep.INDEXING: return <Layers className="w-4 h-4" />;
          default: return null;
      }
  }

  return (
    <div className="w-full md:w-[400px] h-full bg-white border-r border-slate-200 flex flex-col shadow-xl z-10">
      {/* Header */}
      <div className="p-6 border-b border-slate-100 bg-slate-50">
        <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <Database className="w-6 h-6 text-blue-600" />
            RAG Viz
        </h1>
        <p className="text-sm text-slate-500 mt-1">Interactive Retrieval Augmented Generation</p>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-8">
        
        {/* Progress Bar */}
        <div className="flex items-center justify-between mb-4">
            {STEPS.map((step, idx) => (
                <div key={step.id} className={`h-2 flex-1 mx-0.5 rounded-full transition-colors duration-300 ${idx <= currentStepIndex ? 'bg-blue-500' : 'bg-slate-200'}`} title={step.title} />
            ))}
        </div>

        {/* Step Info */}
        <div className="space-y-4">
            <div className="flex items-center gap-3">
                <span className="text-xs font-bold uppercase tracking-wider text-blue-600 bg-blue-50 px-2 py-1 rounded flex items-center gap-1">
                    {getStepIcon(currentStep)}
                    Step {currentStepIndex + 1} / {STEPS.length}
                </span>
                <h2 className="text-xl font-bold text-slate-900">{currentInfo.title}</h2>
            </div>
            <p className="text-slate-600 leading-relaxed">
                {currentInfo.description}
            </p>
        </div>

        {/* Contextual Data View */}
        <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 space-y-3">
            <h3 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                <Cpu className="w-4 h-4" /> System State
            </h3>
            
            {currentStep === RagStep.UPLOAD && (
                <div className="text-sm flex items-center gap-3 p-3 bg-white rounded border border-slate-200">
                    <FileText className="w-8 h-8 text-slate-400" />
                    <div>
                        <p className="font-medium text-slate-700">Knowledge_Base.pdf</p>
                        <p className="text-xs text-slate-400">Uploading... 100%</p>
                    </div>
                </div>
            )}

            {currentStep === RagStep.CHUNKING && (
                <div className="text-sm space-y-2">
                    <p className="text-slate-500">Splitting document into chunks:</p>
                    <div className="grid grid-cols-2 gap-2">
                        {[1,2,3,4].map(i => (
                            <div key={i} className="h-6 bg-white border border-slate-200 rounded animate-pulse" />
                        ))}
                    </div>
                </div>
            )}

             {currentStep === RagStep.INDEXING && (
                <div className="text-sm space-y-2">
                    <p className="text-slate-500">Embedding chunks & Storing:</p>
                    <div className="font-mono text-xs bg-slate-900 text-green-400 p-2 rounded overflow-hidden">
                        Chunk[0] -&gt; [0.11, 0.94, ...] -&gt; DB<br/>
                        Chunk[1] -&gt; [0.42, 0.12, ...] -&gt; DB<br/>
                        ...
                    </div>
                </div>
            )}

            {currentStep === RagStep.INPUT && (
                <div className="text-sm">
                    <p className="text-slate-500 mb-1">User Query:</p>
                    <div className="p-3 bg-white rounded border border-slate-200 text-slate-800 italic">
                        "{data.userQuery}"
                    </div>
                </div>
            )}

            {currentStep === RagStep.EMBEDDING && (
                <div className="text-sm space-y-2">
                    <p className="text-slate-500">Converting query to vector...</p>
                    <div className="font-mono text-xs bg-slate-900 text-green-400 p-2 rounded overflow-hidden">
                        Query -&gt; [0.128, -0.542, 0.991, 0.004, ...]
                    </div>
                </div>
            )}

            {currentStep === RagStep.RETRIEVAL && (
                <div className="text-sm space-y-2">
                     <p className="text-slate-500">Searching knowledge base...</p>
                     <div className="space-y-1">
                        {data.retrievedIndices.map(idx => (
                            <div key={idx} className="flex items-start gap-2 p-2 bg-green-50 border border-green-200 rounded text-green-800 text-xs">
                                <FileText className="w-3 h-3 mt-0.5 flex-shrink-0" />
                                <span className="line-clamp-2">{data.documents[idx]}</span>
                            </div>
                        ))}
                     </div>
                </div>
            )}

            {(currentStep === RagStep.AUGMENTATION) && (
                <div className="text-sm space-y-2">
                    <p className="text-slate-500">Constructing augmented prompt:</p>
                    <div className="p-2 bg-yellow-50 border border-yellow-200 rounded text-slate-800 text-xs whitespace-pre-wrap h-32 overflow-y-auto font-mono">
                        {(() => {
                            const doc1 = data.retrievedIndices.length > 0 && data.retrievedIndices[0] < data.documents.length
                                ? data.documents[data.retrievedIndices[0]].substring(0, 30)
                                : 'Document 1';
                            const doc2 = data.retrievedIndices.length > 1 && data.retrievedIndices[1] < data.documents.length
                                ? data.documents[data.retrievedIndices[1]].substring(0, 30)
                                : 'Document 2';
                            return `SYSTEM: Answer based on:\n- ${doc1}...\n- ${doc2}...\n\nUSER: ${data.userQuery}`;
                        })()}
                    </div>
                </div>
            )}

             {(currentStep === RagStep.GENERATION || currentStep === RagStep.COMPLETE) && (
                <div className="text-sm space-y-2">
                    <p className="text-slate-500">LLM Output:</p>
                    <div className="p-3 bg-blue-50 border border-blue-200 rounded text-slate-800">
                        {data.generatedAnswer}
                    </div>
                </div>
            )}

        </div>

        {/* AI Provider Selection */}
        <div className="pt-6 border-t border-slate-200">
            <h3 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
                <Sparkles className="w-4 h-4" /> AI Provider
            </h3>
            <div className="grid grid-cols-3 gap-2 mb-4">
                <button
                    type="button"
                    onClick={() => setProvider(AIProvider.GEMINI)}
                    disabled={isGenerating}
                    className={`px-3 py-2 text-xs rounded-lg border transition-colors ${
                        provider === AIProvider.GEMINI
                            ? 'bg-blue-50 border-blue-500 text-blue-700 font-medium'
                            : 'bg-white border-slate-300 text-slate-600 hover:bg-slate-50'
                    } disabled:opacity-50`}
                >
                    Gemini
                </button>
                <button
                    type="button"
                    onClick={() => setProvider(AIProvider.ANTHROPIC)}
                    disabled={isGenerating}
                    className={`px-3 py-2 text-xs rounded-lg border transition-colors ${
                        provider === AIProvider.ANTHROPIC
                            ? 'bg-orange-50 border-orange-500 text-orange-700 font-medium'
                            : 'bg-white border-slate-300 text-slate-600 hover:bg-slate-50'
                    } disabled:opacity-50`}
                >
                    Claude
                </button>
                <button
                    type="button"
                    onClick={() => setProvider(AIProvider.AZURE_OPENAI)}
                    disabled={isGenerating}
                    className={`px-3 py-2 text-xs rounded-lg border transition-colors ${
                        provider === AIProvider.AZURE_OPENAI
                            ? 'bg-green-50 border-green-500 text-green-700 font-medium'
                            : 'bg-white border-slate-300 text-slate-600 hover:bg-slate-50'
                    } disabled:opacity-50`}
                >
                    Azure
                </button>
            </div>
        </div>

        {/* Custom Scenario Generator */}
        <div className="pt-4 border-t border-slate-200">
            <h3 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
                Try a new topic
            </h3>
            <form onSubmit={handleSubmitTopic} className="flex gap-2">
                <input 
                    type="text" 
                    value={customTopic}
                    onChange={(e) => setCustomTopic(e.target.value)}
                    placeholder="e.g., Photosynthesis, Ancient Rome..."
                    className="flex-1 px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    disabled={isGenerating}
                />
                <button 
                    type="submit"
                    disabled={isGenerating || !customTopic.trim()}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 flex items-center justify-center min-w-[40px]"
                >
                    {isGenerating ? <Loader2 className="w-4 h-4 animate-spin" /> : <MessageSquare className="w-4 h-4" />}
                </button>
            </form>
            {isGenerating && <p className="text-xs text-blue-500 mt-2 animate-pulse">Generating scenario with {provider}...</p>}
        </div>

      </div>

      {/* Footer Controls */}
      <div className="p-6 border-t border-slate-200 bg-slate-50 flex justify-between items-center">
        <button 
            onClick={handlePrev} 
            disabled={currentStepIndex === 0}
            className="p-2 hover:bg-slate-200 rounded-full disabled:opacity-30 transition-colors"
        >
            <ChevronLeft className="w-6 h-6 text-slate-700" />
        </button>

        <div className="text-sm font-medium text-slate-500">
            {currentStep === RagStep.COMPLETE ? "Finished" : "Navigate"}
        </div>

        {currentStepIndex === STEPS.length - 1 ? (
             <button 
                onClick={() => setStep(RagStep.UPLOAD)} 
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-full font-medium transition-colors"
            >
                <RotateCcw className="w-4 h-4" /> Restart
            </button>
        ) : (
            <button 
                onClick={handleNext} 
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-full font-medium transition-colors shadow-lg shadow-blue-200"
            >
                Next <ChevronRight className="w-4 h-4" />
            </button>
        )}
      </div>
    </div>
  );
};