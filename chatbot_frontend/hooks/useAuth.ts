'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

/**
 * Hook for managing authentication state
 * Handles login, logout, and guest mode
 */
export function useAuth() {
    const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
    const [isGuestMode, setIsGuestMode] = useState<boolean>(false);
    const [isLoading, setIsLoading] = useState<boolean>(true);

    // Initialize authentication state on mount
    useEffect(() => {
        console.log('[useAuth] 🔵 Initializing auth state');

        const initAuth = async () => {
            try {
                // Check if user is authenticated via cookie
                await api.me();
                console.log('[useAuth] ✅ User authenticated');
                setIsAuthenticated(true);
                setIsGuestMode(false);
            } catch (err) {
                // Not authenticated - check guest mode
                console.log('[useAuth] ❌ Not authenticated, checking guest mode');
                if (typeof window !== 'undefined') {
                    const guestMode = localStorage.getItem('guest_mode') === 'true';
                    console.log('[useAuth] 🔍 Guest mode:', guestMode);
                    setIsGuestMode(guestMode);
                    setIsAuthenticated(false);
                }
            } finally {
                setIsLoading(false);
            }
        };

        if (typeof window !== 'undefined') {
            initAuth();

            // Clean up guest mode on page close
            const handleBeforeUnload = () => {
                const isGuest = localStorage.getItem('guest_mode') === 'true';
                if (isGuest) {
                    localStorage.removeItem('guest_mode');
                }
            };

            window.addEventListener('beforeunload', handleBeforeUnload);
            return () => window.removeEventListener('beforeunload', handleBeforeUnload);
        } else {
            setIsLoading(false);
        }
    }, []);

    /**
     * Handle successful login
     * Clears guest mode and reloads the page
     */
    const handleLoginSuccess = () => {
        localStorage.removeItem('guest_mode');
        setIsAuthenticated(true);
        setIsGuestMode(false);
        window.location.reload();
    };

    /**
     * Handle logout
     * Calls API logout and reloads the page
     */
    const handleLogout = async () => {
        try {
            await api.logout();
        } catch (e) {
            console.error('Logout error:', e);
        }
        if (typeof window !== 'undefined') {
            localStorage.removeItem('guest_mode');
            window.location.reload();
        }
    };

    /**
     * Activate guest mode
     * Sets guest mode in localStorage and updates state
     */
    const activateGuestMode = () => {
        if (typeof window !== 'undefined') {
            localStorage.setItem('guest_mode', 'true');
            setIsAuthenticated(false);
            setIsGuestMode(true);
            window.dispatchEvent(new Event('guestModeActivated'));
        }
    };

    return {
        isAuthenticated,
        isGuestMode,
        isLoading,
        handleLoginSuccess,
        handleLogout,
        activateGuestMode,
    };
}
