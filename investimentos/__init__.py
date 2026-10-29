"""Pacote raiz das apps Django do projeto de investimentos.

Por que este arquivo existe
---------------------------
Os três apps do projeto ficam em ``investimentos.<app>`` (``market_data``,
``carteira`` e ``analise``). Sem um ``__init__.py`` aqui, o pacote ``investimentos``
vira um *namespace package* e ferramentas como o pytest passam a importar os
módulos por caminhos "curtos" (``carteira.models`` em vez de
``investimentos.carteira.models``). Nesse caso o Django não encontra o app no
registro de aplicações e o teste quebra com:

    RuntimeError: Model class carteira.models.Objetivo doesn't declare an
    explicit app_label and isn't in an application in INSTALLED_APPS.

Manter este arquivo (vazio ou só com docstring) garante que código, testes e
comandos de manage.py enxerguem os mesmos módulos. Regra relacionada:
``specs/aplicacao.md`` (P1 — fronteira por módulo).
"""
