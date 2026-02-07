// components/Sidebar/HistoryItem.tsx
'use client';
import React, { useState, useRef, useEffect } from 'react';

interface HistoryItemProps {
    id: number | string;
    title: string;
    isActive?: boolean;
    onDelete: (id: number | string) => void;
    onRename: (id: number | string, newTitle: string) => void;
    onClick?: (id: number | string) => void;
}

const RenameIcon = () => (
    <svg className="w-4 h-4 text-brand-text/50 hover:text-brand-text" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
    </svg>
);

const DeleteIcon = () => (
    <svg className="w-4 h-4 text-brand-text/50 hover:text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
    </svg>
);

const HistoryItem: React.FC<HistoryItemProps> = ({ id, title, isActive = false, onDelete, onRename, onClick }) => {
    const [isEditing, setIsEditing] = useState(false);
    const [editValue, setEditValue] = useState(title);
    const inputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        if (isEditing && inputRef.current) {
            inputRef.current.focus();
            inputRef.current.select();
        }
    }, [isEditing]);

    const handleRenameClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        setEditValue(title);
        setIsEditing(true);
    };

    const handleSave = () => {
        const trimmed = editValue.trim();
        if (trimmed && trimmed !== title) {
            onRename(id, trimmed);
        }
        setIsEditing(false);
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            handleSave();
        } else if (e.key === 'Escape') {
            setEditValue(title);
            setIsEditing(false);
        }
    };

    const displayTitle = title.length > 25 ? title.substring(0, 25) + '...' : title;
    const baseClasses = 'flex items-center justify-between p-2 text-sm rounded-lg transition duration-150 group';
    const activeClasses = isActive ? 'bg-brand-emerald text-brand-text font-medium' : 'text-brand-text/80 hover:bg-brand-emerald/50';

    return (
        <li className={`${baseClasses} ${activeClasses}`} onClick={() => !isEditing && onClick?.(id)}>
            {isEditing ? (
                <input
                    ref={inputRef}
                    type="text"
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    onBlur={handleSave}
                    onKeyDown={handleKeyDown}
                    onClick={(e) => e.stopPropagation()}
                    className="flex-grow bg-brand-emerald/80 text-brand-text text-sm px-2 py-1 rounded border border-brand-text/30 focus:outline-none focus:border-brand-text/60"
                    maxLength={50}
                />
            ) : (
                <button type="button" className="flex-grow text-left truncate" title={title}>
                    {displayTitle}
                </button>
            )}
            {!isEditing && (
                <div className="flex items-center space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button onClick={handleRenameClick} title="Yeniden Adlandır">
                        <RenameIcon />
                    </button>
                    <button onClick={(e) => { e.stopPropagation(); onDelete(id); }} title="Sil">
                        <DeleteIcon />
                    </button>
                </div>
            )}
        </li>
    );
};

export default HistoryItem;