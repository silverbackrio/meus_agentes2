import React from "react";
import { analiseApi } from "../../api/analiseApi";

interface Cobertura {
  esperadas: number;
  presentes: number;
  faltantes: number;
  fracao: number;
  pct?: number;
  de: string;
  ate: string;
  gaps: [string, string][];
  primeira: string | null;
  ultima: string | null;
}

interface Serie {
  id: number;
  ativo: string;
  codigo: string;
  nome: string;
  unidade?: string;
  frequencia: string;
  moeda: string;
  as_of: string | null;
  observacoes: number;
  cobertura: Cobertura;
}

interface SerieLista {
  as_of: string | null;
  total: number;
  series: Serie[];
}

interface Pontos {
  unidade: string;
  fonte: { nome: string; licenca: string };
  periodo: { de: string; ate: string };
  pontos: [string, number][];
  gaps: [string, string][];
  sem_dado: boolean;
}

const numero = (valor: number) =>
  new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 4 }).format(valor);

export const Dados = () => {
  const [lista, setLista] = React.useState<SerieLista | null>(null);
  const [selecionada, setSelecionada] = React.useState<Serie | null>(null);
  const [pontos, setPontos] = React.useState<Pontos | null>(null);
  const [carregando, setCarregando] = React.useState(true);
  const [erro, setErro] = React.useState<string | null>(null);

  const carregarSeries = React.useCallback(() => {
    setCarregando(true);
    setErro(null);
    analiseApi
      .listSeries()
      .then((resp) => {
        setLista(resp.data);
        setCarregando(false);
      })
      .catch((e) => {
        setErro(
          e?.response?.data?.erro ||
            "Não foi possível carregar as séries. O backend está rodando na 8901?",
        );
        setCarregando(false);
      });
  }, []);

  React.useEffect(() => {
    carregarSeries();
  }, [carregarSeries]);

  const abrirSerie = (serie: Serie) => {
    setSelecionada(serie);
    setPontos(null);
    analiseApi
      .serieObservacoes(serie.id)
      .then((resp) => setPontos(resp.data))
      .catch(() => setPontos(null));
  };

  if (carregando) return <div className="loading">Carregando séries...</div>;
  if (erro) return <div className="error">Erro: {erro}</div>;

  return (
    <section className="dados-section">
      <div className="secao-topo">
        <h2>Séries de mercado</h2>
        <button className="secondary-btn" onClick={carregarSeries}>
          Atualizar
        </button>
      </div>

      <p className="muted">
        Banco local (leitura primeiro, sem chamada de rede). Data-base mais recente:{" "}
        <strong>{lista?.as_of ?? "sem dado"}</strong> · {lista?.total ?? 0} série(s)
      </p>

      {!lista || lista.series.length === 0 ? (
        <p className="vazio">
          Nenhuma série no banco ainda. Rode <code>manage.py ingest</code> para popular a base
          histórica.
        </p>
      ) : (
        <table className="tabela">
          <thead>
            <tr>
              <th>Série</th>
              <th>Código</th>
              <th>Freq.</th>
              <th>Cobertura</th>
              <th>Gaps</th>
              <th>Última</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {lista.series.map((s) => (
              <tr key={s.id} className={selecionada?.id === s.id ? "linha-ativa" : undefined}>
                <td>
                  <strong>{s.nome}</strong>
                  <div className="muted small">{s.ativo}</div>
                </td>
                <td>{s.codigo}</td>
                <td>{s.frequencia}</td>
                <td>
                  {s.cobertura.presentes}/{s.cobertura.esperadas} (
                  {numero(s.cobertura.fracao * 100)}%)
                  <div className="barra">
                    <span style={{ width: `${Math.min(100, s.cobertura.fracao * 100)}%` }} />
                  </div>
                </td>
                <td>{s.cobertura.gaps.length}</td>
                <td>{s.cobertura.ultima ?? "—"}</td>
                <td className="acoes-linha">
                  <button className="link-btn" onClick={() => abrirSerie(s)}>
                    Ver pontos
                  </button>
                  <a className="link-btn" href={`/api/v1/series/${s.id}/export.csv`}>
                    CSV
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {selecionada && (
        <div className="detalhe-serie">
          <h3>
            {selecionada.nome} · {selecionada.unidade ?? selecionada.moeda}
          </h3>
          {!pontos && <p className="muted">Carregando pontos...</p>}
          {pontos && (
            <>
              <p className="muted">
                Período {pontos.periodo.de} a {pontos.periodo.ate} · fonte {pontos.fonte.nome}{" "}
                ({pontos.fonte.licenca})
              </p>
              {pontos.sem_dado ? (
                <p className="vazio">Sem observação no período — a lacuna é relatada, não estimada.</p>
              ) : (
                <table className="tabela tabela-compacta">
                  <thead>
                    <tr>
                      <th>Data</th>
                      <th>Valor</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pontos.pontos.map(([data, valor]) => (
                      <tr key={data}>
                        <td>{data}</td>
                        <td>{numero(valor)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
              {pontos.gaps.length > 0 && (
                <p className="muted small">
                  Gaps:{" "}
                  {pontos.gaps.map(([a, b]) => `${a} → ${b}`).join(" · ")}
                </p>
              )}
            </>
          )}
        </div>
      )}
    </section>
  );
};
