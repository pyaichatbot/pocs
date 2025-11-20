
export enum RagStep {
  UPLOAD = 'UPLOAD',
  CHUNKING = 'CHUNKING',
  INDEXING = 'INDEXING',
  INPUT = 'INPUT',
  EMBEDDING = 'EMBEDDING',
  RETRIEVAL = 'RETRIEVAL',
  AUGMENTATION = 'AUGMENTATION',
  GENERATION = 'GENERATION',
  COMPLETE = 'COMPLETE'
}

export enum AIProvider {
  GEMINI = 'GEMINI',
  ANTHROPIC = 'ANTHROPIC',
  AZURE_OPENAI = 'AZURE_OPENAI'
}

export interface RagData {
  topic: string;
  userQuery: string;
  documents: string[];
  retrievedIndices: number[];
  generatedAnswer: string;
}

export interface StepInfo {
  id: RagStep;
  title: string;
  description: string;
  cameraPos: [number, number, number];
}

export const STEPS: StepInfo[] = [
  {
    id: RagStep.UPLOAD,
    title: "Document Upload",
    description: "Before the system can answer questions, we must provide it with knowledge. A source document (e.g., PDF, Wiki page) containing raw text is uploaded to the system.",
    cameraPos: [-12, 5, 14]
  },
  {
    id: RagStep.CHUNKING,
    title: "Text Chunking",
    description: "Large documents are too big to process at once. The system splits the text into smaller, manageable pieces called 'chunks'. Each chunk represents a distinct fact or paragraph.",
    cameraPos: [-12, 5, 10]
  },
  {
    id: RagStep.INDEXING,
    title: "Indexing & Storage",
    description: "Each text chunk is passed through the Embedding Model to create a vector. These vectors are then stored in the Vector Database, creating a searchable index of knowledge.",
    cameraPos: [0, 0, 14]
  },
  {
    id: RagStep.INPUT,
    title: "User Query",
    description: "The system is now ready. A user submits a question. In a standard LLM, the model relies solely on training data. In RAG, we use this query to search our new index.",
    cameraPos: [-14, 2, 12]
  },
  {
    id: RagStep.EMBEDDING,
    title: "Query Embedding",
    description: "The user's query is sent to the same Embedding Model. It converts the question into a vector in the same high-dimensional space as our document chunks.",
    cameraPos: [-7, 2, 12]
  },
  {
    id: RagStep.RETRIEVAL,
    title: "Vector Search",
    description: "The system calculates the distance between the query vector and all document vectors. The closest matches (most relevant chunks) are retrieved from the database.",
    cameraPos: [0, 8, 8]
  },
  {
    id: RagStep.AUGMENTATION,
    title: "Prompt Augmentation",
    description: "The retrieved chunks are combined with the original user query into a new, enriched prompt. This gives the LLM the exact facts it needs to answer correctly.",
    cameraPos: [7, 2, 12]
  },
  {
    id: RagStep.GENERATION,
    title: "LLM Generation",
    description: "The augmented prompt is sent to the LLM. The model generates a final answer, grounding its response in the retrieved facts rather than hallucinating.",
    cameraPos: [14, 2, 12]
  },
  {
    id: RagStep.COMPLETE,
    title: "Complete",
    description: "The RAG process is complete. The LLM has generated an accurate answer based on the retrieved context, demonstrating how RAG enhances LLM responses with external knowledge.",
    cameraPos: [14, 2, 12]
  }
];
