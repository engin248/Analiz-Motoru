'use client';

import { useEffect, useRef, useState } from 'react';
import { Socket, io } from 'socket.io-client';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL?.replace(/\/$/, '') || 'http://localhost:8000';

/**
 * Hook for managing Socket.IO connection
 * Handles connection lifecycle and event listeners
 */
export function useSocket(isGuest: boolean, isAuthenticated: boolean) {
    const socketRef = useRef<Socket | null>(null);
    const [isConnected, setIsConnected] = useState(false);

    useEffect(() => {
        if (typeof window === 'undefined') return;

        const guestMode = localStorage.getItem('guest_mode') === 'true';
        const shouldConnect = isAuthenticated || (isGuest && guestMode);

        if (!shouldConnect) {
            // Disconnect if conditions not met
            if (socketRef.current) {
                socketRef.current.disconnect();
                socketRef.current = null;
                setIsConnected(false);
            }
            return;
        }

        // Don't reconnect if already connected
        if (socketRef.current?.connected) {
            return;
        }

        // Create socket connection
        const socketOptions: any = {
            transports: ['websocket', 'polling'],
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionAttempts: 5
        };

        socketRef.current = io(BACKEND_URL, socketOptions);
        const socket = socketRef.current;

        socket.on('connect', () => {
            setIsConnected(true);
        });

        socket.on('disconnect', () => {
            setIsConnected(false);
        });

        socket.on('connect_error', (error) => {
            console.error('Socket connection error:', error?.message || error);
            setIsConnected(false);
        });

        // Cleanup on unmount
        return () => {
            if (socket) {
                socket.disconnect();
                setIsConnected(false);
            }
        };
    }, [isGuest, isAuthenticated]);

    return {
        socket: socketRef.current,
        isConnected,
    };
}
