'use client';

interface StatusBadgeProps {
  status: 'success' | 'warning' | 'error' | 'pending' | 'running';
  text?: string;
  className?: string;
}

const statusConfig = {
  success: {
    bg: 'bg-green-100',
    text: 'text-green-800',
    defaultText: 'Healthy'
  },
  warning: {
    bg: 'bg-yellow-100',
    text: 'text-yellow-800',
    defaultText: 'Warning'
  },
  error: {
    bg: 'bg-red-100',
    text: 'text-red-800',
    defaultText: 'Error'
  },
  pending: {
    bg: 'bg-gray-100',
    text: 'text-gray-800',
    defaultText: 'Pending'
  },
  running: {
    bg: 'bg-blue-100',
    text: 'text-blue-800',
    defaultText: 'Running'
  }
};

export default function StatusBadge({ status, text, className = '' }: StatusBadgeProps) {
  const config = statusConfig[status];
  
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.bg} ${config.text} ${className}`}
    >
      <span className={`w-1.5 h-1.5 mr-1.5 rounded-full ${config.bg.replace('100', '400')}`}></span>
      {text || config.defaultText}
    </span>
  );
}
