/**
 * Sistema de Internacionalização - Cliente
 * 
 * Gerencia a troca de idiomas no lado cliente, incluindo:
 * - Persistência via localStorage
 * - Atualização dinâmica da interface
 * - Comunicação com o servidor
 * - Recursos de acessibilidade
 */

class I18nManager {
    constructor() {
        // Inicializa lista de idiomas suportados e nomes antes de detectar
        this.supportedLanguages = ['pt-BR', 'en-US', 'es-ES'];
        this.languageNames = {
            'pt-BR': 'Português',
            'en-US': 'English',
            'es-ES': 'Español'
        };
        this.translations = {};

        // Detecta idioma atual com base em preferências e navegador
        this.currentLanguage = this.detectLanguage();

        this.init();
    }
    
    init() {
        // Carrega traduções do servidor se necessário
        this.loadTranslations();
        
        // Configura event listeners
        this.setupEventListeners();
        
        // Atualiza interface inicial
        this.updateInterface();
    }
    
    detectLanguage() {
        // 1. localStorage (preferência salva)
        const saved = localStorage.getItem('preferred_language');
        if (saved && Array.isArray(this.supportedLanguages) && this.supportedLanguages.includes(saved)) {
            return saved;
        }

        // 2. Navegador (inclui fallback para lista de idiomas)
        let browserLang = null;
        if (typeof navigator !== 'undefined') {
            browserLang = navigator.language || navigator.userLanguage || (Array.isArray(navigator.languages) ? navigator.languages[0] : null);
        }
        if (browserLang && this.supportedLanguages.includes(browserLang)) {
            return browserLang;
        }

        // 3. Código base do navegador (pt, en, es)
        if (browserLang) {
            const langCode = String(browserLang).split('-')[0].toLowerCase();
            for (const supported of this.supportedLanguages) {
                if (supported.toLowerCase().startsWith(langCode)) {
                    return supported;
                }
            }
        }

        // 4. Fallback
        return 'pt-BR';
    }
    
    async setLanguage(language) {
        if (!this.supportedLanguages.includes(language)) {
            console.error('Idioma não suportado:', language);
            return false;
        }
        
        try {
            // Salva no localStorage
            localStorage.setItem('preferred_language', language);
            
            // Envia para o servidor
            const response = await fetch(`/i18n/set-language/${language}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.currentLanguage = language;
                
                // Atualiza interface
                this.updateInterface();
                
                // Mostra notificação de sucesso
                this.showLanguageChangeNotification(data.message);
                
                // Recarrega a página para aplicar traduções do servidor
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
                
                return true;
            } else {
                throw new Error('Erro ao alterar idioma no servidor');
            }
        } catch (error) {
            console.error('Erro ao alterar idioma:', error);
            this.showError('Erro ao alterar idioma. Tente novamente.');
            return false;
        }
    }
    
    async loadTranslations(namespace = 'common') {
        try {
            const response = await fetch(`/i18n/translations/${namespace}`);
            if (response.ok) {
                const data = await response.json();
                this.translations[namespace] = data.translations;
            }
        } catch (error) {
            console.error('Erro ao carregar traduções:', error);
        }
    }
    
    translate(key, namespace = 'common', variables = {}) {
        const translation = this.getNestedValue(this.translations[namespace], key);
        if (!translation) {
            return key; // Fallback para a própria chave
        }
        
        // Aplica interpolação de variáveis
        return this.interpolate(translation, variables);
    }
    
    getNestedValue(obj, path) {
        return path.split('.').reduce((current, key) => {
            return current && current[key] !== undefined ? current[key] : null;
        }, obj);
    }
    
    interpolate(text, variables) {
        if (!variables || Object.keys(variables).length === 0) {
            return text;
        }
        
        return text.replace(/\{(\w+)\}/g, (match, key) => {
            return variables[key] !== undefined ? variables[key] : match;
        });
    }
    
    setupEventListeners() {
        // Event listeners para seletores de idioma
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-language]')) {
                e.preventDefault();
                const language = e.target.getAttribute('data-language');
                this.setLanguage(language);
            }
        });
        
        // Event listener para dropdown de idioma
        document.addEventListener('change', (e) => {
            if (e.target.matches('#language-selector') || e.target.matches('#languageDropdown') || e.target.matches('select.language-selector-dropdown')) {
                const language = e.target.value;
                this.setLanguage(language);
            }
        });
        
        // Teclas de atalho para acessibilidade
        document.addEventListener('keydown', (e) => {
            // Alt + L para abrir seletor de idioma
            if (e.altKey && e.key === 'l') {
                e.preventDefault();
                this.focusLanguageSelector();
            }
        });
    }
    
    updateInterface() {
        // Atualiza indicador de idioma atual
        const currentLangElements = document.querySelectorAll('[data-current-language]');
        currentLangElements.forEach(el => {
            el.textContent = this.languageNames[this.currentLanguage];
            el.setAttribute('aria-label', `Idioma atual: ${this.languageNames[this.currentLanguage]}`);
        });
        
        // Atualiza seletores
        const selectors = document.querySelectorAll('#language-selector, #languageDropdown, select.language-selector-dropdown');
        selectors.forEach(select => {
            select.value = this.currentLanguage;
        });
        
        // Atualiza botões de idioma
        const languageButtons = document.querySelectorAll('[data-language]');
        languageButtons.forEach(btn => {
            const lang = btn.getAttribute('data-language');
            btn.classList.toggle('active', lang === this.currentLanguage);
            btn.setAttribute('aria-pressed', lang === this.currentLanguage);
        });
        
        // Atualiza atributo lang do documento
        document.documentElement.lang = this.currentLanguage;
    }
    
    focusLanguageSelector() {
        const selector = document.querySelector('#language-selector') || 
                        document.querySelector('#languageDropdown') ||
                        document.querySelector('select.language-selector-dropdown') ||
                        document.querySelector('[data-language]');
        if (selector) {
            selector.focus();
        }
    }
    
    showLanguageChangeNotification(message) {
        // Cria notificação acessível
        const notification = document.createElement('div');
        notification.className = 'language-change-notification';
        notification.setAttribute('role', 'status');
        notification.setAttribute('aria-live', 'polite');
        notification.textContent = message;
        
        // Estilos inline para garantir visibilidade
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            backgroundColor: '#28a745',
            color: 'white',
            padding: '12px 20px',
            borderRadius: '4px',
            boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
            zIndex: '9999',
            fontSize: '14px',
            maxWidth: '300px'
        });
        
        document.body.appendChild(notification);
        
        // Remove após 3 segundos
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }
    
    showError(message) {
        // Cria notificação de erro
        const notification = document.createElement('div');
        notification.className = 'language-error-notification';
        notification.setAttribute('role', 'alert');
        notification.setAttribute('aria-live', 'assertive');
        notification.textContent = message;
        
        // Estilos inline para garantir visibilidade
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            backgroundColor: '#dc3545',
            color: 'white',
            padding: '12px 20px',
            borderRadius: '4px',
            boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
            zIndex: '9999',
            fontSize: '14px',
            maxWidth: '300px'
        });
        
        document.body.appendChild(notification);
        
        // Remove após 5 segundos
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }
    
    // Métodos utilitários para formatação
    formatCurrency(amount) {
        const formats = {
            'pt-BR': { locale: 'pt-BR', currency: 'BRL' },
            'en-US': { locale: 'en-US', currency: 'USD' },
            'es-ES': { locale: 'es-ES', currency: 'EUR' }
        };
        
        const format = formats[this.currentLanguage] || formats['pt-BR'];
        
        try {
            return new Intl.NumberFormat(format.locale, {
                style: 'currency',
                currency: format.currency
            }).format(amount);
        } catch (error) {
            return `${amount.toFixed(2)}`;
        }
    }
    
    formatDate(date, options = {}) {
        const defaultOptions = {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit'
        };
        
        const formatOptions = { ...defaultOptions, ...options };
        
        try {
            return new Intl.DateTimeFormat(this.currentLanguage, formatOptions).format(date);
        } catch (error) {
            return date.toLocaleDateString();
        }
    }
}

// Inicializa o gerenciador quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    const mgr = new I18nManager();
    window.i18n = mgr;
    window.I18n = mgr; // Alias para compatibilidade com componentes
});

// Exporta para uso em outros scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = I18nManager;
}