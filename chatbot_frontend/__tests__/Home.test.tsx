import React from 'react';
import { render, screen } from '@testing-library/react';
import Home from '@/app/page';

// Mock useChat hook
jest.mock('@/hooks/useChat', () => ({
    useChat: () => ({
        messages: [],
        isLoading: false,
        sendMessage: jest.fn(),
        startNewChat: jest.fn(),
        deleteConversation: jest.fn(),
        isChatStarted: false,
        inputText: '',
        setInputText: jest.fn(),
        isGuest: false,
        currentConversationId: null,
        guestAlias: 'Misafir',
        conversations: [],
        loadConversation: jest.fn(),
        stopGeneration: jest.fn(),
        setConversations: jest.fn()
    })
}));

// Mock API
jest.mock('@/lib/api', () => ({
    api: {
        me: jest.fn(),
        changePassword: jest.fn(),
    }
}));

// Mock Sidebar and UserMenu components to simplify
jest.mock('@/components/sidebar/sidebar', () => {
    return function DummySidebar() {
        return <div data-testid="sidebar">Sidebar</div>;
    };
});

jest.mock('@/components/header/userMenu', () => {
    return function DummyUserMenu() {
        return <div data-testid="user-menu">UserMenu</div>;
    };
});

// Mock LoginForm
jest.mock('@/components/auth/loginForm', () => {
    return function DummyLoginForm() {
        return <div data-testid="login-form">Login Form</div>;
    };
});

// Mock MessageList
jest.mock('@/components/chat/messageList', () => {
    return function DummyMessageList() {
        return <div data-testid="message-list">Message List</div>;
    };
});

describe('Home Page', () => {
    it('renders login form when not authenticated', () => {
        render(<Home />);
        // Since localStorage is empty by default in jsdom, it should render the login form
        const loginForm = screen.getByTestId('login-form');
        expect(loginForm).toBeInTheDocument();
    });
});
