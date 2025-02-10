interface LoadingSpinnerProps {
    size?: 'small' | 'medium' | 'large';
    color?: string;
}

export default function LoadingSpinner({ size = 'medium', color = 'white' }: LoadingSpinnerProps) {
    const sizeClasses = {
        small: 'w-4 h-4',
        medium: 'w-6 h-6',
        large: 'w-8 h-8'
    };

    return (
        <div className={`inline-block animate-spin rounded-full border-2 border-solid border-current border-r-transparent ${sizeClasses[size]}`} 
             style={{ color }}
             role="status">
            <span className="sr-only">Loading...</span>
        </div>
    );
}
