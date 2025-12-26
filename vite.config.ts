import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { resolve } from 'path';

export default defineConfig({
    plugins: [
        vue({
            // Treat files in components directory as custom elements
            // This tells Vue to include styles in the component definition
            // so they get injected into the Shadow DOM.
            // Exclude VariableToolbar.vue as it is used as a standard Vue component in App.vue
            customElement: /webview\/components\/(?!VariableToolbar\.vue).+\.vue$/
        })
    ],

    // Force production mode for webview build
    mode: 'production',

    resolve: {
        alias: {
            // Use Vue's production ESM bundle
            'vue': 'vue/dist/vue.esm-browser.prod.js'
        }
    },

    build: {
        // Output to out/webview for VS Code extension to load
        outDir: 'out/webview',
        emptyOutDir: true,

        // Library mode for embedding in webview
        lib: {
            entry: resolve(__dirname, 'src/webview/main.ts'),
            name: 'AimdPreview',
            formats: ['iife'], // Immediately Invoked Function Expression for browser
            fileName: () => 'webview.js'
        },

        rollupOptions: {
            output: {
                // Inline all dependencies
                inlineDynamicImports: true,
                // CSS will be injected into JS
                assetFileNames: 'webview.[ext]'
            }
        },

        // Don't minify for easier debugging
        minify: false,
        sourcemap: true
    },

    define: {
        // Replace process.env.NODE_ENV with 'production' to avoid runtime errors
        'process.env.NODE_ENV': JSON.stringify('production'),
        'process.env': JSON.stringify({}),

        // Vue feature flags
        __VUE_OPTIONS_API__: true,
        __VUE_PROD_DEVTOOLS__: false,
        __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: false
    }
});
