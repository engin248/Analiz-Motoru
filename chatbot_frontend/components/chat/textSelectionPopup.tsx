// components/chat/textSelectionPopup.tsx
'use client';

import React, { useEffect, useState, useCallback } from 'react';

interface TextSelectionPopupProps {
    containerRef: React.RefObject<HTMLElement | null>;
    onQuote: (text: string) => void;
}

interface PopupPosition {
    x: number;
    y: number;
}

const TextSelectionPopup: React.FC<TextSelectionPopupProps> = ({ containerRef, onQuote }) => {
    const [isVisible, setIsVisible] = useState(false);
    const [position, setPosition] = useState<PopupPosition>({ x: 0, y: 0 });
    const [selectedText, setSelectedText] = useState('');

    const handleMouseUp = useCallback(() => {
        // Küçük bir gecikme ile seçimi kontrol et
        setTimeout(() => {
            const selection = window.getSelection();
            const text = selection?.toString().trim();

            if (text && text.length > 0 && containerRef.current) {
                // Seçimin container içinde olup olmadığını kontrol et
                const range = selection?.getRangeAt(0);
                if (range && containerRef.current.contains(range.commonAncestorContainer)) {
                    const rect = range.getBoundingClientRect();

                    // Popup'ı seçimin üstünde ortala
                    setPosition({
                        x: rect.left + rect.width / 2,
                        y: rect.top - 10
                    });
                    setSelectedText(text);
                    setIsVisible(true);
                } else {
                    setIsVisible(false);
                }
            } else {
                setIsVisible(false);
            }
        }, 10);
    }, [containerRef]);

    const handleMouseDown = useCallback((e: MouseEvent) => {
        // Popup'a tıklanmadıysa kapat
        const target = e.target as HTMLElement;
        if (!target.closest('[data-selection-popup]')) {
            setIsVisible(false);
        }
    }, []);

    const handleQuoteClick = () => {
        if (selectedText) {
            onQuote(selectedText);
            setIsVisible(false);
            // Seçimi temizle
            window.getSelection()?.removeAllRanges();
        }
    };

    useEffect(() => {
        document.addEventListener('mouseup', handleMouseUp);
        document.addEventListener('mousedown', handleMouseDown);

        return () => {
            document.removeEventListener('mouseup', handleMouseUp);
            document.removeEventListener('mousedown', handleMouseDown);
        };
    }, [handleMouseUp, handleMouseDown]);

    if (!isVisible) return null;

    return (
        <div
            data-selection-popup
            className="fixed z-50 animate-fade-in"
            style={{
                left: `${position.x}px`,
                top: `${position.y}px`,
                transform: 'translate(-50%, -100%)'
            }}
        >
            <button
                onClick={handleQuoteClick}
                className="flex items-center gap-2 px-3 py-2 bg-[#2F2F2F] hover:bg-[#3a3a3a] text-white/90 text-sm font-medium rounded-xl border border-white/10 shadow-xl transition-all duration-200 hover:scale-105"
            >
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={1.5}
                    stroke="currentColor"
                    className="w-4 h-4"
                >
                    <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 01.865-.501 48.172 48.172 0 003.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z"
                    />
                </svg>
                <span>AI&apos;a Sor</span>
            </button>

            {/* Küçük ok işareti */}
            <div
                className="absolute left-1/2 -translate-x-1/2 top-full w-0 h-0 border-l-8 border-r-8 border-t-8 border-l-transparent border-r-transparent border-t-[#2F2F2F]"
            />
        </div>
    );
};

export default TextSelectionPopup;
