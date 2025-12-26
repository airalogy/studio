import * as vscode from 'vscode';
import { getHighlighter, Highlighter, BUNDLED_LANGUAGES, BUNDLED_THEMES } from 'shiki';

export class HighlighterService {
    private static instance: HighlighterService;
    private highlighter: Highlighter | null = null;
    private initPromise: Promise<void> | null = null;

    private constructor() { }

    public static getInstance(): HighlighterService {
        if (!HighlighterService.instance) {
            HighlighterService.instance = new HighlighterService();
        }
        return HighlighterService.instance;
    }

    private async ensureInitialized(): Promise<void> {
        if (this.highlighter) return;
        if (!this.initPromise) {
            this.initPromise = (async () => {
                this.highlighter = await getHighlighter({
                    themes: ['min-light', 'dark-plus'],
                    langs: ['python', 'javascript', 'typescript', 'json', 'markdown', 'html']
                });
            })();
        }
        await this.initPromise;
    }

    /**
     * Highlight code using Shiki
     */
    public async highlight(code: string, lang: string): Promise<string> {
        await this.ensureInitialized();
        if (!this.highlighter) return `<pre>${code}</pre>`;

        // Detech theme kind
        const kind = vscode.window.activeColorTheme.kind;
        const theme = kind === vscode.ColorThemeKind.Dark || kind === vscode.ColorThemeKind.HighContrast
            ? 'dark-plus'
            : 'min-light';

        try {
            return this.highlighter.codeToHtml(code, { lang, theme });
        } catch (e) {
            console.warn(`Failed to highlight ${lang}:`, e);
            // Fallback to plain text
            return this.highlighter.codeToHtml(code, { lang: 'txt', theme });
        }
    }
}
