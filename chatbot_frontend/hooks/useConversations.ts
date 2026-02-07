'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import { Socket } from 'socket.io-client';
import { ChatMessage } from '@/types/chat';

export interface Conversation {
    id: number | string;
    title: string;
    isGuest: boolean;
}

/**
 * Hook for managing conversation list
 * Handles CRUD operations for conversations
 */
export function useConversations(
    socket: Socket | null,
    isAuthenticated: boolean,
    isGuest: boolean,
    setMessages: (messages: ChatMessage[]) => void,
    setIsLoading: (loading: boolean) => void
) {
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [currentConversationId, setCurrentConversationId] = useState<number | string | null>(null);
    const [guestAlias, setGuestAlias] = useState<string>('Misafir Sohbeti');

    // Load conversations when authenticated
    useEffect(() => {
        if (!isAuthenticated) {
            setConversations([]);
            return;
        }

        const loadConversations = async () => {
            try {
                const list = await api.listConversations();
                setConversations(list.map(c => ({
                    id: c.id,
                    title: c.alias || c.title || `Sohbet ${c.id}`,
                    isGuest: false,
                })));
            } catch (e) {
                console.error('Failed to load conversations:', e);
            }
        };

        loadConversations();
    }, [isAuthenticated]);

    // Setup socket event listeners for guest mode
    useEffect(() => {
        if (!socket || !isGuest) return;

        const handleGuestConversationList = (data: any) => {
            const list = data.conversations || [];
            setConversations(list.map((c: any) => ({
                id: c.id,
                title: c.alias || 'Misafir Sohbeti',
                isGuest: true,
            })));
            if (list.length > 0) {
                setCurrentConversationId(list[0].id);
                setGuestAlias(list[0].alias || 'Misafir Sohbeti');
            }
            setIsLoading(false);
        };

        socket.on('guest_conversation_list', handleGuestConversationList);

        return () => {
            socket.off('guest_conversation_list', handleGuestConversationList);
        };
    }, [socket, isGuest, setIsLoading]);

    // Create new conversation
    const startNewChat = useCallback(async (): Promise<number | string | null> => {
        if (isGuest) {
            if (socket) {
                socket.emit('guest_new_conversation');
            }
            setMessages([]);
            setCurrentConversationId(null);
            setGuestAlias('Misafir Sohbeti');
            return null;
        }

        if (!isAuthenticated) return null;

        try {
            const conversation = await api.createConversation('Yeni Konuşma');
            setCurrentConversationId(conversation.id);
            setMessages([]);
            setConversations(prev => [...prev, {
                id: conversation.id,
                title: conversation.alias || 'Yeni Konuşma',
                isGuest: false
            }]);
            return conversation.id;
        } catch (error) {
            console.error('Failed to create conversation:', error);
            return null;
        }
    }, [isGuest, isAuthenticated, socket, setMessages]);

    // Delete conversation
    const deleteConversation = useCallback(async (conversationId: number | string) => {
        if (!isAuthenticated) return;

        try {
            await api.deleteConversation(Number(conversationId));
            const remaining = conversations.filter(c => c.id !== conversationId);
            setConversations(remaining);

            if (currentConversationId === conversationId) {
                setMessages([]);
                if (remaining.length > 0) {
                    setCurrentConversationId(remaining[0].id);
                    // Load messages for next conversation
                    try {
                        const msgs = await api.getMessages(Number(remaining[0].id));
                        const restored = msgs.map(m => ({
                            id: m.id.toString(),
                            sender: m.sender,
                            content: m.content || '',
                            imageUrl: m.image_url || undefined,
                            timestamp: new Date(m.created_at).getTime(),
                        })) as ChatMessage[];
                        setMessages(restored);
                    } catch (e) {
                        console.error('Failed to load messages:', e);
                    }
                } else {
                    setCurrentConversationId(null);
                }
            }
        } catch (e) {
            console.error('Failed to delete conversation:', e);
        }
    }, [isAuthenticated, conversations, currentConversationId, setMessages]);

    // Load conversation messages
    const loadConversation = useCallback(async (conversationId: number | string, isGuestConversation: boolean) => {
        if (isGuestConversation) {
            if (socket) {
                setIsLoading(true);
                socket.emit('guest_get_conversation', { conversation_id: conversationId });
            }
            return;
        }

        if (!isAuthenticated) return;

        try {
            setIsLoading(true);
            const msgs = await api.getMessages(Number(conversationId));
            const restored: ChatMessage[] = msgs.map(m => ({
                id: m.id.toString(),
                sender: m.sender,
                content: m.content || '',
                imageUrl: m.image_url || undefined,
                timestamp: new Date(m.created_at).getTime(),
            }));
            setMessages(restored);
            setCurrentConversationId(conversationId);
        } catch (e) {
            console.error('Failed to load conversation:', e);
        } finally {
            setIsLoading(false);
        }
    }, [isAuthenticated, socket, setMessages, setIsLoading]);

    return {
        conversations,
        setConversations,
        currentConversationId,
        setCurrentConversationId,
        guestAlias,
        setGuestAlias,
        startNewChat,
        deleteConversation,
        loadConversation,
    };
}
