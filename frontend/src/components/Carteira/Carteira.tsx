import React from "react";
import { analiseApi } from "../../api/analiseApi";
import { decimalMoedaLocal } from "../../utils/format";

export interface Posicao {
  ativo: string;
  tipo: "renda_fixa" | "acao" | "fundo" | "outro";
  quantidade: number;
  preco_medio: number;
  valor_total: number;
  pnl: number;
  pnl_pct: number;
}

export interface ResumoCarteira {
  data_referencia: string;
  total_posicoes: number;
  custo_total_geral: number;
  pnl_total: number;
  pesos_vs_politica: any[];
}

export const Carteira = () => {
  const [carregando, setCarregando] = React.useState(true);
  const [resumo, setResumo] = React.useState<ResumoCarteira | null>(null);
  const [posicoes, setPosicoes] = React.useState<Posicao[] | null>(null);    React.useEffect(() => {
    analiseApi.listMetricas().then((_resp) => {
      // TODO: Implement listPosicoes when available
      setResumo({
        data_referencia: new Date().toISOString().split("T")[0],
        total_posicoes: 0,
        custo_total_geral: 0,
        pnl_total: 0,
        pesos_vs_politica: [],
      });
      setPosicoes([]);
      setCarregando(false);
    }).catch((_e) => {
      setCarregando(false);
    });
  }, []);

  if (carregando) return <div className="loading">Carregando carteira...</div>;

  return (
    <section className="carteira-section">
      <h2>Carteira de Investimentos</h2>

      <div className="resumo-box">
        <h3>Resumo</h3>
        <p>Data de referência: {resumo?.data_referencia}</p>
        <p>Total de posições: {resumo?.total_posicoes}</p>
        <p>Custo total geral: {decimalMoedaLocal(resumo?.custo_total_geral ?? 0)}</p>
        <p>P&L total: {decimalMoedaLocal(resumo?.pnl_total ?? 0)}</p>
      </div>

      <div className="posicoes-list">
        <h3>Posições ({resumo?.total_posicoes || 0})</h3>
        {posicoes && posicoes.length > 0 ? (
          <ul>
            {posicoes.map((p: Posicao) => (
              <li key={p.ativo}>
                {p.ativo} ({p.tipo}): {p.quantidade} x R$ {p.preco_medio} = R$ {p.valor_total}
                <br />
                P&L: {decimalMoedaLocal(p.pnl)} ({p.pnl_pct >= 0 ? "+" : ""}{p.pnl_pct}%)
              </li>
            ))}
          </ul>
        ) : <p>Nenhuma posição cadastrada</p>}
      </div>

      <div className="acoes">
        <button className="primary-btn">Atualizar Carteira</button>
        <button className="secondary-btn">Importar CSV</button>
      </div>
    </section>
  );
};