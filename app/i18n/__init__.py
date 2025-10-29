"""
Sistema de Internacionalização (i18n) para o aplicativo de controle de gastos.

Este módulo fornece funcionalidades completas de internacionalização incluindo:
- Detecção automática do idioma do navegador
- Persistência de preferências via localStorage
- Sistema de fallback para textos não traduzidos
- Suporte a interpolação de variáveis
- Recursos de acessibilidade
"""

import json
import os
from typing import Dict, Any, Optional
from flask import request, session, current_app


class I18nManager:
    """Gerenciador principal do sistema de internacionalização."""
    
    def __init__(self, app=None):
        self.app = app
        self.translations = {}
        self.supported_languages = ['pt-BR', 'en-US', 'es-ES']
        self.default_language = 'pt-BR'
        self.current_language = self.default_language
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializa o sistema i18n com a aplicação Flask."""
        self.app = app
        app.i18n = self
        
        # Carrega todas as traduções
        self.load_translations()
        
        # Registra funções de template
        app.jinja_env.globals['_'] = self.translate
        app.jinja_env.globals['get_current_language'] = self.get_current_language
        app.jinja_env.globals['get_supported_languages'] = self.get_supported_languages
        app.jinja_env.globals['get_language_name'] = self.get_language_name
        app.jinja_env.globals['format_currency'] = self.format_currency
        app.jinja_env.globals['format_date'] = self.format_date
        
        # Hook para detectar idioma antes de cada request
        @app.before_request
        def detect_language():
            self.detect_and_set_language()
    
    def load_translations(self):
        """Carrega todos os arquivos de tradução."""
        i18n_dir = os.path.join(os.path.dirname(__file__))
        
        for lang in self.supported_languages:
            lang_dir = os.path.join(i18n_dir, lang)
            if os.path.exists(lang_dir):
                self.translations[lang] = {}
                
                # Carrega todos os arquivos JSON do idioma
                for filename in os.listdir(lang_dir):
                    if filename.endswith('.json'):
                        namespace = filename[:-5]  # Remove .json
                        filepath = os.path.join(lang_dir, filename)
                        
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                self.translations[lang][namespace] = json.load(f)
                        except Exception as e:
                            current_app.logger.error(f"Erro ao carregar {filepath}: {e}")
    
    def detect_and_set_language(self):
        """Detecta e define o idioma atual baseado em prioridades."""
        # 1. Idioma da sessão (preferência do usuário)
        if 'language' in session and session['language'] in self.supported_languages:
            self.current_language = session['language']
            return
        
        # 2. Idioma do cabeçalho Accept-Language do navegador
        if request and hasattr(request, 'accept_languages'):
            for lang in request.accept_languages:
                # Verifica correspondência exata
                if lang[0] in self.supported_languages:
                    self.current_language = lang[0]
                    session['language'] = lang[0]
                    return
                
                # Verifica correspondência por código de idioma base
                lang_code = lang[0].split('-')[0]
                for supported in self.supported_languages:
                    if supported.startswith(lang_code):
                        self.current_language = supported
                        session['language'] = supported
                        return
        
        # 3. Fallback para idioma padrão
        self.current_language = self.default_language
        session['language'] = self.default_language
    
    def set_language(self, language: str):
        """Define manualmente o idioma atual."""
        if language in self.supported_languages:
            self.current_language = language
            session['language'] = language
            return True
        return False
    
    def get_current_language(self) -> str:
        """Retorna o idioma atual."""
        return self.current_language
    
    def get_supported_languages(self) -> list:
        """Retorna lista de idiomas suportados."""
        return self.supported_languages

    def get_language_name(self, code: str) -> str:
        """Retorna o nome legível do idioma conforme o idioma atual da interface."""
        code = (code or '').strip()
        # Tenta usar chaves de tradução se existirem
        try:
            if code == 'pt-BR':
                name = self.translate('language.portuguese')
            elif code == 'en-US':
                name = self.translate('language.english')
            elif code == 'es-ES':
                name = self.translate('language.spanish')
            else:
                name = code
        except Exception:
            name = code
        # Fallback específico para pt-BR se não houver chaves
        if name == code:
            fallback_pt = {
                'pt-BR': 'Português',
                'en-US': 'Inglês',
                'es-ES': 'Espanhol',
            }
            fallback_en = {
                'pt-BR': 'Portuguese',
                'en-US': 'English',
                'es-ES': 'Spanish',
            }
            fallback_es = {
                'pt-BR': 'Portugués',
                'en-US': 'Inglés',
                'es-ES': 'Español',
            }
            current = self.get_current_language()
            mapping = fallback_pt
            if current == 'en-US':
                mapping = fallback_en
            elif current == 'es-ES':
                mapping = fallback_es
            name = mapping.get(code, code)
        return name
    
    def translate(self, key: str, namespace: str = 'common', **kwargs) -> str:
        """
        Traduz uma chave para o idioma atual.
        
        Args:
            key: Chave da tradução (pode usar notação de ponto para objetos aninhados)
            namespace: Namespace da tradução (arquivo JSON)
            **kwargs: Variáveis para interpolação
        
        Returns:
            Texto traduzido com interpolação aplicada
        """
        # Tenta obter tradução no idioma atual
        translation = self._get_translation(key, namespace, self.current_language)
        
        # Fallback para idioma padrão se não encontrar
        if translation is None and self.current_language != self.default_language:
            translation = self._get_translation(key, namespace, self.default_language)
        
        # Fallback final para a própria chave
        if translation is None:
            translation = key
        
        # Aplica interpolação de variáveis
        return self._interpolate(translation, **kwargs)
    
    def _get_translation(self, key: str, namespace: str, language: str) -> Optional[str]:
        """Obtém uma tradução específica."""
        if language not in self.translations:
            return None
        
        if namespace not in self.translations[language]:
            return None
        
        # Navega pela estrutura usando notação de ponto
        current = self.translations[language][namespace]
        for part in key.split('.'):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        
        return current if isinstance(current, str) else None
    
    def _interpolate(self, text: str, **kwargs) -> str:
        """Aplica interpolação de variáveis no texto."""
        if not kwargs:
            return text
        
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            # Se a interpolação falhar, retorna o texto original
            return text
    
    def format_currency(self, amount: float) -> str:
        """Formata valor monetário de acordo com o idioma atual."""
        currency_info = self._get_translation('currency', 'common', self.current_language)
        
        if currency_info and isinstance(currency_info, dict):
            symbol = currency_info.get('symbol', 'R$')
            format_str = currency_info.get('format', 'R$ {amount}')
            decimal_sep = currency_info.get('decimal_separator', ',')
            thousand_sep = currency_info.get('thousand_separator', '.')
        else:
            # Fallback para formato brasileiro
            symbol = 'R$'
            format_str = 'R$ {amount}'
            decimal_sep = ','
            thousand_sep = '.'
        
        # Formata o número
        formatted_amount = f"{amount:,.2f}".replace(',', 'TEMP').replace('.', decimal_sep).replace('TEMP', thousand_sep)
        
        return format_str.format(amount=formatted_amount)
    
    def format_date(self, date_obj, format_type: str = 'short') -> str:
        """Formata data de acordo com o idioma atual."""
        if not date_obj:
            return ''
        
        date_formats = self._get_translation('date_formats', 'common', self.current_language)
        
        if date_formats and isinstance(date_formats, dict):
            format_str = date_formats.get(format_type, '%d/%m/%Y')
        else:
            format_str = '%d/%m/%Y'  # Fallback brasileiro
        
        try:
            return date_obj.strftime(format_str)
        except:
            return str(date_obj)


# Instância global do gerenciador
i18n = I18nManager()


def init_i18n(app):
    """Função de conveniência para inicializar i18n."""
    i18n.init_app(app)
    return i18n


# Função de conveniência para templates
def _(key: str, namespace: str = 'common', **kwargs) -> str:
    """Função de tradução para uso em templates e código Python."""
    return i18n.translate(key, namespace, **kwargs)