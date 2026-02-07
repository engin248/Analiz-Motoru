'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';

interface LoginFormProps {
    onLoginSuccess: () => void;  // No token needed - cookies handle it
    onGuestMode: () => void;
}

export default function LoginForm({ onLoginSuccess, onGuestMode }: LoginFormProps) {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [isRegister, setIsRegister] = useState(false);
    const [email, setEmail] = useState('');
    const [fullName, setFullName] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);

        try {
            if (isRegister) {
                // Register
                await api.register({
                    username,
                    email,
                    password,
                    full_name: fullName || undefined,
                });
                // Auto-login after registration
                await api.login(username, password);
                onLoginSuccess();
            } else {
                // Login
                await api.login(username, password);
                onLoginSuccess();
            }
        } catch (err: any) {
            let msg = err.message || 'Bir hata oluştu';
            if (msg.includes('Failed to fetch') || msg.includes('Network request failed')) {
                msg = 'Sunucuya erişilemiyor. Lütfen bağlantınızı kontrol edin.';
            } else if (msg.toLowerCase().includes('field required')) {
                msg = 'Lütfen tüm zorunlu alanları doldurun.';
            } else if (msg.toLowerCase().includes('email') && msg.toLowerCase().includes('not valid')) {
                msg = 'Geçerli bir e-posta adresi giriniz.';
            }
            setError(msg);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="w-full max-w-md mx-auto p-6 bg-brand-emerald/95 backdrop-blur-md rounded-2xl border border-brand-emerald/50 shadow-2xl">
            <h2 className="text-2xl font-bold text-brand-text mb-6 text-center">
                {isRegister ? 'Kayıt Ol' : 'Giriş Yap'}
            </h2>

            <form onSubmit={handleSubmit} className="space-y-4">
                {isRegister && (
                    <>
                        <div>
                            <label className="block text-sm font-medium text-brand-text mb-2">
                                Ad Soyad
                            </label>
                            <input
                                type="text"
                                value={fullName}
                                onChange={(e) => setFullName(e.target.value)}
                                className="w-full px-4 py-2 bg-brand-emerald/50 border border-brand-emerald/50 rounded-lg text-brand-text focus:outline-none focus:ring-2 focus:ring-white/50 placeholder:text-brand-text/50"
                                placeholder="Ad Soyad (opsiyonel)"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-brand-text mb-2">
                                E-posta
                            </label>
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                className="w-full px-4 py-2 bg-brand-emerald/50 border border-brand-emerald/50 rounded-lg text-brand-text focus:outline-none focus:ring-2 focus:ring-white/50 placeholder:text-brand-text/50"
                                placeholder="ornek@email.com"
                            />
                        </div>
                    </>
                )}

                <div>
                    <label className="block text-sm font-medium text-brand-text mb-2">
                        Kullanıcı Adı
                    </label>
                    <input
                        type="text"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        required
                        className="w-full px-4 py-2 bg-brand-emerald/50 border border-brand-emerald/50 rounded-lg text-brand-text focus:outline-none focus:ring-2 focus:ring-white/50 placeholder:text-brand-text/50"
                        placeholder="kullanici_adi"
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-brand-text mb-2">
                        Şifre
                    </label>
                    <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                        className="w-full px-4 py-2 bg-brand-emerald/50 border border-brand-emerald/50 rounded-lg text-brand-text focus:outline-none focus:ring-2 focus:ring-white/50 placeholder:text-brand-text/50"
                        placeholder="••••••••"
                    />
                </div>

                {error && (
                    <div className="flex items-start gap-3 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-200 text-sm animate-shake">
                        <svg className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                        </svg>
                        <span>{error}</span>
                    </div>
                )}

                <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full py-3 bg-brand-emerald hover:bg-emerald-700 rounded-lg hover:shadow-lg transition-all duration-200 disabled:bg-gray-600 disabled:cursor-not-allowed text-brand-text font-medium shadow-md border border-brand-emerald/50"
                >
                    {isLoading ? 'Yükleniyor...' : isRegister ? 'Kayıt Ol' : 'Giriş Yap'}
                </button>
            </form>

            <div className="mt-4 space-y-2">
                <div className="text-center">
                    <button
                        type="button"
                        onClick={() => {
                            setIsRegister(!isRegister);
                            setError(null);
                        }}
                        className="text-sm text-blue-400 hover:text-blue-300 transition-colors"
                    >
                        {isRegister ? 'Zaten hesabınız var mı? Giriş yapın' : 'Hesabınız yok mu? Kayıt olun'}
                    </button>
                </div>
                <div className="relative flex items-center my-4">
                    <div className="flex-grow border-t border-gray-700"></div>
                    <span className="px-3 text-sm text-gray-500">veya</span>
                    <div className="flex-grow border-t border-gray-700"></div>
                </div>
                <button
                    type="button"
                    onClick={onGuestMode}
                    className="w-full py-3 bg-brand-emerald/30 hover:bg-brand-emerald/50 rounded-lg transition-all duration-200 text-brand-text font-medium border border-brand-emerald/50 hover:border-brand-text/50"
                >
                    Misafir Olarak Devam Et
                </button>
            </div>
        </div>
    );
}

