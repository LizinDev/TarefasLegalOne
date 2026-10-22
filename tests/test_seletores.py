"""Contrato literal anterior a extracao: nao depende do navegador real."""

import pytest

import seletores

ANTERIORES = {'JS_BUSCAR_PROCESSO': '\n'
                       '        const sentinela = '
                       "!!document.querySelector('#Search');\n"
                       '        const vistas = new Set();\n'
                       '        const linhas = [];\n'
                       '        for (const tabela of '
                       "document.querySelectorAll('table')) {\n"
                       "          for (const tr of tabela.querySelectorAll('tbody "
                       "tr')) {\n"
                       '            if (vistas.has(tr)) continue;\n'
                       '            vistas.add(tr);\n'
                       "            const link = [...tr.querySelectorAll('a')]\n"
                       "              .map(a => a.getAttribute('href') || '')\n"
                       '              .find(h => '
                       "h.includes('/processos/processos/details/'));\n"
                       '            if (!link) continue;\n'
                       '            linhas.push({\n'
                       "              cels: [...tr.querySelectorAll('td')].map(td => "
                       'td.innerText.trim()),\n'
                       '              href: link,\n'
                       '            });\n'
                       '          }\n'
                       '        }\n'
                       '        return {sentinela: sentinela, linhas: linhas};\n'
                       '        ',
 'JS_CONTAR_TAREFAS': '\n'
                      '        const sentinela = '
                      "!!document.querySelector('#Search');\n"
                      "        for (const t of document.querySelectorAll('table')) "
                      '{\n'
                      "          const cab = [...t.querySelectorAll('thead th, thead "
                      "td')]\n"
                      '            .map(e => e.innerText.trim());\n'
                      '          const i = cab.findIndex(c => /Descri/i.test(c));\n'
                      '          if (i < 0) continue;\n'
                      '          return {sentinela: sentinela, descricoes: '
                      "[...t.querySelectorAll('tbody tr')]\n"
                      '            .map(tr => {\n'
                      "              const c = tr.querySelectorAll('td');\n"
                      '              return i < c.length ? '
                      "c[i].innerText.replace(/\\s+/g, ' ').trim() : '';\n"
                      '            })};\n'
                      '        }\n'
                      '        return {sentinela: sentinela, descricoes: null};\n'
                      '        ',
 'ABRIR_STATUS': '#LookupStatusCompromissoTarefa .lookup-button.lookup-show',
 'LINHA_STATUS': "//div[contains(@class,'lookup-dropdown')]//td[@data-val-field='Value' "
                 "and normalize-space()='{status}']",
 'STATUS_TEXTO': 'StatusText',
 'STATUS_ID': 'StatusId',
 'RESPONSAVEL': "input[id*='__EnvolvidoText']",
 'LINHA_RESPONSAVEL': "td[data-val-field='ContatoNome']",
 'TIPO_TEXTO': 'TipoText',
 'TIPO_ID': 'TipoId',
 'ABRIR_TIPO': '#lookup_tipo .lookup-button.lookup-show',
 'LINHA_TIPO': "tr[id='{tipo_id}']",
 'EXPANDIR_TIPO': "tr[id='{pai}'] .expander",
 'CELULA': 'td',
 'DATA_INICIAL': 'DtInicial',
 'DATA_FINAL': 'DtFinal',
 'HORA_INICIAL': 'HrInicio',
 'HORA_FINAL': 'HrFinal',
 'DATA_PUBLICACAO': 'DtPublicacao',
 'DATA_DISPONIBILIZACAO': 'AvailableDate',
 'DESCRICAO': 'Descricao',
 'JS_FECHAR_AVISO_PENDO': '\n'
                          '        // offsetParent nao serve: e null em elemento '
                          'position:fixed, que e\n'
                          '        // justamente como o aviso fica ancorado no canto '
                          'da tela.\n'
                          '        const visivel = e => e && '
                          'e.getClientRects().length > 0\n'
                          '          && getComputedStyle(e).visibility !== '
                          "'hidden';\n"
                          '        for (const guia of document.querySelectorAll(\n'
                          "            '#pendo-guide-container, "
                          "._pendo-step-container-styles')) {\n"
                          '          if (!visivel(guia)) continue;\n'
                          '          const botao = '
                          "[...guia.querySelectorAll('button, "
                          "._pendo-close-guide')]\n"
                          '            .find(b => visivel(b) && '
                          "(b.classList.contains('_pendo-close-guide')\n"
                          '                   || '
                          "/^\\s*ok,?\\s*entendi\\s*$/i.test(b.innerText || '')));\n"
                          '          if (botao) { botao.click(); return true; }\n'
                          '        }\n'
                          '        return false;\n'
                          '        ',
 'JS_ESPERAR_MASCARA_SUMIR': '\n'
                             '            return '
                             "[...document.querySelectorAll('.modal-mask')]\n"
                             '              .some(m => m.getClientRects().length > '
                             '0\n'
                             '                         && '
                             "getComputedStyle(m).visibility !== 'hidden');\n"
                             '            ',
 'SALVAR': "//button[@name='ButtonSave' and @value='0']",
 'ERROS_VALIDACAO': '.field-validation-error, .validation-summary-errors, '
                    '.alert-danger, .span-error-validation-message',
 'JS_ERROS_DE_VALIDACAO': '\n'
                          '        return '
                          '[...document.querySelectorAll(arguments[0])]\n'
                          '          .filter(e => e.getClientRects().length > 0)\n'
                          '          .map(e => e.innerText.trim()).filter(t => '
                          "t).join(' | ');\n"
                          '        ',
 'JS_AVISO_NA_TELA': '\n'
                     "        const ok = document.getElementById('popup_ok');\n"
                     '        if (!ok || ok.getClientRects().length === 0) return '
                     "'';\n"
                     '        const caixa = '
                     "document.getElementById('popup_message')\n"
                     "          || document.getElementById('popup_container') || "
                     'ok.parentElement;\n'
                     "        const texto = (caixa.innerText || '').replace(/\\s+/g, "
                     "' ').trim();\n"
                     "        return texto || '(aviso sem texto)';\n"
                     '        ',
 'CONFIRMAR_AVISO': 'popup_ok',
 'RECUSAR_AVISO': 'popup_cancel'}


@pytest.mark.parametrize("nome", ANTERIORES)
def test_seletor_preserva_literal(nome):
    assert getattr(seletores, nome) == ANTERIORES[nome]
