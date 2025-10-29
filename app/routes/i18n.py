"""
Rotas para gerenciamento de internacionalização.
"""

from flask import Blueprint, request, jsonify, redirect, url_for, current_app
from ..i18n import i18n

bp = Blueprint('i18n', __name__, url_prefix='/i18n')


@bp.route('/set-language/<language>', methods=['POST'])
def set_language(language):
    """
    Define o idioma da sessão do usuário.
    
    Args:
        language: Código do idioma (pt-BR, en-US, es-ES)
    
    Returns:
        JSON com status da operação ou redirect para página anterior
    """
    success = i18n.set_language(language)
    
    if request.is_json or request.headers.get('Content-Type') == 'application/json':
        if success:
            return jsonify({
                'success': True,
                'language': language,
                'message': i18n.translate('language_changed', language=i18n.translate(f'language.{language.replace("-", "_").lower()}'))
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Idioma não suportado'
            }), 400
    else:
        # Redirect para a página anterior ou dashboard
        next_page = request.form.get('next') or request.referrer or url_for('main.dashboard')
        return redirect(next_page)


@bp.route('/get-language', methods=['GET'])
def get_language():
    """
    Retorna o idioma atual e idiomas suportados.
    
    Returns:
        JSON com informações de idioma
    """
    return jsonify({
        'current_language': i18n.get_current_language(),
        'supported_languages': i18n.get_supported_languages(),
        'language_names': {
            'pt-BR': i18n.translate('language.portuguese'),
            'en-US': i18n.translate('language.english'),
            'es-ES': i18n.translate('language.spanish')
        }
    })


@bp.route('/translations/<namespace>', methods=['GET'])
def get_translations(namespace):
    """
    Retorna todas as traduções de um namespace para o idioma atual.
    Útil para aplicações JavaScript que precisam de traduções client-side.
    
    Args:
        namespace: Nome do namespace (common, auth, dashboard, etc.)
    
    Returns:
        JSON com traduções do namespace
    """
    language = i18n.get_current_language()
    
    if language in i18n.translations and namespace in i18n.translations[language]:
        return jsonify({
            'language': language,
            'namespace': namespace,
            'translations': i18n.translations[language][namespace]
        })
    else:
        return jsonify({
            'language': language,
            'namespace': namespace,
            'translations': {}
        }), 404