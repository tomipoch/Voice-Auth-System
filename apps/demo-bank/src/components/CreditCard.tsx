import React, { useState } from 'react';
import { CreditCard as CardIcon, Eye, EyeOff, Copy } from 'lucide-react';
import toast from 'react-hot-toast';

interface CreditCardProps {
  number: string;
  name: string;
  expiry: string;
  type: 'visa' | 'mastercard';
  color?: string;
  cvv?: string;
}

export const CreditCard: React.FC<CreditCardProps> = ({ 
  number, 
  name, 
  expiry, 
  color = 'from-slate-800 to-slate-950',
  cvv = '123'
}) => {
  const [showData, setShowData] = useState(false);

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    toast.success(`${label} copiado`);
  };

  return (
    <div className={`relative w-full aspect-[1.58/1] rounded-[2.5rem] p-8 text-white overflow-hidden shadow-2xl transition-all duration-500 hover:scale-[1.01] bg-gradient-to-br ${color} shimmer group`}>
      {/* Background patterns */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full -mr-20 -mt-20 blur-3xl opacity-50 group-hover:opacity-80 transition-opacity" />
      <div className="absolute bottom-0 left-0 w-48 h-48 bg-amber-500/10 rounded-full -ml-10 -mb-10 blur-2xl opacity-50" />
      
      <div className="relative h-full flex flex-col justify-between">
        <div className="flex justify-between items-start">
          <div className="w-14 h-11 bg-amber-400/20 rounded-xl backdrop-blur-md flex items-center justify-center border border-amber-400/30">
            <div className="w-10 h-7 bg-gradient-to-br from-amber-300 to-amber-500 rounded-sm opacity-80" />
          </div>
          <div className="flex items-center gap-3">
            <button 
              onClick={() => setShowData(!showData)}
              className="p-2 bg-white/10 hover:bg-white/20 rounded-xl backdrop-blur-md transition-all border border-white/10"
              title={showData ? "Ocultar datos" : "Mostrar datos"}
            >
              {showData ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
            <CardIcon className="w-8 h-8 opacity-40" />
          </div>
        </div>
        
        <div className="mt-4">
          <div className="flex items-center gap-4 mb-6">
            <p className={`text-2xl font-medium tracking-[0.25em] drop-shadow-lg transition-all duration-300 ${!showData ? 'blur-sm select-none' : ''}`}>
              {showData ? number : '•••• •••• •••• ' + number.slice(-4)}
            </p>
            {showData && (
              <button onClick={() => copyToClipboard(number.replace(/\s/g, ''), 'Número')} className="opacity-60 hover:opacity-100">
                <Copy className="w-4 h-4" />
              </button>
            )}
          </div>
          
          <div className="flex justify-between items-end">
            <div className="space-y-1">
              <p className="text-[10px] uppercase tracking-widest text-slate-400">Titular de la Tarjeta</p>
              <p className="text-sm font-bold tracking-wide">{name}</p>
            </div>
            <div className="flex gap-8">
              <div className="space-y-1 text-right">
                <p className="text-[10px] uppercase tracking-widest text-slate-400">Vence</p>
                <p className="text-sm font-bold tracking-wide">{expiry}</p>
              </div>
              <div className="space-y-1 text-right">
                <p className="text-[10px] uppercase tracking-widest text-slate-400">CVV</p>
                <p className={`text-sm font-bold tracking-wide transition-all ${!showData ? 'blur-sm select-none' : ''}`}>
                  {showData ? cvv : '•••'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Glossy overlay */}
      <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/5 to-white/10 pointer-events-none opacity-50" />
    </div>
  );
};
