// components/Chat/TypingIndicator.tsx
import React from 'react';
import Image from 'next/image';

const TypingIndicator: React.FC = () => {
    return (
        <div className="flex w-full mb-6 justify-start animate-fade-in">
            {/* AI Avatar */}
            <div className="w-10 h-10 rounded-full overflow-hidden flex-shrink-0 shadow-lg ring-2 ring-[var(--color-gold)]/30">
                <Image
                    src="/avatar.png"
                    alt="AI"
                    width={40}
                    height={40}
                    className="w-full h-full object-cover"
                />
            </div>

            {/* Makas Animasyonu İçeren Balon */}
            <div className="ml-3">
                <div className="p-4 rounded-2xl bg-[var(--output-ai-bg)] backdrop-blur-sm border border-[var(--output-ai-border)] shadow-xl">
                    <div className="flex items-center space-x-3">
                        <span className="text-[var(--output-ai-text)] text-sm">Düşünüyorum</span>

                        {/* Makas ve Kumaş Animasyonu */}
                        <div className="relative flex items-center space-x-2">
                            {/* Makas İkonu - Animasyonlu */}
                            <svg
                                className="w-5 h-5 text-[var(--color-gold)] animate-[snip_1.5s_ease-in-out_infinite]"
                                fill="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path d="M9.64 7.64c.23-.5.36-1.05.36-1.64 0-2.21-1.79-4-4-4S2 3.79 2 6s1.79 4 4 4c.59 0 1.14-.13 1.64-.36L10 12l-2.36 2.36C7.14 14.13 6.59 14 6 14c-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4c0-.59-.13-1.14-.36-1.64L12 14l7 7h3v-1L9.64 7.64zM6 8c-1.1 0-2-.89-2-2s.9-2 2-2 2 .89 2 2-.9 2-2 2zm0 12c-1.1 0-2-.89-2-2s.9-2 2-2 2 .89 2 2-.9 2-2 2zm6-7.5c-.28 0-.5-.22-.5-.5s.22-.5.5-.5.5.22.5.5-.22.5-.5.5zM19 3l-6 6 2 2 7-7V3z" />
                            </svg>

                            {/* Kesilen Kumaş Parçaları - Dalgalı Çizgiler */}
                            <div className="flex space-x-1">
                                <div className="w-1 h-4 bg-gradient-to-b from-[var(--color-gold)] to-[var(--color-green)] rounded-full animate-[fall_1.5s_ease-in-out_infinite] opacity-70" style={{ animationDelay: '0ms' }}></div>
                                <div className="w-1 h-4 bg-gradient-to-b from-[var(--color-green)] to-[var(--color-gold)] rounded-full animate-[fall_1.5s_ease-in-out_infinite] opacity-70" style={{ animationDelay: '300ms' }}></div>
                                <div className="w-1 h-4 bg-gradient-to-b from-[var(--color-gold)] to-[var(--color-green-light)] rounded-full animate-[fall_1.5s_ease-in-out_infinite] opacity-70" style={{ animationDelay: '600ms' }}></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Özel Animasyon Stilleri */}
            <style jsx>{`
                @keyframes snip {
                    0%, 100% {
                        transform: rotate(0deg) scale(1);
                    }
                    25% {
                        transform: rotate(-15deg) scale(1.1);
                    }
                    50% {
                        transform: rotate(0deg) scale(1);
                    }
                    75% {
                        transform: rotate(15deg) scale(1.1);
                    }
                }
                
                @keyframes fall {
                    0% {
                        transform: translateY(0) scaleY(1);
                        opacity: 0.7;
                    }
                    50% {
                        transform: translateY(3px) scaleY(0.8);
                        opacity: 0.4;
                    }
                    100% {
                        transform: translateY(0) scaleY(1);
                        opacity: 0.7;
                    }
                }
            `}</style>
        </div>
    );
};

export default TypingIndicator;
