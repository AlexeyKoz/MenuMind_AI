// Type declaration for react-markdown
declare module 'react-markdown' {
    import { ReactElement } from 'react';

    export interface ReactMarkdownProps {
        children?: string;
        components?: Record<string, React.ComponentType<any>>;
        [key: string]: any;
    }

    export default function ReactMarkdown(props: ReactMarkdownProps): ReactElement;
}

