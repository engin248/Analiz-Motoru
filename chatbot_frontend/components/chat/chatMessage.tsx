// components/chat/chatMessage.tsx
import React, { useMemo, useState } from 'react';
import MarkdownRenderer from './markdownRenderer';
// TIP TANIMLARI İÇİN 'type' ANAHTAR KELİMESİNİ KULLANIYORUZ
import type { ChatMessage } from '@/types/chat';
import { useLightbox } from '@/components/ui/lightbox-provider';

interface ChatMessageProps {
    message: ChatMessage;
    userProfile?: { email?: string; full_name?: string | null; username?: string };
    avatarOverride?: string;
    isGuest?: boolean;
    onRegenerate?: () => void;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message, userProfile, avatarOverride, isGuest, onRegenerate }) => {
    const isUser = message.sender === 'user';
    const isStreaming = message.id === 'streaming-ai';
    const { openLightbox } = useLightbox();
    const [feedback, setFeedback] = useState<'like' | 'dislike' | null>(null);

    const handleFeedback = (type: 'like' | 'dislike') => {
        if (feedback === type) {
            setFeedback(null);
            console.log(`[Feedback] Removed ${type} for message ${message.id}`);
        } else {
            setFeedback(type);
            console.log(`[Feedback] Set ${type} for message ${message.id}`);
        }
    };

    // Basit MD5 (Gravatar için)
    const md5 = (str: string) => {
        /* c8 ignore start */
        const utf8 = new TextEncoder().encode(str);
        let output = '';
        // Minimal MD5 implementation (non-optimized, short input)
        const r = (x: number, n: number) => (x << n) | (x >>> (32 - n));
        const k = [
            0xd76aa478, 0xe8c7b756, 0x242070db, 0xc1bdceee, 0xf57c0faf, 0x4787c62a, 0xa8304613, 0xfd469501,
            0x698098d8, 0x8b44f7af, 0xffff5bb1, 0x895cd7be, 0x6b901122, 0xfd987193, 0xa679438e, 0x49b40821,
            0xf61e2562, 0xc040b340, 0x265e5a51, 0xe9b6c7aa, 0xd62f105d, 0x02441453, 0xd8a1e681, 0xe7d3fbc8,
            0x21e1cde6, 0xc33707d6, 0xf4d50d87, 0x455a14ed, 0xa9e3e905, 0xfcefa3f8, 0x676f02d9, 0x8d2a4c8a,
            0xfffa3942, 0x8771f681, 0x6d9d6122, 0xfde5380c, 0xa4beea44, 0x4bdecfa9, 0xf6bb4b60, 0xbebfbc70,
            0x289b7ec6, 0xeaa127fa, 0xd4ef3085, 0x04881d05, 0xd9d4d039, 0xe6db99e5, 0x1fa27cf8, 0xc4ac5665,
            0xf4292244, 0x432aff97, 0xab9423a7, 0xfc93a039, 0x655b59c3, 0x8f0ccc92, 0xffeff47d, 0x85845dd1,
            0x6fa87e4f, 0xfe2ce6e0, 0xa3014314, 0x4e0811a1, 0xf7537e82, 0xbd3af235, 0x2ad7d2bb, 0xeb86d391
        ];
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
                let f: number; let g: number;
                if (j < 16) { f = (b & c) | (~b & d); g = j; }
                else if (j < 32) { f = (d & b) | (~d & c); g = (5 * j + 1) % 16; }
                else if (j < 48) { f = b ^ c ^ d; g = (3 * j + 5) % 16; }
                else { f = c ^ (b | ~d); g = (7 * j) % 16; }
                const tmp = d;
                d = c;
                c = b;
                b = b + r((a + f + k[j] + (m[i + g] | 0)) | 0, s[(j >> 4) * 4 + (j % 4)]);
                a = tmp;
            }
            a = (a + oa) | 0; b = (b + ob) | 0; c = (c + oc) | 0; d = (d + od) | 0;
        }
        const toHex = (n: number) => ('00000000' + (n >>> 0).toString(16)).slice(-8);
        output = toHex(a) + toHex(b) + toHex(c) + toHex(d);
        return output;
        /* c8 ignore end */
    };

    const defaultAvatarUrl = '/default-avatar.svg';

    const { gravatarUrl, fallbackAvatarUrl } = useMemo(() => {
        if (isGuest) {
            return { gravatarUrl: null, fallbackAvatarUrl: defaultAvatarUrl };
        }
        if (avatarOverride) {
            return { gravatarUrl: avatarOverride, fallbackAvatarUrl: avatarOverride };
        }
        const email = userProfile?.email?.trim().toLowerCase();
        if (!email) return { gravatarUrl: null, fallbackAvatarUrl: defaultAvatarUrl };
        const hash = md5(email);
        const gravUrl = `https://www.gravatar.com/avatar/${hash}?d=404`;
        return { gravatarUrl: gravUrl, fallbackAvatarUrl: defaultAvatarUrl };
    }, [userProfile, avatarOverride, isGuest]);

    // Mesajın stil ve ikonunu belirleme
    const containerClasses = isUser ? 'justify-end' : 'justify-start';

    // Avatar boyutunu küçült (ChatGPT tarzı - 8x8 = 2rem)
    const icon = isUser ? (
        <img
            src={gravatarUrl || fallbackAvatarUrl}
            alt="Kullanıcı"
            className="w-8 h-8 rounded-full object-cover shadow-sm ring-1 ring-white/10"
            loading="lazy"
            onError={(e) => {
                const target = e.target as HTMLImageElement;
                if (target.src !== fallbackAvatarUrl) {
                    target.src = fallbackAvatarUrl;
                }
            }}
        />
    ) : (
        // AI Avatar - ChatGPT tarzı minimal
        <div className="w-8 h-8 flex items-center justify-center rounded-full overflow-hidden bg-brand-emerald/10 ring-1 ring-white/20 shadow-md">
            <img
                src="/lumora_orb.png"
                alt="Lumora AI"
                className="w-full h-full object-cover"
            />
        </div>
    );

    return (
        <div className={`flex w-full mb-2 ${containerClasses} animate-fade-in group`}>

            {/* İkon / Avatar (AI için sola) - Sadece AI için göster, kullanıcı için gizle (ChatGPT stilinde genelde kullanıcı avatarı yoktur ama isteğe bağlı) */}
            {!isUser && (
                <div className="mr-4 flex-shrink-0 mt-1">
                    {icon}
                </div>
            )}

            {/* Mesaj İçeriği */}
            <div className={`flex flex-col ${isUser ? 'max-w-3xl ml-auto' : 'max-w-5xl w-full'}`}>

                {/* İsim alanı (Opsiyonel - ChatGPT'de var) */}
                <div className="flex items-center gap-2 mb-1 px-1">
                    <span className="text-xs font-semibold text-gray-400">
                        {isUser ? 'Siz' : 'Lumora AI'}
                    </span>
                </div>

                <div className={`
                    relative px-5 py-3 text-[15px] leading-relaxed
                    ${isUser
                        ? 'bg-[#2F2F2F] text-gray-100 rounded-3xl rounded-tr-sm shadow-sm' // Kullanıcı: Koyu gri bubble
                        : 'bg-transparent text-gray-100 pl-0' // AI: Transparent, bubble yok
                    } 
                    ${message.isStopped ? 'opacity-60 italic' : ''}
                    break-words overflow-hidden
                `}>

                    {/* Resim gösterimi */}
                    {(message.imageUrls && message.imageUrls.length > 0) || message.imageUrl ? (
                        <div className="mb-4">
                            <div className="flex flex-wrap gap-3">
                                {(message.imageUrls && message.imageUrls.length > 0 ? message.imageUrls : message.imageUrl ? [message.imageUrl] : []).map((imageUrl, index) => (
                                    <div key={index} className="relative rounded-2xl overflow-hidden border border-white/10 shadow-xl bg-gray-900/50 group/img cursor-pointer max-w-sm w-full aspect-square" onClick={() => openLightbox(imageUrl)}>
                                        <img
                                            src={imageUrl}
                                            alt={`AI generated ${index + 1}`}
                                            className="w-full h-full object-cover transition-all duration-300 group-hover/img:scale-[1.05]"
                                            loading="eager"
                                        />
                                    </div>
                                ))}
                            </div>
                        </div>
                    ) : null}

                    {/* Metin içeriği */}
                    {message.content && (
                        <div className="text-gray-100">
                            {isUser ? (
                                <p className="whitespace-pre-wrap break-words">{message.content}</p>
                            ) : (
                                <>
                                    <div className="prose prose-invert prose-p:text-gray-50 prose-headings:text-white prose-strong:text-white prose-li:text-gray-50 prose-p:leading-relaxed prose-pre:bg-[#0d0d0d] prose-pre:border prose-pre:border-white/10 max-w-none">
                                        <MarkdownRenderer content={message.content} />

                                        {/* Görsel linkleri */}
                                        {(message.imageUrls && message.imageUrls.length > 0) && (
                                            <div className="mt-4 pt-3 border-t border-white/5">
                                                <div className="text-xs font-medium text-gray-500 mb-2 uppercase tracking-wider">Referans Görseller</div>
                                                <div className="flex flex-wrap gap-2">
                                                    {message.imageUrls.map((u, idx) => (
                                                        <a
                                                            key={idx}
                                                            href={u}
                                                            target="_blank"
                                                            rel="noopener noreferrer"
                                                            className="text-xs bg-white/5 hover:bg-white/10 px-2 py-1 rounded text-blue-400 transition-colors truncate max-w-[200px]"
                                                        >
                                                            Görsel {idx + 1}
                                                        </a>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                    {!isStreaming && (
                                        <div className="flex items-center gap-1 mt-2 text-gray-400 select-none opacity-0 group-hover:opacity-100 transition-opacity duration-500 animate-fade-in">
                                            <button
                                                onClick={() => navigator.clipboard.writeText(message.content)}
                                                className="p-1.5 hover:bg-[#2F2F2F] rounded-md hover:text-gray-200 transition-colors"
                                                title="Kopyala"
                                            >
                                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                                                    <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 17.25v3.375c0 .621-.504 1.125-1.125 1.125h-9.75a1.125 1.125 0 01-1.125-1.125V7.875c0-.621.504-1.125 1.125-1.125H6.75a9.06 9.06 0 011.5.124m7.5 10.376h3.375c.621 0 1.125-.504 1.125-1.125V11.25c0-4.46-3.243-8.161-7.5-8.876a9.06 9.06 0 00-1.5-.124H9.375c-.621 0-1.125.504-1.125 1.125v3.5m7.5 10.375H9.375a1.125 1.125 0 01-1.125-1.125v-9.25m12 6.625v-1.875a3.375 3.375 0 00-3.375-3.375h-1.5" />
                                                </svg>
                                            </button>
                                            <button
                                                className={`p-1.5 rounded-md transition-colors ${feedback === 'like' ? 'text-green-400 bg-green-400/10' : 'hover:bg-[#2F2F2F] hover:text-gray-200'}`}
                                                title="Beğen"
                                                onClick={() => handleFeedback('like')}
                                            >
                                                <svg xmlns="http://www.w3.org/2000/svg" fill={feedback === 'like' ? "currentColor" : "none"} viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                                                    <path strokeLinecap="round" strokeLinejoin="round" d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
                                                </svg>
                                            </button>
                                            <button
                                                className={`p-1.5 rounded-md transition-colors ${feedback === 'dislike' ? 'text-red-400 bg-red-400/10' : 'hover:bg-[#2F2F2F] hover:text-gray-200'}`}
                                                title="Beğenme"
                                                onClick={() => handleFeedback('dislike')}
                                            >
                                                <svg xmlns="http://www.w3.org/2000/svg" fill={feedback === 'dislike' ? "currentColor" : "none"} viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                                                    <path strokeLinecap="round" strokeLinejoin="round" d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.737 3h4.018a2 2 0 01.485.06l3.76.94m-7 10v5a2 2 0 002 2h.095c.5 0 .905-.405.905-.905 0-.714.211-1.412.608-2.006L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5" />
                                                </svg>
                                            </button>
                                            <button className="p-1.5 hover:bg-[#2F2F2F] rounded-md hover:text-gray-200 transition-colors" title="Yeniden Yanıtla" onClick={onRegenerate}>
                                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                                                    <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
                                                </svg>
                                            </button>
                                            <button className="p-1.5 hover:bg-[#2F2F2F] rounded-md hover:text-gray-200 transition-colors" title="Paylaş">
                                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                                                    <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                                                </svg>
                                            </button>
                                            <button className="p-1.5 hover:bg-[#2F2F2F] rounded-md hover:text-gray-200 transition-colors" title="Daha fazla">
                                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                                                    <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 12a.75.75 0 11-1.5 0 .75.75 0 011.5 0zM12.75 12a.75.75 0 11-1.5 0 .75.75 0 011.5 0zM18.75 12a.75.75 0 11-1.5 0 .75.75 0 011.5 0z" />
                                                </svg>
                                            </button>
                                        </div>
                                    )}
                                </>
                            )}
                        </div>
                    )}
                </div>
            </div>

            {/* İkon / Avatar (Kullanıcı için sağa) */}
            {isUser && (
                <div className="ml-4 flex-shrink-0 mt-1">
                    {icon}
                </div>
            )}

        </div>
    );
};

export default ChatMessage;