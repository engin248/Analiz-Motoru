// components/Chat/MessageList.tsx
import React, { useRef, useEffect } from 'react';
import ChatMessage from './chatMessage';
import { ChatMessage as ChatMessageType } from '@/types/chat';
import TypingIndicator from './typingIndicator'; // Yeni bileşeni import et

interface MessageListProps {
    messages: ChatMessageType[];
    isLoading: boolean; // isLoading prop'unu ekle
    userProfile?: { email?: string; full_name?: string | null; username?: string };
    avatarOverride?: string;
    isGuest?: boolean;
    onRegenerate?: () => void;
}

const MessageList: React.FC<MessageListProps> = ({ messages, isLoading, userProfile, avatarOverride, isGuest, onRegenerate }) => {
    const messagesEndRef = useRef<null | HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    // isLoading durumu değiştiğinde de en alta kaydır
    useEffect(() => {
        scrollToBottom();
    }, [messages, isLoading]);

    return (
        <div className="flex flex-col space-y-4 w-full pt-4 pb-4">
            {messages.map((message) => (
                <ChatMessage
                    key={message.id}
                    message={message}
                    userProfile={userProfile}
                    avatarOverride={avatarOverride}
                    isGuest={isGuest}
                    onRegenerate={onRegenerate}
                />
            ))}

            {/* YENİ: Yükleme durumunda "Yazıyor..." göstergesini render et */}
            {isLoading && <TypingIndicator />}

            <div ref={messagesEndRef} />
        </div>
    );
};

export default MessageList;