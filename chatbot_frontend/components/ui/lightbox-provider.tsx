'use client';

import React, { createContext, useContext, useState, ReactNode, useEffect } from 'react';

interface LightboxContextType {
    openLightbox: (src: string) => void;
    closeLightbox: () => void;
}

const LightboxContext = createContext<LightboxContextType | undefined>(undefined);

export const useLightbox = () => {
    const context = useContext(LightboxContext);
    if (!context) {
        throw new Error('useLightbox must be used within a LightboxProvider');
    }
    return context;
};

export const LightboxProvider = ({ children }: { children: ReactNode }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [imageSrc, setImageSrc] = useState('');

    const openLightbox = (src: string) => {
        setImageSrc(src);
        setIsOpen(true);
        // Prevent scrolling when lightbox is open
        document.body.style.overflow = 'hidden';
    };

    const closeLightbox = () => {
        setIsOpen(false);
        setImageSrc('');
        // Restore scrolling
        document.body.style.overflow = 'unset';
    };

    // Close on escape key
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Escape') {
                closeLightbox();
            }
        };

        if (isOpen) {
            window.addEventListener('keydown', handleKeyDown);
        }

        return () => {
            window.removeEventListener('keydown', handleKeyDown);
        };
    }, [isOpen]);

    return (
        <LightboxContext.Provider value={{ openLightbox, closeLightbox }}>
            {children}
            {isOpen && (
                <div
                    className="fixed inset-0 z-[100] flex items-center justify-center bg-black/90 p-4 animate-fade-in"
                    onClick={closeLightbox}
                >
                    <div 
                        className="relative w-full h-full flex items-center justify-center pointer-events-none"
                    >
                        {/* Wrapper for image to handle clicks on the image vs background */}
                        <div className="relative max-w-full max-h-full pointer-events-auto">
                            <img
                                src={imageSrc}
                                alt="Full size"
                                className="max-w-[95vw] max-h-[95vh] object-contain rounded-lg shadow-2xl"
                                onClick={(e) => e.stopPropagation()} // Clicking image shouldn't close it? Usually it does or doesn't. User said "ekranda açsın", usually click bg to close.
                            />
                            <button
                                onClick={closeLightbox}
                                className="absolute -top-12 -right-4 md:-right-12 text-white hover:text-gray-300 focus:outline-none p-2 rounded-full bg-black/50 hover:bg-black/70 transition-colors"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </LightboxContext.Provider>
    );
};

