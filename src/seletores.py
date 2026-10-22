"""Seletores do Legal One, extraidos sem alterar os valores observados.

Os blocos JS ficam inteiros para preservar eventos, ordem e leitura do DOM.
Templates apenas interpolam os mesmos valores que os f-strings anteriores.
Nao constituem evidencia de que a interface remota continua igual.
"""

JS_BUSCAR_PROCESSO = """
        const sentinela = !!document.querySelector('#Search');
        const vistas = new Set();
        const linhas = [];
        for (const tabela of document.querySelectorAll('table')) {
          for (const tr of tabela.querySelectorAll('tbody tr')) {
            if (vistas.has(tr)) continue;
            vistas.add(tr);
            const link = [...tr.querySelectorAll('a')]
              .map(a => a.getAttribute('href') || '')
              .find(h => h.includes('/processos/processos/details/'));
            if (!link) continue;
            linhas.push({
              cels: [...tr.querySelectorAll('td')].map(td => td.innerText.trim()),
              href: link,
            });
          }
        }
        return {sentinela: sentinela, linhas: linhas};
        """

JS_CONTAR_TAREFAS = """
        const sentinela = !!document.querySelector('#Search');
        for (const t of document.querySelectorAll('table')) {
          const cab = [...t.querySelectorAll('thead th, thead td')]
            .map(e => e.innerText.trim());
          const i = cab.findIndex(c => /Descri/i.test(c));
          if (i < 0) continue;
          return {sentinela: sentinela, descricoes: [...t.querySelectorAll('tbody tr')]
            .map(tr => {
              const c = tr.querySelectorAll('td');
              return i < c.length ? c[i].innerText.replace(/\\s+/g, ' ').trim() : '';
            })};
        }
        return {sentinela: sentinela, descricoes: null};
        """

ABRIR_STATUS = "#LookupStatusCompromissoTarefa .lookup-button.lookup-show"

LINHA_STATUS = ("//div[contains(@class,'lookup-dropdown')]"
                "//td[@data-val-field='Value' and normalize-space()='{status}']")

STATUS_TEXTO = "StatusText"

STATUS_ID = "StatusId"

RESPONSAVEL = "input[id*='__EnvolvidoText']"

LINHA_RESPONSAVEL = "td[data-val-field='ContatoNome']"

TIPO_TEXTO = "TipoText"

TIPO_ID = "TipoId"

ABRIR_TIPO = "#lookup_tipo .lookup-button.lookup-show"

LINHA_TIPO = "tr[id='{tipo_id}']"

EXPANDIR_TIPO = "tr[id='{pai}'] .expander"

CELULA = "td"

DATA_INICIAL = "DtInicial"

DATA_FINAL = "DtFinal"

HORA_INICIAL = "HrInicio"

HORA_FINAL = "HrFinal"

DATA_PUBLICACAO = "DtPublicacao"

DATA_DISPONIBILIZACAO = "AvailableDate"

DESCRICAO = "Descricao"

JS_FECHAR_AVISO_PENDO = """
        // offsetParent nao serve: e null em elemento position:fixed, que e
        // justamente como o aviso fica ancorado no canto da tela.
        const visivel = e => e && e.getClientRects().length > 0
          && getComputedStyle(e).visibility !== 'hidden';
        for (const guia of document.querySelectorAll(
            '#pendo-guide-container, ._pendo-step-container-styles')) {
          if (!visivel(guia)) continue;
          const botao = [...guia.querySelectorAll('button, ._pendo-close-guide')]
            .find(b => visivel(b) && (b.classList.contains('_pendo-close-guide')
                   || /^\\s*ok,?\\s*entendi\\s*$/i.test(b.innerText || '')));
          if (botao) { botao.click(); return true; }
        }
        return false;
        """

JS_ESPERAR_MASCARA_SUMIR = """
            return [...document.querySelectorAll('.modal-mask')]
              .some(m => m.getClientRects().length > 0
                         && getComputedStyle(m).visibility !== 'hidden');
            """

SALVAR = "//button[@name='ButtonSave' and @value='0']"

ERROS_VALIDACAO = (".field-validation-error, .validation-summary-errors, "
                     ".alert-danger, .span-error-validation-message")

JS_ERROS_DE_VALIDACAO = """
        return [...document.querySelectorAll(arguments[0])]
          .filter(e => e.getClientRects().length > 0)
          .map(e => e.innerText.trim()).filter(t => t).join(' | ');
        """

JS_AVISO_NA_TELA = """
        const ok = document.getElementById('popup_ok');
        if (!ok || ok.getClientRects().length === 0) return '';
        const caixa = document.getElementById('popup_message')
          || document.getElementById('popup_container') || ok.parentElement;
        const texto = (caixa.innerText || '').replace(/\\s+/g, ' ').trim();
        return texto || '(aviso sem texto)';
        """

CONFIRMAR_AVISO = "popup_ok"

RECUSAR_AVISO = "popup_cancel"

