'use client';

import React, { useState, useEffect } from 'react';

interface TypewriterProps {
    texts: string[];
    typingSpeed?: number;
    deletingSpeed?: number;
    delayBeforeDelete?: number;
    delayBeforeType?: number;
    className?: string;
}

export const Typewriter: React.FC<TypewriterProps> = ({
    texts,
    typingSpeed = 50,
    deletingSpeed = 30,
    delayBeforeDelete = 2000,
    delayBeforeType = 500,
    className = "",
}) => {
    const [textIndex, setTextIndex] = useState(0);
    const [subIndex, setSubIndex] = useState(0);
    const [isDeleting, setIsDeleting] = useState(false);
    const [blink, setBlink] = useState(true);

    // Blinking cursor effect
    useEffect(() => {
        const timeout = setTimeout(() => {
            setBlink(prev => !prev);
        }, 500);
        return () => clearTimeout(timeout);
    }, [blink]);

    // Typing logic
    useEffect(() => {
        if (!texts || texts.length === 0) return;

        const currentText = texts[textIndex % texts.length];

        if (isDeleting) {
            // Deleting
            if (subIndex > 0) {
                const timeout = setTimeout(() => {
                    setSubIndex(prev => prev - 1);
                }, deletingSpeed);
                return () => clearTimeout(timeout);
            } else {
                // Done deleting
                const timeout = setTimeout(() => {
                    setIsDeleting(false);
                    setTextIndex(prev => prev + 1);
                }, delayBeforeType);
                return () => clearTimeout(timeout);
            }
        } else {
            // Typing
            if (subIndex < currentText.length) {
                const timeout = setTimeout(() => {
                    setSubIndex(prev => prev + 1);
                }, typingSpeed);
                return () => clearTimeout(timeout);
            } else {
                // Done typing
                const timeout = setTimeout(() => {
                    setIsDeleting(true);
                }, delayBeforeDelete);
                return () => clearTimeout(timeout);
            }
        }
    }, [subIndex, isDeleting, textIndex, texts, typingSpeed, deletingSpeed, delayBeforeDelete, delayBeforeType]);

    return (
        <span className={className}>
            {texts[textIndex % texts.length].substring(0, subIndex)}
            <span className={`${blink ? 'opacity-100' : 'opacity-0'} ml-0.5 font-light`}>|</span>
        </span>
    );
};
