import { GoogleGenAI, Type } from "@google/genai";
import Anthropic from "@anthropic-ai/sdk";
import { RagData, AIProvider } from "../types";

const DEFAULT_DATA: RagData = {
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
  generatedAnswer: "At the event horizon, gravity is so intense that nothing, not even light, can escape. Time dilation becomes extreme, effectively stopping time for an outside observer looking at an object falling in. Objects crossing it may eventually undergo spaghettification."
};

const SYSTEM_PROMPT = `Create a simplified RAG (Retrieval Augmented Generation) scenario about the topic provided.
I need a user query, a list of 8 short factual snippets (documents) representing a knowledge base, 
identification of which 3 indices (0-7) are most relevant to the query, and a final short answer.

Return ONLY valid JSON in this exact format:
{
  "userQuery": "A simple question a user might ask about the topic",
  "documents": ["8 short facts about the topic"],
  "retrievedIndices": [0, 1, 2],
  "generatedAnswer": "A concise answer based on the retrieved documents"
}`;

function validateResponse(data: any): data is RagData {
  return (
    data &&
    typeof data.userQuery === 'string' &&
    Array.isArray(data.documents) &&
    data.documents.length === 8 &&
    Array.isArray(data.retrievedIndices) &&
    typeof data.generatedAnswer === 'string'
  );
}

function sanitizeResponse(data: any, topic: string): RagData {
  if (!validateResponse(data)) {
    console.error("Invalid response structure from API");
    return { ...DEFAULT_DATA, topic: topic || "Black Holes" };
  }
  
  // Validate retrievedIndices are within bounds
  const validIndices = data.retrievedIndices.filter((idx: number) => 
    typeof idx === 'number' && idx >= 0 && idx < data.documents.length
  );
  
  if (validIndices.length === 0) {
    console.error("No valid retrieved indices");
    return { ...DEFAULT_DATA, topic: topic || "Black Holes" };
  }
  
  return {
    topic,
    userQuery: data.userQuery,
    documents: data.documents,
    retrievedIndices: validIndices,
    generatedAnswer: data.generatedAnswer
  };
}

async function generateWithGemini(topic: string, apiKey: string): Promise<RagData> {
  try {
    const ai = new GoogleGenAI({ apiKey });
    const model = "gemini-2.5-flash";

    const response = await ai.models.generateContent({
      model,
      contents: `Create a simplified RAG (Retrieval Augmented Generation) scenario about the topic: "${topic}".
      I need a user query, a list of 8 short factual snippets (documents) representing a knowledge base, 
      identification of which 3 indices (0-7) are most relevant to the query, and a final short answer.`,
      config: {
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.OBJECT,
          properties: {
            userQuery: { type: Type.STRING, description: "A simple question a user might ask about the topic" },
            documents: { 
              type: Type.ARRAY, 
              items: { type: Type.STRING },
              description: "8 short facts about the topic"
            },
            retrievedIndices: {
              type: Type.ARRAY,
              items: { type: Type.INTEGER },
              description: "Indices of the 3 most relevant documents (0-7)"
            },
            generatedAnswer: { type: Type.STRING, description: "A concise answer based on the retrieved documents" }
          },
          required: ["userQuery", "documents", "retrievedIndices", "generatedAnswer"]
        }
      }
    });

    if (response.text) {
      const data = JSON.parse(response.text);
      return sanitizeResponse(data, topic);
    }
    
    return { ...DEFAULT_DATA, topic: topic || "Black Holes" };
  } catch (error) {
    console.error("Gemini generation failed:", error);
    throw error;
  }
}

async function generateWithAnthropic(topic: string, apiKey: string, model: string = "claude-sonnet-4-20250514"): Promise<RagData> {
  try {
    const anthropic = new Anthropic({ apiKey });
    
    const message = await anthropic.messages.create({
      model,
      max_tokens: 2000,
      system: SYSTEM_PROMPT,
      messages: [{
        role: "user",
        content: `Create a RAG scenario about: "${topic}". Return ONLY valid JSON, no additional text.`
      }]
    });

    const content = message.content[0];
    if (content.type === 'text') {
      // Try to extract JSON from the response
      let text = content.text.trim();
      
      // Remove markdown code blocks if present
      text = text.replace(/^```json\s*/i, '').replace(/^```\s*/i, '').replace(/\s*```$/i, '');
      
      // Try to find JSON object
      const jsonMatch = text.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        try {
          const data = JSON.parse(jsonMatch[0]);
          return sanitizeResponse(data, topic);
        } catch (parseError) {
          console.error("Failed to parse Anthropic JSON:", parseError);
        }
      }
    }
    
    return { ...DEFAULT_DATA, topic: topic || "Black Holes" };
  } catch (error) {
    console.error("Anthropic generation failed:", error);
    throw error;
  }
}

async function generateWithAzureOpenAI(topic: string, apiKey: string, endpoint: string, deploymentName: string = "gpt-4"): Promise<RagData> {
  try {
    // Dynamic import to avoid breaking if package has issues
    const { OpenAIClient, AzureKeyCredential } = await import("@azure/openai");
    const client = new OpenAIClient(endpoint, new AzureKeyCredential(apiKey));
    
    const response = await client.getChatCompletions(deploymentName, [
      {
        role: "system",
        content: SYSTEM_PROMPT
      },
      {
        role: "user",
        content: `Create a RAG scenario about: "${topic}". Return ONLY valid JSON, no additional text.`
      }
    ], {
      responseFormat: { type: "json_object" },
      temperature: 0.7,
      maxTokens: 2000
    });

    const content = response.choices[0]?.message?.content;
    if (content) {
      try {
        let text = content.trim();
        // Remove markdown code blocks if present
        text = text.replace(/^```json\s*/i, '').replace(/^```\s*/i, '').replace(/\s*```$/i, '');
        
        const data = JSON.parse(text);
        return sanitizeResponse(data, topic);
      } catch (parseError) {
        console.error("Failed to parse Azure OpenAI JSON:", parseError);
        return { ...DEFAULT_DATA, topic: topic || "Black Holes" };
      }
    }
    
    return { ...DEFAULT_DATA, topic: topic || "Black Holes" };
  } catch (error) {
    console.error("Azure OpenAI generation failed:", error);
    throw error;
  }
}

export const generateRagScenario = async (
  topic: string, 
  provider: AIProvider = AIProvider.GEMINI
): Promise<RagData> => {
  // Get API keys from environment
  const geminiKey = process.env.GEMINI_API_KEY || process.env.API_KEY;
  const anthropicKey = process.env.ANTHROPIC_API_KEY;
  const anthropicModel = process.env.ANTHROPIC_MODEL || "claude-3-5-sonnet-20241022";
  const azureKey = process.env.AZURE_OPENAI_API_KEY;
  const azureEndpoint = process.env.AZURE_OPENAI_ENDPOINT;
  const azureDeployment = process.env.AZURE_OPENAI_DEPLOYMENT_NAME || "gpt-4";

  // Fallback to default data if no keys available
  if (!geminiKey && !anthropicKey && !azureKey) {
    console.warn("No API Key found for any provider, using default data.");
    return { ...DEFAULT_DATA, topic: topic || "Black Holes" };
  }

  try {
    switch (provider) {
      case AIProvider.GEMINI:
        if (!geminiKey) {
          throw new Error("Gemini API key not found. Please set GEMINI_API_KEY or API_KEY.");
        }
        return await generateWithGemini(topic, geminiKey);

      case AIProvider.ANTHROPIC:
        if (!anthropicKey) {
          throw new Error("Anthropic API key not found. Please set ANTHROPIC_API_KEY.");
        }
        return await generateWithAnthropic(topic, anthropicKey, anthropicModel);

      case AIProvider.AZURE_OPENAI:
        if (!azureKey || !azureEndpoint) {
          throw new Error("Azure OpenAI credentials not found. Please set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT.");
        }
        return await generateWithAzureOpenAI(topic, azureKey, azureEndpoint, azureDeployment);

      default:
        // Try providers in order of preference
        if (geminiKey) {
          return await generateWithGemini(topic, geminiKey);
        } else if (anthropicKey) {
          return await generateWithAnthropic(topic, anthropicKey, anthropicModel);
        } else if (azureKey && azureEndpoint) {
          return await generateWithAzureOpenAI(topic, azureKey, azureEndpoint, azureDeployment);
        }
        throw new Error("No available provider with valid credentials");
    }
  } catch (error) {
    console.error(`AI generation failed (${provider}):`, error);
    // Return default data on error
    return { ...DEFAULT_DATA, topic: topic || "Black Holes" };
  }
};

