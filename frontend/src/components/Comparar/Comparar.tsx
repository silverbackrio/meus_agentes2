import React from "react";
import { analiseApi } from "../../api/analiseApi";

interface Bloco {
  valor: number;
  unidade: string;
  data_base: string;
}

interface Item {
  nome: string;
  prazo_dias: number;
  tipo: "isento" | "tributado";
  taxa_bruta: Bloco;
  ir: { aliquota: Bloco; faixa: string; norma: string };
  bruto: Bloco;
  imposto: Bloco;
  iof: Bloco;
  rendimento_liquido: Bloco;
  valor_recebido: Bloco;
  taxa_liquida: Bloco;
  valor_recebido_no_prazo_comum: Bloco;
}

interface Comparacao {
  base: string;
  data_base: string;
  valor_inicial: Bloco;
  convencao: { dias_base: number; periodo: string; unidade_taxa: string };
  prazo_comum_dias: number;
  itens: Item[];
  formula: Record<string, string>;
  normas: string[];
  riscos: string[];
  aviso: string;
}

const EXEMPLO = "CDB Banco A|10|720|tributado,LCI Banco B|11.5|365|isento";

const moeda = (valor: number) =>
  new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
    minimumFractionDigits: 2,
  }).format(valor);

const numero = (valor: number) =>
  new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 2 }).format(valor);

export const Comparar = () => {
  const [ativos, setAtivos] = React.useState(EXEMPLO);
  const [valor, setValor] = React.useState("10000");
  const [resultado, setResultado] = React.useState<Comparacao | null>(null);
  const [erro, setErro] = React.useState<string | null>(null);
  const [carregando, setCarregando] = React.useState(false);

  const comparar = (evento: React.FormEvent) => {
    evento.preventDefault();
    setCarregando(true);
    setErro(null);
    const valorNumerico = valor.trim() === "" ? undefined : Number(valor.replace(",", "."));
    analiseApi
      .comparar(ativos, "liquida", Number.isFinite(valorNumerico) ? valorNumerico : undefined)
      .then((resp) => {
        setResultado(resp.data);
        setCarregando(false);
      })
      .catch((e) => {
        const dados = e?.response?.data;
        setResultado(null);
        setErro(
          dados
            ? `${dados.erro ?? "Entrada inválida"} — ${dados.sugestao ?? ""}`
            : "Não foi possível comparar. O backend está rodando na 8901?",
        );
        setCarregando(false);
      });
  };

  return (
    <section className="comparar-section">
      <h2>Comparar produtos em base líquida</h2>
      <p className="muted">
        Cada produto entra como <code>nome|taxa_a_a|prazo_dias|tipo</code>, separado por vírgula.
        O tipo é <code>isento</code> (LCI/LCA/CRI/CRA) ou <code>tributado</code>. A comparação é
        sempre em base líquida, com IR e IOF aplicados.
      </p>

      <form className="form-comparar" onSubmit={comparar}>
        <label>
          Produtos
          <textarea
            value={ativos}
            onChange={(e) => setAtivos(e.target.value)}
            rows={3}
            placeholder={EXEMPLO}
          />
        </label>
        <label>
          Valor inicial (R$)
          <input
            type="text"
            inputMode="decimal"
            value={valor}
            onChange={(e) => setValor(e.target.value)}
            placeholder="10000"
          />
        </label>
        <button className="primary-btn" type="submit" disabled={carregando}>
          {carregando ? "Comparando..." : "Comparar"}
        </button>
      </form>

      {erro && <div className="error">Erro: {erro}</div>}

      {resultado && (
        <div className="resultado-comparar">
          <p className="muted">
            Valor inicial {moeda(resultado.valor_inicial.valor)} · prazo comum{" "}
            {resultado.prazo_comum_dias} dias · base {resultado.convencao.dias_base} ·{" "}
            {resultado.convencao.unidade_taxa} · data-base {resultado.data_base}
          </p>

          <table className="tabela">
            <thead>
              <tr>
                <th>Produto</th>
                <th>Tipo</th>
                <th>Prazo</th>
                <th>Bruta</th>
                <th>IR</th>
                <th>Bruto</th>
                <th>Imposto</th>
                <th>IOF</th>
                <th>Líquido</th>
                <th>Recebido</th>
                <th>Taxa líq.</th>
              </tr>
            </thead>
            <tbody>
              {resultado.itens.map((item) => (
                <tr key={item.nome}>
                  <td>
                    <strong>{item.nome}</strong>
                  </td>
                  <td>
                    <span className={item.tipo === "isento" ? "selo ok" : "selo neutro"}>
                      {item.tipo}
                    </span>
                  </td>
                  <td>{item.prazo_dias}d</td>
                  <td>{numero(item.taxa_bruta.valor)}% a.a.</td>
                  <td>{numero(item.ir.aliquota.valor)}%</td>
                  <td>{moeda(item.bruto.valor)}</td>
                  <td>{moeda(item.imposto.valor)}</td>
                  <td>{moeda(item.iof.valor)}</td>
                  <td>{moeda(item.rendimento_liquido.valor)}</td>
                  <td>{moeda(item.valor_recebido.valor)}</td>
                  <td>{numero(item.taxa_liquida.valor)}% a.a.</td>
                </tr>
              ))}
            </tbody>
          </table>

          <h3>Como o número foi calculado</h3>
          <ul className="lista-formulas">
            {Object.entries(resultado.formula).map(([chave, texto]) => (
              <li key={chave}>
                <code>{chave}</code>: {texto}
              </li>
            ))}
          </ul>

          <h3>Normas</h3>
          <ul className="lista-formulas">
            {resultado.normas.map((norma) => (
              <li key={norma}>{norma}</li>
            ))}
          </ul>

          <h3>Riscos a considerar</h3>
          <ul className="lista-formulas">
            {resultado.riscos.map((risco) => (
              <li key={risco}>{risco}</li>
            ))}
          </ul>

          <p className="aviso">{resultado.aviso}</p>
        </div>
      )}
    </section>
  );
};
