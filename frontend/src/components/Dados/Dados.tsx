import React from "react";
import { analiseApi } from "../../api/analiseApi";
import { decimalMoedaLocal } from "../../utils/format";

export interface SerieItem {
  data: string;
  valor: number;
}

export interface DadosEnvelope {
  as_of: string;
  total: number;
  series: SerieItem[];
  cobertura: {
    esperadas: number;
    presentes: number;
    faltantes: number;
    fracao: number;
    de: string;
    ate: string;
    gaps: number[];
    primeira: string;
    ultima: string;
  };
  observacoes: string[];
}

export const Dados = () => {
  const [dados, setDados] = React.useState<DadosEnvelope | null>(null);
  const [carregando, setCarregando] = React.useState(true);
  const [erro, setErro] = React.useState<string | null>(null);

  React.useEffect(() => {
    analiseApi.listSeries().then((resp) => {
      const dadosResp = resp.data;
      if (!dadosResp || !dadosResp.series) {
        setCarregando(false);
        return;
      }
      const series = dadosResp.series.map((s: any) => ({
        data: s.data_base || s.data || "",
        valor: Number(s.valor) || 0,
      }));
      setDados({
        as_of: dadosResp.as_of || new Date().toISOString().split("T")[0],
        total: dadosResp.total || series.length,
        series: series,
        cobertura: dadosResp.cobertura || {
          esperadas: 0,
          presentes: 0,
          faltantes: 0,
          fracao: 0,
          de: "-",
          ate: "-",
          gaps: [],
          primeira: "-",
          ultima: "-",
        },
        observacoes: dadosResp.observacoes || [],
      });
      setCarregando(false);
    }).catch((_e) => {
      setErro("Erro ao carregar séries");
      setCarregando(false);
    });
  }, []);

  if (carregando) return <div className="loading">Carregando dados...</div>;
  if (erro) return <div className="error">Erro: {erro}</div>;
  if (!dados) return <div className="loading">Sem dados</div>;

  return (
    <section className="dados-section">
      <h2>Dados de Mercado</h2>

      <div className="dados-info">
        <p>Consulta em: {dados.as_of}</p>
        <p>Total de séries: {dados.total}</p>
      </div>

      <div className="cobertura-box">
        <h3>Cobertura</h3>
        <p>
          Período: {dados.cobertura.de} a {dados.cobertura.ate}
          <br />
          Expectativas: {dados.cobertura.esperadas} esperadas
          <br />
          Presentes: {dados.cobertura.presentes} present
          <br />
          Faltantes: {dados.cobertura.faltantes} faltando ({dados.cobertura.fracao}%)
        </p>
        <p>Primeira medição: {dados.cobertura.primeira}</p>
        <p>Última medição: {dados.cobertura.ultima}</p>
        <p>Gaps detectados: {dados.cobertura.gaps.length}</p>
      </div>

      <div className="series-list">
        <h3>Séries ({dados.series.length})</h3>
        <ul>
          {dados.series.map((s: SerieItem) => (
            <li key={s.data}>
              {s.data}: {decimalMoedaLocal(s.valor)}
            </li>
          ))}
        </ul>
        {dados.series.length === 0 && <p>Nenhuma série disponível</p>}
      </div>

      <div className="acoes">
        <button className="primary-btn">Exportar CSV</button>
        <button className="secondary-btn">Atualizar</button>
      </div>
    </section>
  );
};