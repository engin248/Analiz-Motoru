'use client';

import React from 'react';
import HistoryItem from './historyItem';
import MenuButton from './menuButton';

interface SidebarProps {
    isVisible: boolean;
    isLocked: boolean;
    onMenuClick: () => void;
    history: Array<{ id: number | string; title: string; isGuest?: boolean }>;
    activeId: number | string | null;
    onSelect: (id: number | string, isGuest?: boolean) => void;
    onConversationDeleted?: (id: number | string) => void;
    onConversationRenamed?: (id: number | string, newTitle: string) => void;
    onNewChat?: () => void;
    // Yeni eklenen props
    userProfile?: {
        full_name?: string | null;
        username?: string;
        email?: string
    };
    avatarUrl?: string;
}

const Sidebar: React.FC<SidebarProps> = ({
    isVisible,
    isLocked,
    onMenuClick,
    history,
    activeId,
    onSelect,
    onConversationDeleted,
    onConversationRenamed,
    onNewChat,
    userProfile,
    avatarUrl
}) => {
    const handleDelete = (convId: number | string) => {
        onConversationDeleted?.(convId);
    };
    const handleRename = (convId: number | string, newTitle: string) => {
        onConversationRenamed?.(convId, newTitle);
    };

    // İsim belirleme
    const displayName = userProfile?.full_name || userProfile?.username || userProfile?.email?.split('@')[0] || "Misafir";
    const displayAvatar = avatarUrl || "/default-avatar.svg";

    return (
        <div className="w-full h-full relative flex flex-col">
            <div className="flex items-center p-4 h-14 justify-between">
                <div className="flex items-center w-full justify-between">
                    {isVisible && (
                        <button
                            onClick={onNewChat}
                            className="flex items-center gap-2 animate-fade-in ml-1 cursor-pointer transition-transform hover:scale-105 active:scale-95 group focus:outline-none"
                            title="Yeni Sohbet Başlat"
                        >
                            <div className="relative w-9 h-9 rounded-full overflow-hidden shadow-[0_0_15px_rgba(16,185,129,0.25)] border-[3px] border-black/80 ring-1 ring-emerald-500/20 group-hover:shadow-[0_0_25px_rgba(16,185,129,0.5)] transition-all duration-300">
                                <img src="/lumora_orb.png" alt="Lumora" className="w-full h-full object-cover" />
                            </div>
                        </button>
                    )}
                    <MenuButton isVisible={isVisible} isLocked={isLocked} onClick={onMenuClick} />
                </div>
            </div>

            {/* "Sohbetler" Title moved down */}
            {isVisible && (
                <div className="px-4 pb-2 pt-6 animate-fade-in">
                    <span className="text-xs font-semibold text-brand-text/50 uppercase tracking-wider">Sohbetler</span>
                </div>
            )}

            {/* New Chat Button (Fixed at top) */}
            {isVisible && onNewChat && (
                <div className="px-3 pb-2 pt-1 flex-shrink-0 animate-fade-in">
                    <button
                        onClick={onNewChat}
                        className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg hover:bg-white/5 transition-all text-white/90 text-sm font-medium border border-white/10 hover:border-white/20 shadow-sm group"
                    >
                        <div className="p-0.5 bg-white/10 rounded-md group-hover:bg-white/20 transition-colors">
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4 text-white">
                                <path d="M21.731 2.269a2.625 2.625 0 00-3.712 0l-1.157 1.157 3.712 3.712 1.157-1.157a2.625 2.625 0 000-3.712zM19.513 8.199l-3.712-3.712-12.15 12.15a5.25 5.25 0 00-1.32 2.214l-.8 2.685a.75.75 0 00.933.933l2.685-.8a5.25 5.25 0 002.214-1.32L19.513 8.2z" />
                            </svg>
                        </div>
                        <span>Yeni sohbet</span>

                        {/* Optional Right Icon (Edit/Plus) */}
                        <div className="ml-auto opacity-0 group-hover:opacity-100 transition-opacity">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4 text-white/50">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
                            </svg>
                        </div>
                    </button>
                </div>
            )}

            <div className={`flex-grow flex flex-col overflow-hidden transition-opacity duration-300 ${isVisible ? 'opacity-100' : 'opacity-0'}`}>
                <div className="px-2 pb-2 overflow-y-auto flex-1 custom-scrollbar">
                    {history.length > 0 ? (
                        <ul className="space-y-1">
                            {history.map(item => (
                                <HistoryItem
                                    key={item.id} id={item.id} title={item.title}
                                    isActive={item.id === activeId} onDelete={handleDelete} onRename={handleRename}
                                    onClick={() => onSelect(item.id, item.isGuest)}
                                />
                            ))}
                        </ul>
                    ) : (
                        <div className="mt-4 px-2 text-left">
                            <p className="text-sm text-brand-text/50">Henüz sohbet geçmişiniz yok.</p>
                        </div>
                    )}
                </div>
            </div>

            {/* User Profile Footer (ChatGPT Style) */}
            {isVisible && (
                <div className="p-3 border-t border-brand-text/10 mt-auto">
                    <div className="flex items-center gap-3 p-2 rounded-xl hover:bg-brand-text/5 transition-colors cursor-pointer group">
                        <img
                            src={displayAvatar}
                            alt="Profile"
                            className="w-8 h-8 rounded-full object-cover ring-1 ring-brand-text/20"
                            onError={(e) => {
                                const target = e.target as HTMLImageElement;
                                target.src = "/default-avatar.svg";
                            }}
                        />
                        <div className="flex flex-col overflow-hidden">
                            <span className="text-sm font-medium text-brand-text truncate">
                                {displayName}
                            </span>
                            <span className="text-xs text-brand-text/50 truncate">
                                {userProfile?.email || "Misafir Kullanıcı"}
                            </span>
                        </div>
                    </div>
                </div>
            )}

            {!isVisible && (
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
                    <span className="text-gray-500 text-xs [writing-mode:vertical-lr] transform rotate-180 select-none">Sohbeti Genişlet</span>
                </div>
            )}
        </div>
    );
};

export default Sidebar;
