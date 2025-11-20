import React, { useRef, useEffect, useState } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { Text, Line, Box, Sphere, Float, Grid, Center, Html, RoundedBox, OrbitControls } from '@react-three/drei';
import * as THREE from 'three';
import { RagStep, RagData, STEPS } from '../types';

// Fix for TypeScript errors where R3F intrinsic elements are not recognized in the global JSX namespace
declare global {
  namespace JSX {
    interface IntrinsicElements {
      group: any;
      meshStandardMaterial: any;
      ambientLight: any;
      pointLight: any;
      directionalLight: any;
      meshPhysicalMaterial: any;
      points: any;
      bufferGeometry: any;
      bufferAttribute: any;
      pointsMaterial: any;
    }
  }
}

interface SceneProps {
  currentStep: RagStep;
  data: RagData;
}

const Colors = {
  user: '#3b82f6', // blue-500
  embedding: '#a855f7', // purple-500
  db: '#64748b', // slate-500
  activeDoc: '#22c55e', // green-500
  llm: '#f59e0b', // amber-500
  text: '#1e293b', // slate-800
  source: '#ef4444', // red-500
};

// --- Sub-Components ---

const ConnectionLine = ({ start, end, active, color = 'gray', dashed = true }: { start: [number, number, number], end: [number, number, number], active: boolean, color?: string, dashed?: boolean }) => {
  const ref = useRef<any>(null);
  useFrame((state) => {
    if (ref.current && active && dashed) {
      ref.current.material.dashOffset -= 0.02;
    }
  });

  return (
    <Line
      ref={ref}
      points={[start, end]}
      color={active ? color : '#cbd5e1'}
      lineWidth={active ? 3 : 1}
      dashed={dashed}
      dashScale={active && dashed ? 2 : 0}
      dashSize={0.5}
      gapSize={0.2}
      opacity={active ? 1 : 0.2}
      transparent
    />
  );
};

const Label = ({ position, text, scale = 1 }: { position: [number, number, number], text: string, scale?: number }) => {
  return (
    <Text
      position={position}
      fontSize={0.5 * scale}
      color="#334155"
      anchorX="center"
      anchorY="middle"
      outlineWidth={0.02}
      outlineColor="#ffffff"
    >
      {text}
    </Text>
  );
};

const DocumentNode = ({ position, isRetrieved, text, index, visible = true }: { position: [number, number, number], isRetrieved: boolean, text: string, index: number, visible?: boolean }) => {
  const [hovered, setHover] = useState(false);
  
  return (
    <group position={position} visible={visible}>
        <Float speed={2} rotationIntensity={0.2} floatIntensity={0.2}>
            <RoundedBox args={[0.8, 1, 0.1]} radius={0.05} 
                onPointerOver={(e) => { e.stopPropagation(); setHover(true); }}
                onPointerOut={(e) => setHover(false)}
            >
                <meshStandardMaterial color={isRetrieved ? Colors.activeDoc : Colors.db} transparent opacity={isRetrieved ? 1 : 0.7} />
            </RoundedBox>
            {/* Lines representing text */}
            <Line points={[[-0.3, 0.3, 0.06], [0.3, 0.3, 0.06]]} color="white" lineWidth={2} />
            <Line points={[[-0.3, 0.1, 0.06], [0.3, 0.1, 0.06]]} color="white" lineWidth={2} />
            <Line points={[[-0.3, -0.1, 0.06], [0.1, -0.1, 0.06]]} color="white" lineWidth={2} />
        </Float>
        {hovered && (
             <Html position={[0, 1.2, 0]} center className="pointer-events-none" style={{ pointerEvents: 'none' }}>
             <div className="bg-slate-900 text-white text-xs p-2 rounded shadow-lg w-48 z-50 relative">
               {text}
             </div>
           </Html>
        )}
    </group>
  );
};

const SourceDocument = ({ position, visible }: { position: [number, number, number], visible: boolean }) => {
    return (
        <group position={position} visible={visible}>
             <Float speed={1} rotationIntensity={0.1} floatIntensity={0.1}>
                <RoundedBox args={[2.5, 3.5, 0.2]} radius={0.1}>
                    <meshStandardMaterial color="#f1f5f9" />
                </RoundedBox>
                 {/* Text Lines on big doc */}
                 {[-1, -0.5, 0, 0.5, 1].map((y, i) => (
                     <Line key={i} points={[[-0.8, y, 0.11], [0.8, y, 0.11]]} color="#94a3b8" lineWidth={3} />
                 ))}
                 <Label position={[0, 2, 0]} text="Source Document" scale={1.2} />
             </Float>
             <Html position={[0, 0, 0]} center transform>
                <div className="text-slate-300 opacity-50 text-4xl font-bold rotate-45 select-none">
                    RAW DATA
                </div>
             </Html>
        </group>
    );
};

const StepAwareOrbitControls = ({ step }: { step: RagStep }) => {
    const controlsRef = useRef<any>(null);
    const targetPosRef = useRef(new THREE.Vector3());
    const isAnimating = useRef(false);
    const userInteracting = useRef(false);

    // Detect step change
    useEffect(() => {
        const targetStep = STEPS.find(s => s.id === step) || STEPS[0];
        targetPosRef.current.set(...targetStep.cameraPos);
        isAnimating.current = true;
    }, [step]);

    useFrame((state, delta) => {
        // Only animate if needed and user is not fighting it
        if (isAnimating.current && !userInteracting.current) {
            const stepSize = 4 * delta; // Adjust speed
            state.camera.position.lerp(targetPosRef.current, stepSize);
            
            if (controlsRef.current) {
                // Smoothly move focus to center
                controlsRef.current.target.lerp(new THREE.Vector3(0,0,0), stepSize);
                controlsRef.current.update();
            }

            if (state.camera.position.distanceTo(targetPosRef.current) < 0.1) {
                isAnimating.current = false;
            }
        }
    });

    return (
        <OrbitControls 
            ref={controlsRef}
            makeDefault 
            onStart={() => { userInteracting.current = true; isAnimating.current = false; }}
            onEnd={() => { userInteracting.current = false; }}
            enableDamping={true}
            dampingFactor={0.1}
            minDistance={2}
            maxDistance={40}
        />
    );
}

const DataPacket = ({ route, step, activeStep }: { route: [number, number, number][], step: RagStep, activeStep: RagStep }) => {
    const ref = useRef<THREE.Mesh>(null);
    const [progress, setProgress] = useState(0);

    useFrame(() => {
        if (activeStep === step) {
            if (progress < 1) {
                setProgress(p => p + 0.015);
            } else {
                setProgress(0); // Loop for visual effect
            }
        } else {
            setProgress(0);
        }

        if (ref.current) {
            // Simple linear interpolation between points
            const p1 = new THREE.Vector3(...route[0]);
            const p2 = new THREE.Vector3(...route[1]);
            ref.current.position.lerpVectors(p1, p2, progress);
            
            // Scale effect
            const s = activeStep === step ? 1 : 0;
            ref.current.scale.setScalar(s * 0.3);
        }
    });

    return (
        <Sphere ref={ref} args={[0.5, 16, 16]}>
            <meshStandardMaterial color="#fbbf24" emissive="#f59e0b" emissiveIntensity={1} />
        </Sphere>
    )
}

// --- Main Scene Content ---

const RagSceneContent = ({ currentStep, data }: SceneProps) => {
  
  // Increased spacing for better visualization
  // Previous X range: [-8, 8]. New X range: [-14, 14]
  const posUser = new THREE.Vector3(-14, 0, 0);
  const posSource = new THREE.Vector3(-10, 5, 0);
  const posEmbedding = new THREE.Vector3(-7, 0, 0);
  const posDB = new THREE.Vector3(0, -5, -2);
  const posContext = new THREE.Vector3(7, 0, 0);
  const posLLM = new THREE.Vector3(14, 0, 0);

  // Calculate document positions in a grid/cloud for the DB
  const dbPositions = React.useMemo(() => data.documents.map((_, i) => {
    const col = i % 4;
    const row = Math.floor(i / 4);
    return new THREE.Vector3(
        posDB.x + (col - 1.5) * 1.5, 
        posDB.y + row * 1.5, 
        posDB.z + (Math.random() * 2)
    );
  }), [data.documents]);

  // Calculate chunk positions (initial split positions near source)
  const chunkPositions = React.useMemo(() => data.documents.map((_, i) => {
     const col = i % 2;
     const row = Math.floor(i / 2);
     return new THREE.Vector3(
         posSource.x + (col - 0.5) * 1.5,
         posSource.y - 2 + row * -1.2,
         posSource.z
     );
  }), [data.documents]);

  // Visibility logic for User Query: strict check for phases where query exists
  const isUserVisible = [
      RagStep.INPUT, 
      RagStep.EMBEDDING, 
      RagStep.RETRIEVAL, 
      RagStep.AUGMENTATION, 
      RagStep.GENERATION, 
      RagStep.COMPLETE
  ].includes(currentStep);

  return (
    <>
      <ambientLight intensity={0.7} />
      <pointLight position={[10, 10, 10]} intensity={1} />
      <directionalLight position={[-5, 5, 5]} intensity={0.5} />
      <Grid infiniteGrid fadeDistance={40} fadeStrength={5} cellColor="#cbd5e1" sectionColor="#94a3b8" position={[0, -8, 0]} />

      <StepAwareOrbitControls step={currentStep} />

      {/* --- 0. SOURCE DOCUMENT (Upload/Chunking) --- */}
      <SourceDocument 
        position={posSource.toArray()} 
        visible={currentStep === RagStep.UPLOAD || currentStep === RagStep.CHUNKING} 
      />

      {/* --- 1. USER NODE --- */}
      <group position={posUser} visible={isUserVisible}>
        <Sphere args={[0.8, 32, 32]}>
            <meshStandardMaterial color={Colors.user} />
        </Sphere>
        <Label position={[0, 1.5, 0]} text="User" />
        {/* Query Bubble */}
        <Html position={[0, -1.5, 0]} center transform sprite>
            <div className="transition-all duration-500 bg-white border-2 border-blue-500 p-2 rounded-lg shadow-md w-48 text-xs text-center">
                <span className="font-bold text-blue-600">Query:</span><br/>
                <span className="text-slate-800">"{data.userQuery}"</span>
            </div>
        </Html>
      </group>

      {/* User -> Embedding Connection */}
      <ConnectionLine 
        start={posUser.toArray()} 
        end={posEmbedding.toArray()} 
        active={currentStep === RagStep.EMBEDDING || currentStep === RagStep.RETRIEVAL} 
        color={Colors.embedding}
      />
      <DataPacket route={[posUser.toArray(), posEmbedding.toArray()]} step={RagStep.EMBEDDING} activeStep={currentStep} />

      {/* --- 2. EMBEDDING MODEL --- */}
      <group position={posEmbedding}>
         <Box args={[1.5, 1.5, 1.5]}>
            <meshStandardMaterial color={Colors.embedding} transparent opacity={0.8} />
         </Box>
         <Label position={[0, 1.2, 0]} text="Embedding Model" />
         {/* Embedding visualization logic */}
         {(currentStep === RagStep.EMBEDDING || currentStep === RagStep.INDEXING) && (
             <Html position={[0, 2.5, 0]} center>
                 <div className="bg-purple-600 text-white px-3 py-1 rounded-full text-xs animate-bounce w-max">
                    {currentStep === RagStep.INDEXING ? "Vectorizing Chunks..." : "Vectorizing Query..."}
                 </div>
             </Html>
         )}
      </group>

      {/* Embedding -> DB Connection (Used for both Indexing and Retrieval) */}
      <ConnectionLine 
        start={posEmbedding.toArray()} 
        end={[posDB.x, posDB.y + 2, posDB.z]} 
        active={currentStep === RagStep.RETRIEVAL || currentStep === RagStep.INDEXING}
        color={currentStep === RagStep.INDEXING ? Colors.db : Colors.activeDoc} 
      />
      
      {/* In retrieval, the query travels. In indexing, we visualize docs moving separately */}
      <DataPacket route={[posEmbedding.toArray(), [posDB.x, posDB.y+2, posDB.z]]} step={RagStep.RETRIEVAL} activeStep={currentStep} />


      {/* --- 3. VECTOR DB & DOCUMENTS --- */}
      <group>
        {data.documents.map((doc, i) => {
            const isRetrieved = data.retrievedIndices.includes(i);
            const isRetrievalStep = currentStep === RagStep.RETRIEVAL;
            
            // Animation Logic for Document Position
            let targetPos = dbPositions[i];
            let basePos = dbPositions[i];
            let visible = true;

            // Logic for Indexing Phase
            if (currentStep === RagStep.UPLOAD) {
                visible = false;
                basePos = chunkPositions[i]; // Start hidden at chunk pos
            } else if (currentStep === RagStep.CHUNKING) {
                visible = true;
                targetPos = chunkPositions[i];
                basePos = chunkPositions[i];
            } else if (currentStep === RagStep.INDEXING) {
                // Move from Chunk Pos -> DB Pos
                // We use AnimatedDocument to lerp, so target is DB, base is implicitly handled by lerp
                targetPos = dbPositions[i];
                basePos = chunkPositions[i]; // Reset base for safety, though lerp takes over
            }

            // Logic for Retrieval/Augmentation Phase
            const isMovingToContext = isRetrieved && (currentStep === RagStep.AUGMENTATION || currentStep === RagStep.GENERATION || currentStep === RagStep.COMPLETE);
            if (isMovingToContext) {
                targetPos = posContext.clone().add(new THREE.Vector3(0, (i % 3) * 0.5 - 0.5, 0));
            }
            
            // Lines showing indexing flow
            const showIndexingLine = currentStep === RagStep.INDEXING;

            return (
                <React.Fragment key={i}>
                    <AnimatedDocument 
                        targetPos={targetPos}
                        basePos={basePos} // Initial pos for lerp
                        isRetrieved={isRetrieved}
                        isHighlighted={isRetrievalStep && isRetrieved}
                        text={doc}
                        index={i}
                        visible={visible}
                        moveSpeed={currentStep === RagStep.INDEXING ? 0.03 : 0.05}
                    />
                    {/* Line from Embedding to Doc during indexing */}
                    {showIndexingLine && (
                        <IndexingLine start={posEmbedding} end={dbPositions[i]} />
                    )}
                </React.Fragment>
            );
        })}
        <Label position={[posDB.x, posDB.y - 1.5, posDB.z]} text="Vector Database" scale={1.5} />
      </group>

      {/* --- 4. CONTEXT WINDOW --- */}
      {currentStep === RagStep.AUGMENTATION && (
        <group position={posContext}>
             <Html position={[0, 2, 0]} center>
                 <div className="bg-green-600 text-white px-4 py-2 rounded-lg shadow-lg text-sm w-64 text-center">
                    <strong>Augmenting Prompt:</strong><br/>
                    System: Use these contexts...<br/>
                    User: {data.userQuery}
                 </div>
             </Html>
        </group>
      )}
      
       <ConnectionLine 
        start={posContext.toArray()} 
        end={posLLM.toArray()} 
        active={currentStep === RagStep.GENERATION}
        color={Colors.llm} 
      />
      <DataPacket route={[posContext.toArray(), posLLM.toArray()]} step={RagStep.GENERATION} activeStep={currentStep} />


      {/* --- 5. LLM --- */}
      <group position={posLLM}>
        <RoundedBox args={[2, 3, 2]} radius={0.1}>
            <meshPhysicalMaterial 
                color={Colors.llm} 
                transmission={0.6} 
                roughness={0.2} 
                thickness={2}
            />
        </RoundedBox>
        
        <Points count={20} />
        <Label position={[0, 2, 0]} text="LLM" scale={1.5} />
        
        {(currentStep === RagStep.GENERATION || currentStep === RagStep.COMPLETE) && (
             <Html position={[0, -2.5, 0]} center transform>
             <div className="bg-amber-100 border-2 border-amber-500 p-4 rounded-lg shadow-xl w-64 text-sm text-slate-900">
                <span className="font-bold text-amber-700">Generated Answer:</span>
                <p className="mt-1">{data.generatedAnswer}</p>
             </div>
           </Html>
        )}
      </group>

    </>
  );
};

interface AnimatedDocumentProps {
  targetPos: THREE.Vector3;
  basePos: THREE.Vector3;
  isRetrieved: boolean;
  isHighlighted: boolean;
  text: string;
  index: number;
  visible: boolean;
  moveSpeed?: number;
}

// Helper for animated document movement
const AnimatedDocument = ({ targetPos, basePos, isRetrieved, isHighlighted, text, index, visible, moveSpeed = 0.05 }: AnimatedDocumentProps) => {
    const ref = useRef<THREE.Group>(null);
    // Initialize position manually if provided
    useEffect(() => {
       if (ref.current && basePos) {
           // Only snap if strictly needed, otherwise let lerp handle it
           // ref.current.position.copy(basePos);
       }
    }, []);

    useFrame(() => {
        if (ref.current) {
            // Lerp to target position
            ref.current.position.lerp(targetPos, moveSpeed);
            
            // Pulse scale if highlighted
            if (isHighlighted) {
                const s = 1 + Math.sin(Date.now() / 200) * 0.1;
                ref.current.scale.setScalar(s);
            } else {
                ref.current.scale.lerp(new THREE.Vector3(1,1,1), 0.1);
            }
        }
    });

    return (
        <group ref={ref} position={basePos} visible={visible}>
             <DocumentNode position={[0,0,0]} isRetrieved={isRetrieved} text={text} index={index} />
        </group>
    )
}

// Temporary line during indexing
const IndexingLine = ({ start, end }: { start: THREE.Vector3, end: THREE.Vector3 }) => {
    const ref = useRef<any>(null);
    useFrame(() => {
        if(ref.current) ref.current.material.dashOffset -= 0.1;
    })
    return (
        <Line 
            ref={ref}
            points={[start.toArray(), end.toArray()]} 
            color={Colors.embedding} 
            opacity={0.3} 
            transparent 
            dashed 
            dashScale={1}
        />
    )
}

const Points = ({ count = 10 }) => {
    const points = React.useMemo(() => {
        const p = new Float32Array(count * 3);
        for(let i=0; i<count*3; i++) {
            p[i] = (Math.random() - 0.5) * 1.8;
        }
        return p;
    }, [count]);
    
    return (
        <points>
            <bufferGeometry>
                <bufferAttribute 
                    attach="attributes-position" 
                    count={count} 
                    array={points} 
                    itemSize={3} 
                />
            </bufferGeometry>
            <pointsMaterial size={0.1} color="white" />
        </points>
    )
}

export const Scene3D = (props: SceneProps) => {
  return (
    <div className="w-full h-full bg-slate-50">
      <Canvas shadows camera={{ position: [0, 5, 20], fov: 45 }}>
        <RagSceneContent {...props} />
      </Canvas>
    </div>
  );
};