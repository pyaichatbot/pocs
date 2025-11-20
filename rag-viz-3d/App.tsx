import React, { useState } from 'react';
import { Scene3D } from './components/Scene3D';
import { Sidebar } from './components/Sidebar';
import { RagStep, RagData, AIProvider } from './types';
import { generateRagScenario } from './services/aiService';

const INITIAL_DATA: RagData = {
  topic: "Black Holes",
  userQuery: "What happens at the event horizon?",
  documents: [
    "Black holes are regions of spacetime where gravity is so strong that nothing can escape.",
    "The event horizon is the boundary beyond which events cannot affect an observer.",
    "Singularities are at the center of black holes.",
    "Stephen Hawking predicted black holes emit radiation.",
    "Supermassive black holes exist at galaxy centers.",
    "Time dilation occurs near the event horizon due to strong gravity.",
    "Spaghettification stretches objects falling into a black hole.",
    "Interstellar portrayed a black hole named Gargantua."
  ],
  retrievedIndices: [1, 5, 6],
  generatedAnswer: "At the event horizon, gravity is so intense that nothing, not even light, can escape. Time dilation becomes extreme, effectively stopping time for an outside observer. Objects crossing it may undergo spaghettification."
};

export default function App() {
  const [step, setStep] = useState<RagStep>(RagStep.UPLOAD);
  const [data, setData] = useState<RagData>(INITIAL_DATA);
  const [isGenerating, setIsGenerating] = useState(false);
  // Default to Anthropic since user has it configured
  const [provider, setProvider] = useState<AIProvider>(AIProvider.ANTHROPIC);

  const handleGenerateScenario = async (topic: string, selectedProvider?: AIProvider) => {
    setIsGenerating(true);
    // Reset to start
    setStep(RagStep.UPLOAD);
    
    try {
        const newData = await generateRagScenario(topic, selectedProvider || provider);
        setData(newData);
    } catch (e) {
        console.error("Failed to generate", e);
        alert(`Failed to generate scenario. Check API key for ${selectedProvider || provider}.`);
    } finally {
        setIsGenerating(false);
    }
  };

  return (
    <div className="flex flex-col md:flex-row w-full h-screen overflow-hidden">
      {/* Left Sidebar (Text & Controls) */}
      <Sidebar 
        currentStep={step} 
        setStep={setStep} 
        data={data} 
        onGenerateScenario={handleGenerateScenario}
        isGenerating={isGenerating}
        provider={provider}
        setProvider={setProvider}
      />

      {/* Right Main Area (3D Visualization) */}
      <div className="flex-1 relative bg-slate-100">
        <Scene3D currentStep={step} data={data} />
        
        {/* Overlay Instructions for Interaction */}
        <div className="absolute top-4 right-4 bg-white/80 backdrop-blur-sm p-3 rounded-lg shadow-sm border border-slate-200 text-xs text-slate-500 pointer-events-none">
           <p>🖱️ Drag to rotate view</p>
           <p>🖱️ Scroll to zoom</p>
           <p>👆 Hover over nodes for details</p>
        </div>
      </div>
    </div>
  );
}