// types/chat.ts (Yeni dosya)
export type MessageSender = 'user' | 'ai';

export interface ChatMessage {
    id: string;
    sender: MessageSender;
    content: string; // Markdown metni buraya gelecek
    timestamp: number; // Mesajın ne zaman gönderildiği
    imageUrl?: string; // Resim URL'i (opsiyonel, backward compatibility için)
    imageUrls?: string[]; // Resim URL'leri (opsiyonel, birden fazla görsel için)
    isStopped?: boolean; // Mesajın durdurulup durdurulmadığını belirtir (silik gösterim için)
}

