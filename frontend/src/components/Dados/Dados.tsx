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

  React.useEffect(() => {
    analiseApi.listMetricas().then((_resp) => {
      // TODO: Implement listSeries when available
      setDados({
        as_of: new Date().toISOString().split("T")[0],
        total: 0,
        series: [],
        cobertura: {
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
        observacoes: ["Dados disponíveis via API /series/"],
      });
      setCarregando(false);
    }).catch((_e) => {
      setCarregando(false);
    });
  }, []);

  if (carregando) return <div className="loading">Carregando dados...</div>;
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