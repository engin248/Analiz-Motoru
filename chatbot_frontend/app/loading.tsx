export default function Loading() {
    return (
        <div className="flex h-screen w-screen bg-brand-bg items-center justify-center">
            <div className="text-center">
                {/* Animated Logo Skeleton */}
                <div className="mb-8 animate-pulse">
                    <div className="w-20 h-20 mx-auto rounded-full bg-brand-emerald/30" />
                </div>

                {/* Text Skeleton */}
                <div className="space-y-3 animate-pulse">
                    <div className="h-8 w-48 mx-auto bg-brand-emerald/20 rounded-lg" />
                    <div className="h-4 w-64 mx-auto bg-brand-emerald/10 rounded-lg" />
                </div>

                {/* Loading Dots */}
                <div className="flex justify-center gap-2 mt-8">
                    <div className="w-3 h-3 rounded-full bg-brand-emerald animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-3 h-3 rounded-full bg-brand-emerald animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-3 h-3 rounded-full bg-brand-emerald animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
            </div>
        </div>
    );
}
