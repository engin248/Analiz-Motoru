// components/chat/markdownRenderer.tsx
import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import { useLightbox } from '@/components/ui/lightbox-provider';

// TypeScript'in prop'ları doğru tanıması için yardımcı tipler
type HTMLProps<T> = React.HTMLAttributes<T>;

interface RendererProps {
    content: string;
    // Dışarıdan gelen className prop'unu kabul ediyoruz
    className?: string;
}

const MarkdownRenderer: React.FC<RendererProps> = ({ content, className }) => {
    const { openLightbox } = useLightbox();

    // Ana stil sınıflarını bir değişkene atıyoruz
    const markdownStyles = `prose prose-invert max-w-none break-words ${className || ''}`;

    return (
        <div className={markdownStyles}>
            <ReactMarkdown
                // Ana div'e taşıdığımız için, ReactMarkdown'a doğrudan className vermiyoruz
                // Bu, TS2322 hatasını çözer.
                remarkPlugins={[remarkGfm]}
                // HTML tag'lerinin (table, div, img vb.) gerçek HTML olarak işlenmesi için
                rehypePlugins={[rehypeRaw]}
                components={{
                    // Paragraf etiketi (p)
                    p: (props: HTMLProps<HTMLParagraphElement>) => (
                        <p className="mb-4 text-gray-300" {...props} />
                    ),

                    // Kod bloklarını özelleştirme
                    code: (props: any) => {
                        const { node, inline, className, children, ...rest } = props;
                        const match = /language-(\w+)/.exec(className || '');

                        if (inline) {
                            return (
                                <code className="bg-gray-700 text-blue-300 px-1 py-0.5 rounded text-sm" {...rest}>
                                    {children}
                                </code>
                            );
                        }

                        return (
                            <div className="bg-gray-800 rounded-lg overflow-hidden my-4">
                                <div className="text-right text-xs text-gray-400 p-2 border-b border-gray-700">
                                    {match ? match[1].toUpperCase() : 'TEXT'}
                                </div>
                                <pre className="p-4 overflow-x-auto text-sm">
                                    <code className={`text-white ${className}`} {...rest}>
                                        {children}
                                    </code>
                                </pre>
                            </div>
                        );
                    },

                    // Listeleri özelleştirme
                    ul: (props: HTMLProps<HTMLUListElement>) => (
                        <ul className="list-disc list-inside mb-4 ml-4 text-gray-300" {...props} />
                    ),
                    ol: (props: HTMLProps<HTMLOListElement>) => (
                        <ol className="list-decimal list-inside mb-4 ml-4 text-gray-300" {...props} />
                    ),
                    li: (props: HTMLProps<HTMLLIElement>) => (
                        <li className="my-1" {...props} />
                    ),

                    // Başlıklar ve Vurgular
                    h1: (props: HTMLProps<HTMLHeadingElement>) => (
                        <h1 className="text-2xl font-bold mt-6 mb-3 text-white" {...props} />
                    ),
                    h2: (props: HTMLProps<HTMLHeadingElement>) => (
                        <h2 className="text-xl font-bold mt-5 mb-2 text-white" {...props} />
                    ),
                    strong: (props: HTMLProps<HTMLElement>) => (
                        <strong className="font-semibold text-white" {...props} />
                    ),

                    // Genspark-style tablo ve görseller
                    table: (props: HTMLProps<HTMLTableElement>) => (
                        <div className="w-full overflow-x-auto my-4">
                            <table
                                className="w-full border-collapse border border-gray-700/60 text-sm text-left"
                                {...props}
                            />
                        </div>
                    ),
                    th: (props: HTMLProps<HTMLTableCellElement>) => (
                        <th
                            className="bg-gray-800/80 font-semibold px-3 py-2 border border-gray-700/70 text-gray-100"
                            {...props}
                        />
                    ),
                    td: (props: HTMLProps<HTMLTableCellElement>) => (
                        <td
                            className="px-3 py-2 border border-gray-700/60 text-gray-200 align-top"
                            {...props}
                        />
                    ),
                    img: (props: React.ImgHTMLAttributes<HTMLImageElement>) => (
                        <img
                            className={`max-w-lg w-full h-auto rounded-xl shadow-lg my-4 cursor-pointer hover:opacity-95 transition-all border border-white/10 ${props.className || ''}`}
                            loading={props.loading ?? 'lazy'}
                            onClick={() => typeof props.src === 'string' && openLightbox(props.src)}
                            {...props}
                        />
                    ),
                    a: (props: React.AnchorHTMLAttributes<HTMLAnchorElement>) => (
                        <a
                            className={`text-blue-400 underline hover:text-blue-300 transition-colors ${props.className || ''}`}
                            target={props.target ?? '_blank'}
                            rel={props.rel ?? 'noopener noreferrer'}
                            {...props}
                        />
                    ),
                    div: (props: HTMLProps<HTMLDivElement>) => (
                        <div
                            // Flex container'lar (örn. image grid) için varsayılan uyumlu boşluklandırma
                            className={`my-2 ${props.className || ''}`}
                            {...props}
                        />
                    ),
                }}
            >
                {content}
            </ReactMarkdown>
        </div>
    );
};

export default MarkdownRenderer;