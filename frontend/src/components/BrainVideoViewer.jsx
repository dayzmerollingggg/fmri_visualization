// frontend/src/components/BrainVideoViewer.jsx
'use client';
import { useEffect, useRef, useState } from 'react';
import { Niivue } from '@niivue/niivue';

export default function BrainVideoViewer({ videoUrl, overlayGiiUrl, trDuration = 1.0 }) {
  const canvasRef = useRef(null);
  const videoRef = useRef(null);
  const nvRef = useRef(null);
  const [currentTR, setCurrentTR] = useState(0);

  useEffect(() => {
    const nv = new Niivue({
      show3Dcrosshair: true,
      backColor: [0, 0, 0, 1], // Black background
    });
    
    nv.attachToCanvas(canvasRef.current);

    // Load standard inflated fsaverage mesh and attach the dynamic 4D overlay
    async function loadBrainMesh() {
      await nv.loadSurfaces([
        {
          url: '/surfaces/lh.inflated.gii', // Serve base mesh from public directory
          overlays: [
            {
              url: overlayGiiUrl,
              colormap: 'warm',
              opacity: 0.8,
            },
          ],
        },
      ]);
      nvRef.current = nv;
    }

    loadBrainMesh();
  }, [overlayGiiUrl]);

  // Synchronize HTML5 video timestamp to NiiVue 4D frame
  const handleTimeUpdate = () => {
    if (!videoRef.current || !nvRef.current) return;
    
    const time = videoRef.current.currentTime;
    const targetTR = Math.floor(time / trDuration);

    if (targetTR !== currentTR) {
      setCurrentTR(targetTR);
      // NiiVue setFrame4D(meshIndex, frameIndex)
      nvRef.current.setFrame4D(0, targetTR); 
    }
  };

  return (
    <div className="flex flex-col md:flex-row gap-6 p-4">
      {/* Video Player Section */}
      <div className="flex-1">
        <video
          ref={videoRef}
          src={videoUrl}
          controls
          onTimeUpdate={handleTimeUpdate}
          className="w-full rounded-lg shadow-lg"
        />
        <p className="mt-2 text-sm text-gray-500">
          Active Timepoint (TR): <strong>{currentTR}</strong>
        </p>
      </div>

      {/* 3D Brain Viewer Section */}
      <div className="flex-1 relative">
        <canvas 
          ref={canvasRef} 
          className="w-full h-[400px] rounded-lg border bg-black" 
        />
      </div>
    </div>
  );
}
