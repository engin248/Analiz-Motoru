'use client';

import React, { useState, useRef, useEffect } from 'react';
import Sidebar from '@/components/sidebar/sidebar';
import MessageList from '@/components/chat/messageList';
import UserMenu from '@/components/header/userMenu';
import { Typewriter } from '@/components/ui/typewriter';
import { useChat } from '@/hooks/useChat';
import { useAuth } from '@/hooks/useAuth';
import { useProfile } from '@/hooks/useProfile';
import LoginForm from '@/components/auth/loginForm';
import TextSelectionPopup from '@/components/chat/textSelectionPopup';
import type { ApiUser } from '@/lib/api';
import { api } from '@/lib/api';

export default function Home() {
    // Authentication
    const { isAuthenticated, isGuestMode, isLoading: isAuthLoading, handleLoginSuccess, handleLogout, activateGuestMode } = useAuth();

    // User Profile
    const { userProfile, avatarUrl, handleChangePassword, handleAvatarChange } = useProfile(isAuthenticated);

    const [isMounted, setIsMounted] = useState(false);

    const { messages, isLoading: isChatLoading, sendMessage, startNewChat, deleteConversation, isChatStarted, inputText, setInputText, isGuest, currentConversationId, guestAlias, conversations, loadConversation, stopGeneration, setConversations } = useChat(isAuthenticated, isGuestMode);

    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const [isSidebarLocked, setIsSidebarLocked] = useState(true);
    const [isAttachMenuOpen, setIsAttachMenuOpen] = useState(false);
    const [isImageGenerationMode, setIsImageGenerationMode] = useState(false);
    const [isHovered, setIsHovered] = useState(false);
    const isSidebarVisible = isSidebarLocked || isHovered;

    // Quote (Alıntı) State - AI'a Sor özelliği için
    const [quotedText, setQuotedText] = useState<string>('');
    const messageListRef = useRef<HTMLDivElement>(null);

    const handleConversationRename = async (id: number | string, newTitle: string) => {
        // Update local state immediately
        setConversations(prev => prev.map(c => c.id === id ? { ...c, title: newTitle } : c));

        // Try to update on backend (if authenticated)
        if (isAuthenticated) {
            try {
                await api.updateConversation(Number(id), { alias: newTitle });
            } catch (e) {
                console.error('Konuşma adı kaydedilemedi', e);
            }
        }
    };

    // File Upload State
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setSelectedFile(e.target.files[0]);
        }
    };

    // Initialize mounted state
    useEffect(() => {
        setIsMounted(true);
    }, []);


    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            const scrollHeight = textareaRef.current.scrollHeight;
            textareaRef.current.style.height = `${scrollHeight}px`;
        }
    }, [inputText]);

    useEffect(() => {
        if (!isChatLoading && textareaRef.current) {
            textareaRef.current.focus();
        }
    }, [isChatLoading]);

    // 1. Loading State Check (Prevents Login Flash)
    // Sadece Auth kontrolü sırasında veya sayfa mount edilirken göster
    if (!isMounted || isAuthLoading) {
        return (
            <div className="flex h-screen w-screen bg-brand-bg items-center justify-center">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-12 h-12 border-4 border-brand-emerald border-t-transparent rounded-full animate-spin"></div>
                    <div className="text-brand-emerald text-lg animate-pulse">Yükleniyor...</div>
                </div>
            </div>
        );
    }

    const handleMenuClick = () => setIsSidebarLocked(prev => !prev);

    const handleInputSubmit = async (e: React.FormEvent | React.KeyboardEvent) => {
        e.preventDefault();
        if (isChatLoading) return;
        const messageToSend = inputText.trim();

        if (messageToSend || selectedFile || quotedText) {
            let fileUrl: string | undefined = undefined;

            if (selectedFile) {
                try {
                    const uploadRes = await api.uploadFile(selectedFile);
                    fileUrl = uploadRes.url;
                } catch (error) {
                    console.error('Dosya yükleme hatası:', error);
                }
            }

            // Quote varsa mesaja markdown blockquote formatında ekle
            // Bu format tüm LLM'ler tarafından evrensel olarak anlaşılır
            const finalMessage = quotedText
                ? `> ${quotedText.split('\n').join('\n> ')}\n\n${messageToSend}`.trim()
                : messageToSend;

            sendMessage(finalMessage, fileUrl ? [fileUrl] : undefined, isImageGenerationMode);
        }

        setInputText('');
        setSelectedFile(null);
        setQuotedText(''); // Quote'u temizle
        setIsImageGenerationMode(false);
        if (fileInputRef.current) fileInputRef.current.value = '';
        setTimeout(() => {
            textareaRef.current?.focus();
        }, 0);
    };

    const handleRegenerate = async () => {
        if (isChatLoading) return;
        // Son kullanıcı mesajını bul
        const lastUserMessage = [...messages].reverse().find(m => m.sender === 'user');
        if (lastUserMessage) {
            await sendMessage(lastUserMessage.content);
        }
    };

    // Quote handler - metin seçildiğinde çağrılır
    const handleQuote = (text: string) => {
        setQuotedText(text);
        textareaRef.current?.focus();
    };

    const renderForm = () => {
        const canSend = (inputText.trim() || quotedText) && !isChatLoading;
        return (
            <form onSubmit={handleInputSubmit} className="w-full mx-auto relative">
                <input
                    type="file"
                    ref={fileInputRef}
                    className="hidden"
                    onChange={handleFileSelect}
                    accept="image/*,.pdf,.doc,.docx"
                />
                {selectedFile && (
                    <div className="absolute bottom-full left-0 mb-3 ml-2 flex items-center gap-2 bg-[#2F2F2F] px-3 py-2 rounded-lg border border-white/10 shadow-lg animate-fade-in z-10 max-w-xs">
                        <div className="p-1.5 bg-brand-emerald/10 rounded-full">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4 text-emerald-500">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M18.375 12.739l-7.693 7.693a4.5 4.5 0 01-6.364-6.364l10.94-10.94A3 3 0 1119.5 7.372L8.552 18.32m.009-.01l-.01.01m5.699-9.941l-7.81 7.81a1.5 1.5 0 002.112 2.13" />
                            </svg>
                        </div>
                        <span className="text-sm text-gray-200 truncate">{selectedFile?.name}</span>
                        <button
                            type="button"
                            onClick={() => {
                                setSelectedFile(null);
                                if (fileInputRef.current) fileInputRef.current.value = '';
                            }}
                            className="ml-auto text-gray-400 hover:text-white p-1"
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                                <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
                            </svg>
                        </button>
                    </div>
                )}

                {/* Ana Input Container - ChatGPT tarzı birleşik tasarım */}
                <div className={`relative w-full bg-[#2F2F2F] shadow-lg transition-all duration-200 ${quotedText ? 'rounded-2xl' : 'rounded-3xl'}`}>

                    {/* Quote Bölümü - Input'un içinde, üstte */}
                    {quotedText && (
                        <div className="flex items-start gap-3 px-4 pt-3 pb-2 border-b border-white/5 animate-slide-down">
                            {/* Geri ok ikonu */}
                            <div className="flex-shrink-0 mt-0.5 text-white/50">
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 15L3 9m0 0l6-6M3 9h12a6 6 0 010 12h-3" />
                                </svg>
                            </div>

                            {/* Alıntı metni */}
                            <div className="flex-1 min-w-0">
                                <span className="text-sm text-white/70 line-clamp-2">
                                    &ldquo;{quotedText.length > 120 ? quotedText.substring(0, 120) + '...' : quotedText}&rdquo;
                                </span>
                            </div>

                            {/* Kapat butonu */}
                            <button
                                type="button"
                                onClick={() => setQuotedText('')}
                                className="flex-shrink-0 p-1 hover:bg-white/10 rounded-lg transition-colors text-white/40 hover:text-white"
                                title="Alıntıyı kaldır"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                                    <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
                                </svg>
                            </button>
                        </div>
                    )}

                    {/* Input Alanı */}
                    <div className="relative flex items-center">
                        {/* Plus Button with Menu */}
                        <div className="absolute left-2 bottom-2 z-20">
                            {isAttachMenuOpen && (
                                <>
                                    <div className="fixed inset-0 z-40" onClick={() => setIsAttachMenuOpen(false)} />
                                    <div className="absolute bottom-full -left-2 mb-4 w-64 bg-[#2F2F2F] border border-white/10 rounded-xl shadow-xl overflow-hidden animate-slide-up z-50">
                                        <div className="p-1.5">
                                            <button
                                                type="button"
                                                className="w-full flex items-center gap-3 px-3 py-2.5 text-sm text-white/90 hover:bg-white/10 rounded-lg transition-colors text-left group"
                                                onClick={() => {
                                                    setIsAttachMenuOpen(false);
                                                    fileInputRef.current?.click();
                                                }}
                                            >
                                                <div className="p-2 bg-white/5 rounded-full group-hover:bg-white/10 transition-colors">
                                                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5 text-white/80">
                                                        <path strokeLinecap="round" strokeLinejoin="round" d="M18.375 12.739l-7.693 7.693a4.5 4.5 0 01-6.364-6.364l10.94-10.94A3 3 0 1119.5 7.372L8.552 18.32m.009-.01l-.01.01m5.699-9.941l-7.81 7.81a1.5 1.5 0 002.112 2.13" />
                                                    </svg>
                                                </div>
                                                <span>Fotoğraf ve dosya ekle</span>
                                            </button>

                                            <button
                                                type="button"
                                                className="w-full flex items-center gap-3 px-3 py-2.5 text-sm text-white/90 hover:bg-white/10 rounded-lg transition-colors text-left group"
                                                onClick={() => {
                                                    setIsAttachMenuOpen(false);
                                                    setIsImageGenerationMode(true);
                                                    textareaRef.current?.focus();
                                                }}
                                            >
                                                <div className="p-2 bg-white/5 rounded-full group-hover:bg-white/10 transition-colors">
                                                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5 text-white/80">
                                                        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 001.5-1.5V6a1.5 1.5 0 00-1.5-1.5H3.75A1.5 1.5 0 002.25 6v12a1.5 1.5 0 001.5 1.5zm10.5-11.25h.008v.008h-.008V8.25zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z" />
                                                    </svg>
                                                </div>
                                                <span>Görsel oluştur</span>
                                            </button>
                                        </div>
                                    </div>
                                </>
                            )}

                            <button
                                type="button"
                                onClick={() => setIsAttachMenuOpen(!isAttachMenuOpen)}
                                className={`p-2 rounded-lg transition-all duration-200 ${isAttachMenuOpen ? 'bg-white/20 rotate-45' : 'hover:bg-white/10'}`}
                                title={isAttachMenuOpen ? "Kapat" : "Ekle"}
                            >
                                <svg className="w-6 h-6 text-white/70" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                                </svg>
                            </button>
                        </div>

                        <textarea
                            ref={textareaRef}
                            rows={1}
                            value={inputText}
                            onChange={(e) => setInputText(e.target.value)}
                            onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleInputSubmit(e); } }}
                            disabled={isChatLoading}
                            placeholder={quotedText ? "Herhangi bir şey sor" : (isImageGenerationMode ? "Bir görseli tanımla veya düzenle" : "Mesajınızı yazın...")}
                            className={`w-full pr-24 pl-14 bg-transparent text-white/90 border-0 focus:outline-none focus:ring-0 placeholder:text-white/40 resize-none overflow-y-auto transition-all duration-200 ${isImageGenerationMode ? 'pt-4 pb-12' : 'py-4'}`}
                            style={{ minHeight: '56px', maxHeight: '120px' }}
                            onClick={() => setIsAttachMenuOpen(false)}
                        />

                        {/* Image Generation Mode Pill */}
                        {isImageGenerationMode && (
                            <div className="absolute left-14 bottom-2.5 z-20">
                                <div className="flex items-center gap-1.5 px-2 py-1 bg-white/10 rounded-lg border border-white/5 animate-slide-up text-xs font-medium text-white/90 shadow-sm">
                                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-3.5 h-3.5 text-white/80">
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 001.5-1.5V6a1.5 1.5 0 00-1.5-1.5H3.75A1.5 1.5 0 002.25 6v12a1.5 1.5 0 001.5 1.5zm10.5-11.25h.008v.008h-.008V8.25zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z" />
                                    </svg>
                                    <span>Görsel</span>
                                    <button
                                        type="button"
                                        onClick={() => setIsImageGenerationMode(false)}
                                        className="ml-1 p-0.5 hover:bg-white/20 rounded-full transition-colors"
                                    >
                                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-3 h-3">
                                            <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
                                        </svg>
                                    </button>
                                </div>
                            </div>
                        )}

                        {/* Right Buttons Container */}
                        <div className="absolute right-2 bottom-2 flex items-center gap-1">
                            {/* Microphone Button */}
                            <button
                                type="button"
                                className="p-2 rounded-lg hover:bg-white/10 transition-colors"
                                title="Ses kaydı"
                            >
                                <svg className="w-5 h-5 text-white/70" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z" />
                                </svg>
                            </button>

                            {/* Send/Stop Button */}
                            <button
                                onClick={(e) => {
                                    if (isChatLoading) {
                                        e.preventDefault();
                                        stopGeneration();
                                    }
                                }}
                                type={isChatLoading ? "button" : "submit"}
                                disabled={!isChatLoading && !canSend}
                                className={`p-2.5 rounded-lg transition-all duration-200 
                                    ${isChatLoading
                                        ? "bg-white hover:bg-white/90"
                                        : canSend
                                            ? "bg-white hover:bg-white/90"
                                            : "bg-white/20 cursor-not-allowed"
                                    }`}
                                title={isChatLoading ? "Durdur" : "Mesajı gönder"}
                            >
                                {isChatLoading ? (
                                    <div className="flex items-center justify-center w-5 h-5">
                                        <span className="block w-3 h-3 bg-[#2F2F2F] rounded-sm"></span>
                                    </div>
                                ) : (
                                    <svg className={`w-5 h-5 ${canSend ? 'text-[#2F2F2F]' : 'text-white/40'}`} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                                        <path d="M3.478 2.405a.75.75 0 00-.926.94l2.432 7.905H13.5a.75.75 0 010 1.5H4.984l-2.432 7.905a.75.75 0 00.926.94 60.519 60.519 0 0018.445-8.986.75.75 0 000-1.218A60.517 60.517 0 003.478 2.405z" />
                                    </svg>
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            </form>
        );
    };

    // 1. Loading State Check (Prevents Login Flash)
    // Sadece Auth kontrolü sırasında, sayfa mount edilirken veya sohbet yüklenirken göster
    if (!isMounted || isAuthLoading || (isChatLoading && !isChatStarted)) {
        return (
            <div className="flex h-screen w-screen bg-brand-bg items-center justify-center">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-12 h-12 border-4 border-brand-emerald border-t-transparent rounded-full animate-spin"></div>
                    <div className="text-brand-emerald text-lg animate-pulse">Yükleniyor...</div>
                </div>
            </div>
        );
    }

    // 2. Auth Check
    if (!isAuthenticated && !isGuestMode) {
        return (
            <div className="flex h-screen w-screen bg-brand-bg items-center justify-center">
                <LoginForm onLoginSuccess={handleLoginSuccess} onGuestMode={activateGuestMode} />
            </div>
        );
    }

    return (
        <div className="flex h-screen w-screen bg-brand-bg overflow-hidden relative">
            {/* Sidebar (Sol) */}
            <div
                onMouseEnter={() => !isSidebarLocked && setIsHovered(true)}
                onMouseLeave={() => !isSidebarLocked && setIsHovered(false)}
                className={`h-full bg-brand-sidebar/95 backdrop-blur-xl border-r border-brand-text/20 transition-all duration-300 ease-in-out 
                           ${isSidebarVisible ? 'w-64' : 'w-16'} flex-shrink-0 z-30 shadow-2xl text-brand-text`}
            >
                <Sidebar
                    isVisible={isSidebarVisible}
                    isLocked={isSidebarLocked}
                    onMenuClick={handleMenuClick}
                    history={conversations}
                    activeId={currentConversationId}
                    onSelect={(id, isGuestConversation) => loadConversation(id, !!isGuestConversation)}
                    onConversationDeleted={(id) => deleteConversation(id)}
                    onConversationRenamed={handleConversationRename}
                    onNewChat={startNewChat}
                    userProfile={userProfile || undefined}
                    avatarUrl={avatarUrl || undefined}
                />
            </div>

            {/* Ana İçerik Alanı */}
            <div className="flex-1 flex flex-col relative h-full overflow-hidden">

                {/* Header (Sağ Üst) */}
                <header className="absolute top-0 right-0 z-20 p-4 flex justify-end items-center w-full pointer-events-none">
                    <div className="pointer-events-auto">
                        <UserMenu
                            userProfile={userProfile || undefined}
                            isGuest={isGuestMode || isGuest}
                            guestAlias={guestAlias}
                            avatarOverride={avatarUrl || undefined}
                            onLogout={handleLogout}
                            onChangePassword={handleChangePassword}
                            onAvatarChange={handleAvatarChange}
                            onNewChat={startNewChat}
                        />
                    </div>
                </header>

                {/* Arka plan efekti - Sarı zemin üzerinde hafif bir doku veya temiz bırak */}
                <div className="absolute inset-0 bg-transparent pointer-events-none" />

                <main className="flex-1 overflow-hidden relative flex flex-col pt-16">
                    {!isChatStarted && (
                        <div className="flex flex-col items-center justify-center h-full text-center px-4 pb-20">
                            <div className="pb-12 animate-fade-in">
                                <div className="mb-10 flex flex-col items-center justify-center gap-6">
                                    <div className="relative w-32 h-32 rounded-full bg-black shadow-[0_0_60px_rgba(16,185,129,0.6)] animate-fade-in overflow-hidden border border-emerald-500/30">
                                        <img
                                            src="/lumora_orb.png"
                                            alt="Lumora Logo"
                                            className="w-full h-full object-cover"
                                        />
                                    </div>
                                    <h1 className="text-6xl font-bold text-white tracking-tight">
                                        LUMORA AI
                                    </h1>
                                </div>

                                {/* Sabit yükseklik vererek titremeyi engelliyoruz */}
                                <div className="text-2xl text-white/90 mb-2 h-[4.5rem] flex items-center justify-center w-full max-w-4xl mx-auto">
                                    <Typewriter
                                        texts={[
                                            "Global moda trendlerini anlık olarak takip edin 🌍",
                                            "En çok satan (Best-Seller) ürünleri analiz edin 📈",
                                            "Gelecek sezonun renk ve desenlerini keşfedin 🎨",
                                            "Rakip analizi ile pazarın bir adım önünde olun 🚀",
                                            "Veriye dayalı koleksiyonlar tasarlayın ✨"
                                        ]}
                                        typingSpeed={40}
                                        deletingSpeed={25}
                                        delayBeforeDelete={2500}
                                        className="inline-block"
                                    />
                                </div>
                            </div>
                            <div className="w-full max-w-3xl animate-slide-up relative z-10">
                                {isGuestMode && (
                                    <div className="mb-4 text-sm text-white/80 bg-white/10 border border-white/30 rounded-xl px-4 py-3">
                                        Misafir modundasınız. Sohbet geçmişiniz kaydedilmeyecek.
                                    </div>
                                )}
                                {renderForm()}
                                <p className="mt-6 text-sm text-white/70 animate-fade-in">Sorularınızı sorun ve anında yanıt alın</p>
                            </div>
                        </div>
                    )}

                    {isChatStarted && (
                        <>
                            <div className="flex-1 overflow-y-auto w-full relative z-10 custom-scrollbar">
                                <div ref={messageListRef} className="w-full max-w-6xl mx-auto px-4 py-6">
                                    <MessageList
                                        messages={messages}
                                        isLoading={isChatLoading}
                                        userProfile={userProfile || undefined}
                                        avatarOverride={avatarUrl || undefined}
                                        isGuest={isGuestMode || isGuest}
                                        onRegenerate={handleRegenerate}
                                    />
                                </div>

                                {/* Text Selection Popup - Metin seçildiğinde gösterilir */}
                                <TextSelectionPopup
                                    containerRef={messageListRef}
                                    onQuote={handleQuote}
                                />
                            </div>

                            <div className="pt-4 pb-6 w-full max-w-6xl mx-auto px-4 relative z-10">
                                {renderForm()}
                            </div>
                        </>
                    )}
                </main>
            </div >
        </div >
    );
}
