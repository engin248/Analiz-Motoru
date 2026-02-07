'use client';

import { useState, useEffect, useRef } from 'react';
import { api, type ApiUser } from '@/lib/api';

/**
 * Hook for managing user profile data
 * Fetches and caches user profile when authenticated
 */
const API_BASE = process.env.NEXT_PUBLIC_BACKEND_URL?.replace(/\/$/, '') || 'http://localhost:8000';

/**
 * Hook for managing user profile data
 * Fetches and caches user profile when authenticated
 */
export function useProfile(isAuthenticated: boolean) {
    const [userProfile, setUserProfile] = useState<ApiUser | null>(null);
    const [avatarUrl, setAvatarUrl] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);
    const hasFetchedRef = useRef<boolean>(false);

    const normalizeUrl = (url: string | null) => {
        if (!url) return null;
        if (url.startsWith('http') || url.startsWith('blob:')) return url;
        if (url.startsWith('/')) return `${API_BASE}${url}`;
        return url;
    };

    // Load avatar from localStorage
    useEffect(() => {
        if (typeof window !== 'undefined') {
            const stored = localStorage.getItem('avatar_override_url');
            if (stored) setAvatarUrl(normalizeUrl(stored));
        }
    }, []);

    // Fetch profile when authenticated
    useEffect(() => {
        console.log('[useProfile] 🟡 fetchProfile useEffect, isAuthenticated=', isAuthenticated);

        if (!isAuthenticated) {
            console.log('[useProfile] 🟡 Not authenticated, clearing profile');
            setUserProfile(null);
            setError(null);
            hasFetchedRef.current = false;
            return;
        }

        // Avoid re-fetching if already fetched
        if (hasFetchedRef.current) {
            return;
        }

        let isCancelled = false;

        const fetchProfile = async () => {
            console.log('[useProfile] 🟡 Fetching profile...');
            setIsLoading(true);
            setError(null);

            try {
                const me = await api.me();
                if (!isCancelled) {
                    console.log('[useProfile] ✅ Profile fetched successfully');
                    setUserProfile(me);

                    // Sync avatar from profile if no override in local storage
                    const stored = typeof window !== 'undefined' ? localStorage.getItem('avatar_override_url') : null;
                    if (!stored && me.avatar_url) {
                        setAvatarUrl(normalizeUrl(me.avatar_url));
                    }

                    hasFetchedRef.current = true;
                }
            } catch (e: any) {
                if (!isCancelled) {
                    console.error('[useProfile] ❌ Profile fetch FAILED:', e);
                    setError(e.message || 'Profil yüklenemedi');
                }
            } finally {
                if (!isCancelled) {
                    setIsLoading(false);
                }
            }
        };

        fetchProfile();

        return () => {
            isCancelled = true;
        };
    }, [isAuthenticated]);

    /**
     * Change user avatar
     */
    const handleAvatarChange = (url: string | null) => {
        if (typeof window !== 'undefined') {
            if (url) {
                localStorage.setItem('avatar_override_url', url);
            } else {
                localStorage.removeItem('avatar_override_url');
            }
        }
        setAvatarUrl(normalizeUrl(url));
    };

    /**
     * Change user password
     */
    const handleChangePassword = async (currentPassword: string, newPassword: string) => {
        await api.changePassword(currentPassword, newPassword);
    };

    return {
        userProfile,
        avatarUrl,
        isLoading,
        error,
        handleAvatarChange,
        handleChangePassword,
    };
}
