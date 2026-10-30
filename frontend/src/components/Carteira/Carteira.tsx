import React from "react";
import { analiseApi } from "../../api/analiseApi";
import { decimalMoedaLocal } from "../../utils/format";

export interface Posicao {
  codigo: string;
  nome: string;
  tipo: "renda_fixa" | "renda_variavel" | "fundo";
  quantidade: number;
  preco_medio: number;
  preco_atual: number;
  pnl: number;
  pnl_percentual: number;
}

export interface CarteiraEnvelope {
  data: string;
  total: number;
  posicoes: Posicao[];
  resumo: {
    total_investido: number;
    valor_atual: number;
    ganho_perda: number;
    ganho_percentual: number;
    peso_renda_fixa: number;
    peso_renda_variavel: number;
    peso_fundos: number;
  };
}

export const Carteira = () => {
  const [carteira, setCarteira] = React.useState<CarteiraEnvelope | null>(null);
  const [carregando, setCarregando] = React.useState(true);
  const [erro, setErro] = React.useState<string | null>(null);

  React.useEffect(() => {
    analiseApi.listPosicoes().then((resp) => {
      const dados = resp.data;
      if (!dados || !dados.posicoes) {
        setCarregando(false);
        return;
      }

      const posicoesMap = dados.posicoes.map((p: any) => ({
        codigo: p.codigo || "",
        nome: p.nome || "",
        tipo: p.tipo || "renda_fixa",
        quantidade: Number(p.quantidade) || 0,
        preco_medio: Number(p.preco_medio) || 0,
        preco_atual: Number(p.preco_atual) || 0,
        pnl: Number(p.pnl) || 0,
        pnl_percentual: Number(p.pnl_percentual) || 0,
      }));

      const resumo = {
        total_investido: Number(dados.total_investido) || 0,
        valor_atual: Number(dados.valor_atual) || 0,
        ganho_perda: Number(dados.ganho_perda) || 0,
        ganho_percentual: Number(dados.ganho_percentual) || 0,
        peso_renda_fixa: Number(dados.peso_renda_fixa) || 0,
        peso_renda_variavel: Number(dados.peso_renda_variavel) || 0,
        peso_fundos: Number(dados.peso_fundos) || 0,
      };

      setCarteira({
        data: dados.data || new Date().toISOString().split("T")[0],
        total: posicoesMap.length,
        posicoes: posicoesMap,
        resumo,
      });
      setCarregando(false);
    }).catch((_e) => {
      setErro("Erro ao carregar carteira");
      setCarregando(false);
    });
  }, []);

  if (carregando) return <div className="loading">Carregando dados da carteira...</div>;
  if (erro) return <div className="error">Erro: {erro}</div>;
  if (!carteira) return <div className="loading">Sem dados da carteira</div>;

  return (
    <section className="carteira-section">
      <h2>Resumo da Carteira</h2>

      <div className="resumo-box">
        <p>Data da consulta: {carteira.data}</p>
        <p>Total de posições: {carteira.total}</p>
        <p>Total investido: {decimalMoedaLocal(carteira.resumo.total_investido)}</p>
        <p>Valor atual: {decimalMoedaLocal(carteira.resumo.valor_atual)}</p>
        <p>Ganho/Perdas: {decimalMoedaLocal(carteira.resumo.ganho_perda)} ({carteira.resumo.ganho_percentual}%)</p>
      </div>

      <div className="alocacao">
        <h3>Alocação por tipo</h3>
        <p>Renda fixa: {carteira.resumo.peso_renda_fixa}%</p>
        <p>Renda variável: {carteira.resumo.peso_renda_variavel}%</p>
        <p>Fundos: {carteira.resumo.peso_fundos}%</p>
      </div>

      <div className="posicoes-lista">
        <h3>Posições ({carteira.posicoes.length})</h3>
        <table>
          <thead>
            <tr>
              <th>Código</th>
              <th>Nome</th>
              <th>Tipo</th>
              <th>Qtd</th>
              <th>Preço Médio</th>
              <th>Preço Atual</th>
              <th>P/L</th>
              <th>% P/L</th>
            </tr>
          </thead>
          <tbody>
            {carteira.posicoes.map((p: Posicao) => (
              <tr key={p.codigo}>
                <td>{p.codigo}</td>
                <td>{p.nome}</td>
                <td>{p.tipo}</td>
                <td>{p.quantidade}</td>
                <td>{decimalMoedaLocal(p.preco_medio)}</td>
                <td>{decimalMoedaLocal(p.preco_atual)}</td>
                <td>{decimalMoedaLocal(p.pnl)}</td>
                <td>{decimalMoedaLocal(p.pnl_percentual)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
        {carteira.posicoes.length === 0 && <p>Nenhuma posição disponível</p>}
      </div>

      <div className="acoes">
        <button className="primary-btn">Exportar CSV</button>
        <button className="secondary-btn">Atualizar</button>
      </div>
    </section>
  );
};