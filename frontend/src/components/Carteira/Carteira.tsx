import React from "react";
import { Link } from "react-router-dom";
import { analiseApi } from "../../api/analiseApi";

interface PosicaoResumo {
  ativo: string;
  classe: string;
  status?: string;
  quantidade: number;
  preco_medio: number;
  custo_total: number;
  moeda: string;
  instituicao: string;
  operacoes_count: number;
}

interface PesoPolitica {
  classe: string;
  peso_alvo: number;
  faixa_min: number;
  faixa_max: number;
  peso_atual: number;
  dentro_faixa: boolean;
}

interface Resumo {
  as_of: string;
  total_posicoes: number;
  custo_total_geral: number;
  posicoes: PosicaoResumo[];
  pesos_vs_politica: PesoPolitica[];
  pnl_total: number | null;
  pnl_total_pct: number | null;
}

const moeda = (valor: number) =>
  new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
    minimumFractionDigits: 2,
  }).format(valor);

const numero = (valor: number) =>
  new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 4 }).format(valor);

export const Carteira = () => {
  const [resumo, setResumo] = React.useState<Resumo | null>(null);
  const [carregando, setCarregando] = React.useState(true);
  const [erro, setErro] = React.useState<string | null>(null);

  const carregar = React.useCallback(() => {
    setCarregando(true);
    setErro(null);
    analiseApi
      .carteiraResumo()
      .then((resp) => {
        setResumo(resp.data);
        setCarregando(false);
      })
      .catch((e) => {
        setErro(
          e?.response?.data?.erro ||
            "Não foi possível carregar a carteira. O backend está rodando na 8901?",
        );
        setCarregando(false);
      });
  }, []);

  React.useEffect(() => {
    carregar();
  }, [carregar]);

  if (carregando) return <div className="loading">Carregando carteira...</div>;
  if (erro) return <div className="error">Erro: {erro}</div>;
  if (!resumo) return <div className="vazio">Sem dados de carteira.</div>;

  return (
    <section className="carteira-section">
      <div className="secao-topo">
        <h2>Carteira</h2>
        <div className="acoes-topo">
          <Link className="primary-btn" to="/carteira/nova">
            + Nova posição
          </Link>
          <button className="secondary-btn" onClick={carregar}>
            Atualizar
          </button>
        </div>
      </div>

      <p className="muted">
        Data-base: <strong>{resumo.as_of}</strong>
      </p>

      <div className="cards">
        <div className="card">
          <span className="card-rotulo">Posições</span>
          <strong>{resumo.total_posicoes}</strong>
        </div>
        <div className="card">
          <span className="card-rotulo">Custo total</span>
          <strong>{moeda(resumo.custo_total_geral)}</strong>
        </div>
        <div className="card">
          <span className="card-rotulo">P&amp;L não realizado</span>
          <strong>
            {resumo.pnl_total === null ? "—" : moeda(resumo.pnl_total)}
            {resumo.pnl_total_pct !== null && ` (${numero(resumo.pnl_total_pct)}%)`}
          </strong>
        </div>
      </div>

      {resumo.pnl_total === null && (
        <p className="muted small">
          P&amp;L fica indisponível enquanto não houver série de preço de mercado para a posição —
          o número não é estimado.
        </p>
      )}

      <h3>Posições</h3>
      {resumo.posicoes.length === 0 ? (
        <p className="vazio">
          Nenhuma posição cadastrada. Registre uma operação em <code>POST /api/v1/carteira/operacoes/</code>.
        </p>
      ) : (
        <table className="tabela">
          <thead>
            <tr>
              <th>Ativo</th>
              <th>Classe</th>
              <th>Instituição</th>
              <th>Qtd.</th>
              <th>Preço médio</th>
              <th>Custo total</th>
              <th>Situação</th>
              <th>Operações</th>
            </tr>
          </thead>
          <tbody>
            {resumo.posicoes.map((p) => (
              <tr key={`${p.ativo}-${p.instituicao}`}>
                <td>
                  <strong>{p.ativo}</strong>
                </td>
                <td>{p.classe}</td>
                <td>{p.instituicao || "—"}</td>
                <td>{numero(p.quantidade)}</td>
                <td>{moeda(p.preco_medio)}</td>
                <td>{moeda(p.custo_total)}</td>
                <td>
                  <span className={p.status === "encerrada" ? "selo fora" : "selo ok"}>
                    {p.status ?? "ativa"}
                  </span>
                </td>
                <td>{p.operacoes_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <h3>Pesos atuais vs. política</h3>
      {resumo.pesos_vs_politica.length === 0 ? (
        <p className="vazio">Nenhuma política de alocação definida.</p>
      ) : (
        <table className="tabela">
          <thead>
            <tr>
              <th>Classe</th>
              <th>Alvo</th>
              <th>Faixa</th>
              <th>Atual</th>
              <th>Situação</th>
            </tr>
          </thead>
          <tbody>
            {resumo.pesos_vs_politica.map((p) => (
              <tr key={p.classe}>
                <td>{p.classe}</td>
                <td>{numero(p.peso_alvo)}%</td>
                <td>
                  {numero(p.faixa_min)}% – {numero(p.faixa_max)}%
                </td>
                <td>{numero(p.peso_atual)}%</td>
                <td>
                  <span className={p.dentro_faixa ? "selo ok" : "selo fora"}>
                    {p.dentro_faixa ? "dentro" : "fora"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
};
