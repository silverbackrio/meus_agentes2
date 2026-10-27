#!/usr/bin/env python3
"""Script de ingestão de dividendos e balanços — exemplo didático.
Observação: este é um esqueleto. Em projeto real, integra as fontes licenciadas
que passaram pela regra R8 (licença antes de automatizar) e respeita R1-R12.
"""
import os, sys, json, datetime
from pathlib import Path

ROOT = Path(".").parent.parent.parent.parent
DATA = ROOT / "dados"

def grava_dossie(classe, ativo, data_str, conteudo_md, fonte_nome, url_origem, licenca):
    arq = DATA / classe / ativo / f"{data_str}.md"
    arq.parent.mkdir(parents=True, exist_ok=True)
    if arq.exists():
        if arq.read_text(encoding="utf-8") == conteudo_md:
            print(f"⊘ Já existe para {classe}/{ativo}/{data_str}")
            return False
        print(f"⚠ Divergência: novo dado não sobrescreve o existente (R1)")
    cabecalho = f"""# Dossiê: {ativo}
- coleta: {datetime.date.today()} · anterior: {"primeira" if not arq.exists() else arq.parent / f'{arq.stem}.md'}
- alimenta a decisão: manter | revisão

"""
    assinatura = f"\n---\nFontes\n- fonte: {fonte_nome}\n- licenca: {licenca}\n- url: {url_origem}\n- fetched_at: {datetime.datetime.now().isoformat()}"
    arq.write_text(cabecalho + conteudo_md + assinatura, encoding="utf-8")
    print(f"✅ Gravado: {arq}")

def main():
    print("Script de ingestão de dividendos/balanços — exemplo didático")
    print("Em projeto real: verificar licença (R8), fazer fetch, calcular gap (R4), gravar (R1)")
    print("Regra R6: nenhuma chave impressa, nenhuma valor em log visível.")

if __name__ == "__main__":
    main()
