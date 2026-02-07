// components/sidebar/NewChatButton.tsx
import React from 'react';

interface NewChatButtonProps {
    isVisible: boolean,
    onClick: () => void
}

const NewChatButton: React.FC<NewChatButtonProps> = ({isVisible, onClick}) => {
    return (
        <button
            onClick={onClick}
            className={`flex items-center text-sm font-medium transition-all duration-300 ease-in-out flex-shrink-0
                        text-white hover:bg-gray-800 focus:outline-none cursor-pointer p-2
                        ${isVisible
                ? 'w-full rounded-lg justify-start'
                : 'w-10 h-10 rounded-full justify-center pl-5'}`} // <-- GÖRSEL HİZALAMA İÇİN pl-1 EKLENDİ
            title="Yeni Sohbet Başlat"
        >
            {/* İKON */}
            <svg className="w-5 h-5 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                 xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3"
                      d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"></path>
            </svg>

            {/* Metin */}
            <span className={`ml-3 self-center whitespace-nowrap overflow-hidden transition-opacity duration-300 ease-in-out
                            ${isVisible ? 'opacity-100 max-w-xs' : 'opacity-0 max-w-0'}`}
            >
                Yeni Sohbet Başlat
            </span>
        </button>
    );
};

export default NewChatButton;