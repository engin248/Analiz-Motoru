import React from 'react';

interface MenuButtonProps {
    isVisible: boolean,
    isLocked: boolean,
    onClick: () => void,
    isOpen?: boolean
}

const MenuButton: React.FC<MenuButtonProps> = ({ isVisible, isLocked, onClick }) => {
    const iconColor = isLocked ? 'text-brand-text' : 'text-brand-text/50';

    return (
        <button
            onClick={onClick}
            type="button"
            // Değişiklik burada: cursor-pointer eklendi
            className={`flex items-center justify-center transition-colors duration-150 rounded-lg 
                       hover:bg-brand-emerald/50 focus:outline-none cursor-pointer ${iconColor}
                      ${isVisible ? 'p-2' : 'w-10 h-10'}`}
            title={isLocked ? "Kenar Çubuğunu Sabitle" : "Kenar Çubuğunu Aç/Kapa"}
        >
            {/* İkon */}
            <svg className="w-6 h-6 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16"></path>
            </svg>
        </button>
    );
};

export default MenuButton;