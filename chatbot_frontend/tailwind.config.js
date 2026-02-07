// tailwind.config.js

/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        './app/**/*.{js,ts,jsx,tsx,mdx}',
        './components/**/*.{js,ts,jsx,tsx,mdx}',
        './pages/**/*.{js,ts,jsx,tsx,mdx}',
    ],
    safelist: [
        'bg-brand-bg',
        'bg-brand-emerald',
        'text-brand-emerald',
        'text-brand-text',
        'border-brand-emerald',
        'border-brand-text'
    ],
    theme: {
        extend: {
            transitionDuration: {
                '700': '700ms',
                '1000': '1000ms',
                '2000': '2000ms',
            },
            keyframes: {
                shake: {
                    '0%, 100%': { transform: 'translateX(0)' },
                    '10%, 30%, 50%, 70%, 90%': { transform: 'translateX(-4px)' },
                    '20%, 40%, 60%, 80%': { transform: 'translateX(4px)' },
                },
                'fade-in': {
                    '0%': { opacity: '0', transform: 'translateY(10px)' },
                    '100%': { opacity: '1', transform: 'translateY(0)' },
                },
                'slide-up': {
                    '0%': { opacity: '0', transform: 'translateY(20px)' },
                    '100%': { opacity: '1', transform: 'translateY(0)' },
                }
            },
            animation: {
                shake: 'shake 0.5s cubic-bezier(.36,.07,.19,.97) both',
                'fade-in': 'fade-in 0.5s ease-out forwards',
                'slide-up': 'slide-up 0.6s ease-out forwards',
            },
        },
    },

    plugins: [
        require('@tailwindcss/typography')
    ],
};