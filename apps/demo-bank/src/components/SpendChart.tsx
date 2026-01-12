import React from 'react';

export const SpendChart: React.FC = () => {
  return (
    <div className="relative w-full h-48 flex items-end justify-between gap-1 px-2">
      {[40, 70, 45, 90, 65, 80, 50, 85, 60, 95, 75, 100].map((height, i) => (
        <div key={i} className="flex-1 group relative flex flex-col items-center">
          {/* Tooltip on hover */}
          <div className="absolute -top-10 scale-0 group-hover:scale-100 transition-transform duration-200 bg-slate-800 text-white text-[10px] px-2 py-1 rounded-md z-10">
            ${(height * 1234).toLocaleString()}
          </div>
          
          <div 
            className="w-full rounded-t-lg bg-gradient-to-t from-amber-500/20 to-amber-500/80 transition-all duration-700 ease-out delay-[100ms]"
            style={{ 
              height: `${height}%`,
              animation: `grow-up 1s ease-out ${i * 50}ms forwards`,
              opacity: 0,
              transform: 'translateY(20px)'
            }}
          />
        </div>
      ))}
      
      <style>{`
        @keyframes grow-up {
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
      
      {/* X-Axis Labels */}
      <div className="absolute -bottom-6 w-full flex justify-between text-[10px] text-slate-400 font-medium px-2">
        <span>Ene</span>
        <span>Jun</span>
        <span>Dic</span>
      </div>
    </div>
  );
};
