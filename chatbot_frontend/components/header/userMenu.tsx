'use client';

import React, { useState } from 'react';
import { api } from '@/lib/api';
import { useTheme } from '../ThemeContext';

interface UserMenuProps {
    userProfile?: { username: string; email: string; full_name?: string | null };
    isGuest?: boolean;
    guestAlias?: string | null;
    avatarOverride?: string;
    onLogout?: () => void;
    onChangePassword?: (currentPassword: string, newPassword: string) => Promise<void>;
    onAvatarChange?: (url: string | null) => void;
    onNewChat?: () => void;
}

const UserMenu: React.FC<UserMenuProps> = ({
    userProfile,
    isGuest,
    guestAlias,
    avatarOverride,
    onLogout,
    onChangePassword,
    onAvatarChange,
    onNewChat
}) => {
    const { theme, toggleTheme } = useTheme();
    const [isProfileOpen, setIsProfileOpen] = useState(false);
    const [showChangePassword, setShowChangePassword] = useState(false);
    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [pwdMessage, setPwdMessage] = useState<string | null>(null);
    const [pwdError, setPwdError] = useState<string | null>(null);
    const [pwdLoading, setPwdLoading] = useState(false);
    const [avatarInput, setAvatarInput] = useState(avatarOverride || '');
    const [isUploading, setIsUploading] = useState(false);

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        try {
            setIsUploading(true);
            const user = await api.uploadAvatar(file);
            if (user.avatar_url && onAvatarChange) {
                onAvatarChange(user.avatar_url);
            }
        } catch (error) {
            console.error('Avatar yükleme hatası:', error);
        } finally {
            setIsUploading(false);
        }
    };

    const md5 = (str: string) => {
        const utf8 = new TextEncoder().encode(str);
        const r = (x: number, n: number) => (x << n) | (x >>> (32 - n));
        const k = [0xd76aa478, 0xe8c7b756, 0x242070db, 0xc1bdceee, 0xf57c0faf, 0x4787c62a, 0xa8304613, 0xfd469501, 0x698098d8, 0x8b44f7af, 0xffff5bb1, 0x895cd7be, 0x6b901122, 0xfd987193, 0xa679438e, 0x49b40821, 0xf61e2562, 0xc040b340, 0x265e5a51, 0xe9b6c7aa, 0xd62f105d, 0x02441453, 0xd8a1e681, 0xe7d3fbc8, 0x21e1cde6, 0xc33707d6, 0xf4d50d87, 0x455a14ed, 0xa9e3e905, 0xfcefa3f8, 0x676f02d9, 0x8d2a4c8a, 0xfffa3942, 0x8771f681, 0x6d9d6122, 0xfde5380c, 0xa4beea44, 0x4bdecfa9, 0xf6bb4b60, 0xbebfbc70, 0x289b7ec6, 0xeaa127fa, 0xd4ef3085, 0x04881d05, 0xd9d4d039, 0xe6db99e5, 0x1fa27cf8, 0xc4ac5665, 0xf4292244, 0x432aff97, 0xab9423a7, 0xfc93a039, 0x655b59c3, 0x8f0ccc92, 0xffeff47d, 0x85845dd1, 0x6fa87e4f, 0xfe2ce6e0, 0xa3014314, 0x4e0811a1, 0xf7537e82, 0xbd3af235, 0x2ad7d2bb, 0xeb86d391];
        const s = [7, 12, 17, 22, 5, 9, 14, 20, 4, 11, 16, 23, 6, 10, 15, 21];
        const m: number[] = [];
        for (let i = 0; i < utf8.length; i++) m[i >> 2] |= utf8[i] << ((i % 4) * 8);
        const l = utf8.length * 8;
        m[l >> 5] |= 0x80 << (l % 32);
        m[((l + 64 >>> 9) << 4) + 14] = l;
        let a = 1732584193, b = -271733879, c = -1732584194, d = 271733878;
        for (let i = 0; i < m.length; i += 16) {
            const [oa, ob, oc, od] = [a, b, c, d];
            for (let j = 0; j < 64; j++) {
                let f: number, g: number;
                if (j < 16) { f = (b & c) | (~b & d); g = j; }
                else if (j < 32) { f = (d & b) | (~d & c); g = (5 * j + 1) % 16; }
                else if (j < 48) { f = b ^ c ^ d; g = (3 * j + 5) % 16; }
                else { f = c ^ (b | ~d); g = (7 * j) % 16; }
                const tmp = d; d = c; c = b; b = b + r((a + f + k[j] + (m[i + g] | 0)) | 0, s[(j >> 4) * 4 + (j % 4)]); a = tmp;
            }
            a = (a + oa) | 0; b = (b + ob) | 0; c = (c + oc) | 0; d = (d + od) | 0;
        }
        return (a >>> 0).toString(16).padStart(8, '0') + (b >>> 0).toString(16).padStart(8, '0') + (c >>> 0).toString(16).padStart(8, '0') + (d >>> 0).toString(16).padStart(8, '0');
    };

    const defaultAvatar = '/default-avatar.svg';
    const { avatarUrl, fallbackAvatar } = (() => {
        if (isGuest) return { avatarUrl: defaultAvatar, fallbackAvatar: defaultAvatar };
        if (avatarOverride) return { avatarUrl: avatarOverride, fallbackAvatar: avatarOverride };
        const email = userProfile?.email?.trim().toLowerCase();
        if (!email) return { avatarUrl: defaultAvatar, fallbackAvatar: defaultAvatar };
        const hash = md5(email);
        const gravUrl = `https://www.gravatar.com/avatar/${hash}?d=404`;
        return { avatarUrl: gravUrl, fallbackAvatar: defaultAvatar };
    })();

    return (
        <div className="relative">
            <img
                src={avatarUrl}
                onError={(e) => {
                    const target = e.target as HTMLImageElement;
                    if (target.src !== fallbackAvatar) target.src = fallbackAvatar;
                }}
                onClick={() => setIsProfileOpen(prev => !prev)}
                className="w-10 h-10 rounded-full object-cover shadow-lg border border-white/10 cursor-pointer hover:ring-2 hover:ring-blue-500/50 transition-all"
                title="Profil"
                alt="Profil"
            />
            {isProfileOpen && (
                <div className="absolute right-0 top-full mt-2 w-72 bg-brand-emerald/95 border border-brand-emerald rounded-xl shadow-2xl p-4 z-50 space-y-3 backdrop-blur-xl">
                    <div className="text-sm font-semibold text-brand-text mb-1">
                        {isGuest ? 'Misafir Sohbeti' : (userProfile?.full_name || userProfile?.username || 'Kullanıcı')}
                    </div>
                    <div className="text-xs text-brand-text/70 mb-3 truncate">
                        {isGuest ? 'Misafir modunda' : (userProfile?.email || '')}
                    </div>

                    {!showChangePassword && (
                        <div className="space-y-3">
                            {!isGuest && (
                                <div className="space-y-2">
                                    <label className="text-xs text-brand-text/70">Profil Fotoğrafı</label>
                                    <div className="flex flex-col gap-2">
                                        <label className={`
                                            flex items-center justify-center w-full p-3 border border-dashed border-brand-emerald/50 rounded-lg 
                                            cursor-pointer hover:bg-brand-emerald/10 transition-colors
                                            ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}
                                        `}>
                                            <input
                                                type="file"
                                                accept="image/*"
                                                onChange={handleFileUpload}
                                                className="hidden"
                                                disabled={isUploading}
                                            />
                                            {isUploading ? (
                                                <div className="flex items-center gap-2 text-xs text-brand-text/70">
                                                    <div className="w-3 h-3 border-2 border-brand-text/30 border-t-brand-text rounded-full animate-spin" />
                                                    Yükleniyor...
                                                </div>
                                            ) : (
                                                <div className="flex items-center gap-2 text-xs text-brand-text/70">
                                                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                                                    </svg>
                                                    Bilgisayardan Seç
                                                </div>
                                            )}
                                        </label>

                                        <div className="flex items-center justify-between">
                                            <button
                                                onClick={() => onAvatarChange?.(null)}
                                                className="text-xs text-brand-text/50 hover:text-brand-text transition-colors"
                                                disabled={isUploading}
                                            >
                                                Varsayılanı kullan
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            )}

                            <div className="grid grid-cols-1 gap-2 text-xs">
                                {!isGuest && (
                                    <button
                                        onClick={() => setShowChangePassword(true)}
                                        className="w-full px-3 py-2 bg-brand-emerald/50 hover:bg-brand-emerald rounded-lg text-brand-text text-left border border-brand-emerald"
                                    >
                                        Şifre Değiştir
                                    </button>
                                )}
                                <div className="pt-2 pb-1 border-t border-brand-emerald/50">
                                    <div className="text-[10px] text-brand-text/50 uppercase tracking-wider mb-2 px-1">Tema</div>
                                    <div className="grid grid-cols-2 gap-2">
                                        <button
                                            onClick={() => theme !== 'light' && toggleTheme()}
                                            className={`
                                                flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-xs font-medium transition-all
                                                ${theme === 'light'
                                                    ? 'bg-brand-text text-brand-bg shadow-sm ring-1 ring-brand-text/50'
                                                    : 'bg-brand-emerald/30 text-brand-text/70 hover:bg-brand-emerald/50 hover:text-brand-text'
                                                }
                                            `}
                                        >
                                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                                            </svg>
                                            Aydınlık
                                        </button>
                                        <button
                                            onClick={() => theme !== 'dark' && toggleTheme()}
                                            className={`
                                                flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-xs font-medium transition-all
                                                ${theme === 'dark'
                                                    ? 'bg-brand-text text-brand-bg shadow-sm ring-1 ring-brand-text/50'
                                                    : 'bg-brand-emerald/30 text-brand-text/70 hover:bg-brand-emerald/50 hover:text-brand-text'
                                                }
                                            `}
                                        >
                                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                                            </svg>
                                            Karanlık
                                        </button>
                                    </div>
                                </div>
                                {onLogout && (
                                    <button
                                        onClick={onLogout}
                                        className="w-full px-3 py-2 bg-brand-emerald/50 hover:bg-brand-emerald rounded-lg text-brand-text text-left border border-brand-emerald"
                                    >
                                        Çıkış
                                    </button>
                                )}
                            </div>
                        </div>
                    )}

                    {showChangePassword && (
                        <div className="space-y-2">
                            <input
                                type="password"
                                value={currentPassword}
                                onChange={(e) => setCurrentPassword(e.target.value)}
                                placeholder="Mevcut şifre"
                                className="w-full px-3 py-2 text-xs bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
                            />
                            <input
                                type="password"
                                value={newPassword}
                                onChange={(e) => setNewPassword(e.target.value)}
                                placeholder="Yeni şifre"
                                className="w-full px-3 py-2 text-xs bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
                            />
                            {pwdError && <div className="text-red-300 text-xs">{pwdError}</div>}
                            {pwdMessage && <div className="text-green-300 text-xs">{pwdMessage}</div>}
                            <div className="flex items-center justify-between pt-1">
                                <button
                                    onClick={() => {
                                        setShowChangePassword(false);
                                        setPwdError(null);
                                        setPwdMessage(null);
                                        setCurrentPassword('');
                                        setNewPassword('');
                                    }}
                                    className="text-xs text-gray-400 hover:text-gray-300"
                                >
                                    Geri
                                </button>
                                <button
                                    disabled={pwdLoading || !currentPassword || !newPassword}
                                    onClick={async () => {
                                        if (!onChangePassword) return;
                                        setPwdError(null);
                                        setPwdMessage(null);
                                        setPwdLoading(true);
                                        try {
                                            await onChangePassword(currentPassword, newPassword);
                                            setPwdMessage('Şifre güncellendi');
                                            setCurrentPassword('');
                                            setNewPassword('');
                                        } catch (err: any) {
                                            setPwdError(err?.message || 'Şifre değiştirilemedi');
                                        } finally {
                                            setPwdLoading(false);
                                        }
                                    }}
                                    className="text-xs text-blue-300 hover:text-blue-200 disabled:text-gray-500"
                                >
                                    {pwdLoading ? 'Kaydediliyor...' : 'Kaydet'}
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default UserMenu;
