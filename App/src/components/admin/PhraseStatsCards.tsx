/**
 * Phrase Stats Cards Component
 * Displays key metrics about phrases in card format
 */

import type { PhraseStats } from '../../types/phrases';
import { BookOpen, CheckCircle, Smile, Flame } from 'lucide-react';

interface PhraseStatsCardsProps {
  stats: PhraseStats | null;
  loading: boolean;
}

export const PhraseStatsCards = ({ stats, loading }: PhraseStatsCardsProps) => {
  if (loading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4 animate-pulse border border-gray-100 dark:border-gray-700"
          >
            <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-2"></div>
            <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
          </div>
        ))}
      </div>
    );
  }

  if (!stats) return null;

  const cards = [
    {
      title: 'Total Frases',
      value: stats.total.toLocaleString(),
      icon: BookOpen,
      bg: 'bg-blue-50 dark:bg-blue-900/20',
      text: 'text-blue-600 dark:text-blue-400',
    },
    {
      title: 'Activas',
      value: stats.active.toLocaleString(),
      icon: CheckCircle,
      bg: 'bg-green-50 dark:bg-green-900/20',
      text: 'text-green-600 dark:text-green-400',
    },
    {
      title: 'Fáciles',
      value: stats.easy.toLocaleString(),
      icon: Smile,
      bg: 'bg-teal-50 dark:bg-teal-900/20',
      text: 'text-teal-600 dark:text-teal-400',
    },
    {
      title: 'Difíciles',
      value: stats.hard.toLocaleString(),
      icon: Flame,
      bg: 'bg-red-50 dark:bg-red-900/20',
      text: 'text-red-600 dark:text-red-400',
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      {cards.map((card) => (
        <div
          key={card.title}
          className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-100 dark:border-gray-700 p-4 transition-all hover:shadow-md"
        >
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg shrink-0 ${card.bg} ${card.text}`}>
              <card.icon className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">
                {card.title}
              </p>
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mt-0.5">
                {card.value}
              </h3>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default PhraseStatsCards;
