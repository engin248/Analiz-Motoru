const API_BASE =
    process.env.NEXT_PUBLIC_BACKEND_URL?.replace(/\/$/, '') ||
    'http://localhost:8000';
const API_URL = `${API_BASE}/api`;

export interface ApiUser {
    id: number;
    username: string;
    email: string;
    full_name?: string;
    created_at?: string;
    avatar_url?: string;
}

export interface LoginResponse {
    message: string;
    user: ApiUser;
}

export interface ConversationDto {
    id: number;
    title?: string;
    alias?: string;
    history_json?: any[];
    created_at: string;
}

export interface MessageDto {
    id: number;
    conversation_id: number;
    sender: 'user' | 'ai';
    content?: string;
    image_url?: string;
    created_at: string;
}

interface RequestOptions extends RequestInit {
    token?: string | null;
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const isFormData = options.body instanceof FormData;

    const headers: Record<string, string> = {
        ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
        ...(options.headers as Record<string, string> || {}),
    };

    const res = await fetch(`${API_URL}${endpoint}`, {
        ...options,
        credentials: 'include',  // Send cookies automatically
        headers,
    });

    if (!res.ok) {
        const error = await res.json().catch(() => ({}));
        let errorMessage = error.detail || error.error || 'İstek başarısız';

        if (Array.isArray(errorMessage)) {
            // Pydantic validation errors
            errorMessage = errorMessage.map((e: any) => {
                if (typeof e === 'object' && e.msg) return e.msg;
                return String(e);
            }).join(', ');
        } else if (typeof errorMessage === 'object') {
            errorMessage = JSON.stringify(errorMessage);
        }

        throw new Error(errorMessage);
    }

    if (res.status === 204) {
        return {} as T;
    }

    return res.json();
}

export const api = {
    login: (username: string, password: string) =>
        request<LoginResponse>('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password }),
        }),

    register: (data: { username: string; password: string; email: string; full_name?: string }) =>
        request<ApiUser>('/auth/register', {
            method: 'POST',
            body: JSON.stringify(data),
        }),

    logout: () =>
        request<{ message: string }>('/auth/logout', {
            method: 'POST',
        }),

    me: () =>
        request<ApiUser>('/users/me'),

    uploadAvatar: (file: File) => {
        const formData = new FormData();
        formData.append('file', file);
        return request<ApiUser>('/users/avatar', {
            method: 'POST',
            body: formData,
        });
    },

    changePassword: (current_password: string, new_password: string) =>
        request<{ detail: string }>('/users/change-password', {
            method: 'POST',
            body: JSON.stringify({ current_password, new_password }),
        }),

    listConversations: () =>
        request<ConversationDto[]>('/conversations'),

    createConversation: (title?: string, alias?: string) =>
        request<ConversationDto>('/conversations', {
            method: 'POST',
            body: JSON.stringify({ title, alias }),
        }),

    deleteConversation: (conversationId: number) =>
        request<{ detail: string }>(`/conversations/${conversationId}`, {
            method: 'DELETE',
        }),

    getMessages: (conversationId: number) =>
        request<MessageDto[]>(`/conversations/${conversationId}/messages`),

    saveMessage: (
        payload: { conversation_id: number; sender: 'user' | 'ai'; content?: string; image_url?: string }
    ) =>
        request<MessageDto>('/messages', {
            method: 'POST',
            body: JSON.stringify(payload),
        }),

    updateConversation: (conversationId: number, data: { title?: string; alias?: string }) =>
        request<ConversationDto>(`/conversations/${conversationId}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        }),

    uploadFile: (file: File) => {
        const formData = new FormData();
        formData.append('file', file);
        return request<{ url: string }>('/messages/upload', {
            method: 'POST',
            body: formData,
        });
    },
};
