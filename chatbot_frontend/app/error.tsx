'use client';

import { useEffect } from 'react';

export default function Error({
    error,
    reset,
}: {
    error: Error & { digest?: string };
    reset: () => void;
}) {
    useEffect(() => {
        console.error('Application error:', error);
    }, [error]);

    return (
        <div className="flex h-screen w-screen bg-brand-bg items-center justify-center">
            <div className="text-center p-8 max-w-md">
                <div className="mb-6">
                    <svg className="w-16 h-16 mx-auto text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                </div>
                <h2 className="text-2xl font-bold text-brand-emerald mb-4">
                    Bir şeyler yanlış gitti
                </h2>
                <p className="text-brand-emerald/70 mb-6">
                    Beklenmedik bir hata oluştu. Lütfen tekrar deneyin.
                </p>
                <button
                    onClick={() => reset()}
                    className="px-6 py-3 bg-brand-emerald text-white rounded-xl hover:bg-brand-emerald/90 transition-colors font-medium"
                >
                    Tekrar Dene
                </button>
            </div>
        </div>
    );
}
