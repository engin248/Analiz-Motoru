// components/chat/quoteInput.tsx
'use client';

import React from 'react';

interface QuoteInputProps {
    quotedText: string;
    onClear: () => void;
}

const QuoteInput: React.FC<QuoteInputProps> = ({ quotedText, onClear }) => {
    // Metni kısalt (maksimum 100 karakter)
    const displayText = quotedText.length > 100
        ? quotedText.substring(0, 100) + '...'
        : quotedText;

    return (
        <div className="flex items-start gap-2 bg-[#2F2F2F] px-4 py-3 rounded-t-2xl border-b border-white/5 animate-slide-down">
            {/* Sol taraftaki alıntı ikonu */}
            <div className="flex-shrink-0 mt-0.5">
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={1.5}
                    stroke="currentColor"
                    className="w-4 h-4 text-brand-emerald"
                >
                    <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M9 15L3 9m0 0l6-6M3 9h12a6 6 0 010 12h-3"
                    />
                </svg>
            </div>

            {/* Alıntı metni */}
            <div className="flex-1 min-w-0">
                <span className="text-sm text-white/80 line-clamp-2">
                    &ldquo;{displayText}&rdquo;
                </span>
            </div>

            {/* Kapat butonu */}
            <button
                type="button"
                onClick={onClear}
                className="flex-shrink-0 p-1 hover:bg-white/10 rounded-lg transition-colors text-white/60 hover:text-white"
                title="Alıntıyı kaldır"
            >
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                    className="w-4 h-4"
                >
                    <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
                </svg>
            </button>
        </div>
    );
};

export default QuoteInput;
