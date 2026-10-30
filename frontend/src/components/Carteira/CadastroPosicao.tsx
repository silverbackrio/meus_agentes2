import React from "react";
import { analiseApi } from "../../api/analiseApi";

interface CampoSchema {
  nome: string;
  rotulo: string;
  tipo: string;
  obrigatorio: boolean;
  unidade: string;
  opcoes: string[];
  ajuda: string;
}

interface EventoSchema {
  nome: string;
  rotulo: string;
}

interface ClasseSchema {
  nome: string;
  rotulo: string;
  nota: string;
  campos: CampoSchema[];
  eventos: EventoSchema[];
}

interface Esquema {
  classes: ClasseSchema[];
  custos: CampoSchema[];
  eventos: Record<string, string>;
}

interface Posicao {
  id: number;
  ativo: string;
  classe: string;
  status: string;
}

type Valor = string | boolean;

const limpar = (obj: Record<string, Valor>) =>
  Object.fromEntries(Object.entries(obj).filter(([, valor]) => valor !== "" && valor !== undefined));

const moeda = (valor: number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(valor);

export const CadastroPosicao = () => {
  const [esquema, setEsquema] = React.useState<Esquema | null>(null);
  const [posicoes, setPosicoes] = React.useState<Posicao[]>([]);
  const [erro, setErro] = React.useState<string | null>(null);
  const [mensagem, setMensagem] = React.useState<string | null>(null);

  // --- cadastro da posição ---
  const [classeNome, setClasseNome] = React.useState("acoes");
  const [atributos, setAtributos] = React.useState<Record<string, Valor>>({});
  const [ativo, setAtivo] = React.useState("");
  const [instituicao, setInstituicao] = React.useState("");
  const [quantidade, setQuantidade] = React.useState("");
  const [precoMedio, setPrecoMedio] = React.useState("");
  const [dataEntrada, setDataEntrada] = React.useState("");

  // --- registro de evento ---
  const [posicaoId, setPosicaoId] = React.useState("");
  const [evento, setEvento] = React.useState("aplicacao");
  const [dataEvento, setDataEvento] = React.useState("");
  const [valorEvento, setValorEvento] = React.useState("");
  const [quantidadeEvento, setQuantidadeEvento] = React.useState("");
  const [custos, setCustos] = React.useState<Record<string, string>>({});
  const [resultado, setResultado] = React.useState<{ evento: string; custo_total: number; valor_efeito: number } | null>(
    null,
  );

  const carregarPosicoes = React.useCallback(() => {
    analiseApi
      .listPosicoes()
      .then((resp) => setPosicoes(resp.data))
      .catch(() => setPosicoes([]));
  }, []);

  React.useEffect(() => {
    analiseApi
      .carteiraClasses()
      .then((resp) => setEsquema(resp.data))
      .catch((e) =>
        setErro(e?.response?.data?.erro || "Não foi possível carregar as classes. A API está na 8901?"),
      );
    carregarPosicoes();
  }, [carregarPosicoes]);

  const classeAtual = esquema?.classes.find((item) => item.nome === classeNome);
  const posicaoAtual = posicoes.find((item) => String(item.id) === posicaoId);
  const classeDaPosicao = esquema?.classes.find((item) => item.nome === posicaoAtual?.classe);

  const trocarClasse = (nome: string) => {
    setClasseNome(nome);
    setAtributos({});
    setMensagem(null);
    setErro(null);
  };

  const cadastrarPosicao = (eventoForm: React.FormEvent) => {
    eventoForm.preventDefault();
    setErro(null);
    setMensagem(null);
    analiseApi
      .criarPosicao({
        ativo,
        classe: classeNome,
        instituicao,
        quantidade: quantidade || "0",
        preco_medio: precoMedio || "0",
        data_entrada: dataEntrada || null,
        atributos: limpar(atributos),
      })
      .then((resp) => {
        setMensagem(`Posição cadastrada: ${resp.data.ativo} (${resp.data.classe}).`);
        setAtivo("");
        setQuantidade("");
        setPrecoMedio("");
        setDataEntrada("");
        setAtributos({});
        carregarPosicoes();
      })
      .catch((e) => setErro(e?.response?.data?.erro || "Não foi possível cadastrar a posição."));
  };

  const registrarEvento = (eventoForm: React.FormEvent) => {
    eventoForm.preventDefault();
    setErro(null);
    setMensagem(null);
    setResultado(null);
    const custosInformados = Object.fromEntries(Object.entries(custos).filter(([, valor]) => valor !== ""));
    analiseApi
      .criarOperacao({
        posicao_id: posicaoId,
        evento,
        data: dataEvento,
        valor: valorEvento,
        quantidade: quantidadeEvento || "0",
        custos: custosInformados,
      })
      .then((resp) => {
        setResultado({
          evento: resp.data.evento,
          custo_total: Number(resp.data.custo_total),
          valor_efeito: Number(resp.data.valor_efeito),
        });
        setValorEvento("");
        setQuantidadeEvento("");
        setCustos({});
        carregarPosicoes();
      })
      .catch((e) => {
        const dados = e?.response?.data;
        setErro(
          dados
            ? `${dados.erro ?? "Entrada inválida"} — ${dados.sugestao ?? ""}`
            : "Não foi possível registrar o evento.",
        );
      });
  };

  const renderCampo = (campo: CampoSchema) => {
    const valor = atributos[campo.nome];

    if (campo.tipo === "booleano") {
      return (
        <label className="campo-check" key={campo.nome}>
          <input
            type="checkbox"
            checked={Boolean(valor)}
            onChange={(e) => setAtributos({ ...atributos, [campo.nome]: e.target.checked })}
          />
          <span>{campo.rotulo}</span>
          {campo.ajuda && <small className="ajuda">{campo.ajuda}</small>}
        </label>
      );
    }

    if (campo.tipo === "opcao") {
      return (
        <label key={campo.nome}>
          <span>
            {campo.rotulo}
            {campo.obrigatorio ? " *" : ""}
          </span>
          <select
            value={String(valor ?? "")}
            required={campo.obrigatorio}
            onChange={(e) => setAtributos({ ...atributos, [campo.nome]: e.target.value })}
          >
            <option value="">selecione</option>
            {campo.opcoes.map((opcao) => (
              <option key={opcao} value={opcao}>
                {opcao}
              </option>
            ))}
          </select>
          {campo.ajuda && <small className="ajuda">{campo.ajuda}</small>}
        </label>
      );
    }

    return (
      <label key={campo.nome}>
        <span>
          {campo.rotulo}
          {campo.obrigatorio ? " *" : ""}
          {campo.unidade ? <em className="unidade"> ({campo.unidade})</em> : null}
        </span>
        <input
          type={campo.tipo === "data" ? "date" : "text"}
          inputMode={campo.tipo === "texto" ? undefined : "decimal"}
          value={String(valor ?? "")}
          required={campo.obrigatorio}
          onChange={(e) => setAtributos({ ...atributos, [campo.nome]: e.target.value })}
        />
        {campo.ajuda && <small className="ajuda">{campo.ajuda}</small>}
      </label>
    );
  };

  if (!esquema) return <div className="loading">Carregando classes de investimento...</div>;

  return (
    <section className="cadastro-section">
      <h2>Cadastrar posição</h2>
      <p className="muted">
        Os campos abaixo mudam com a classe: é o esquema do backend que define o que cada
        investimento precisa para ser controlado até a baixa.
      </p>

      {erro && <div className="error">Erro: {erro}</div>}
      {mensagem && <div className="sucesso">{mensagem}</div>}

      <form className="form-cadastro" onSubmit={cadastrarPosicao}>
        <label>
          <span>Classe do investimento *</span>
          <select value={classeNome} onChange={(e) => trocarClasse(e.target.value)}>
            {esquema.classes.map((item) => (
              <option key={item.nome} value={item.nome}>
                {item.rotulo}
              </option>
            ))}
          </select>
        </label>

        {classeAtual?.nota && <p className="nota-classe">{classeAtual.nota}</p>}

        <div className="form-grid">
          <label>
            <span>Ativo *</span>
            <input
              type="text"
              value={ativo}
              required
              placeholder="ex: BBAS3, CDB Banco A 2028, Fundo XYZ"
              onChange={(e) => setAtivo(e.target.value)}
            />
          </label>
          <label>
            <span>Instituição / corretora</span>
            <input type="text" value={instituicao} onChange={(e) => setInstituicao(e.target.value)} />
          </label>
          <label>
            <span>Quantidade</span>
            <input
              type="text"
              inputMode="decimal"
              value={quantidade}
              onChange={(e) => setQuantidade(e.target.value)}
            />
          </label>
          <label>
            <span>Preço médio / custo unitário</span>
            <input
              type="text"
              inputMode="decimal"
              value={precoMedio}
              onChange={(e) => setPrecoMedio(e.target.value)}
            />
          </label>
          <label>
            <span>Data de entrada</span>
            <input type="date" value={dataEntrada} onChange={(e) => setDataEntrada(e.target.value)} />
          </label>
        </div>

        <h3>Campos de {classeAtual?.rotulo ?? classeNome}</h3>
        <div className="form-grid">{(classeAtual?.campos ?? []).map(renderCampo)}</div>

        <button className="primary-btn" type="submit">
          Cadastrar posição
        </button>
      </form>

      <h2>Registrar evento</h2>
      <p className="muted">
        Aplicação, venda, resgate, amortização, provento, IR pago, taxa e encerramento — com os
        custos discriminados. O evento precisa existir para a classe da posição.
      </p>

      {posicoes.length === 0 ? (
        <p className="vazio">Nenhuma posição cadastrada ainda.</p>
      ) : (
        <form className="form-cadastro" onSubmit={registrarEvento}>
          <div className="form-grid">
            <label>
              <span>Posição *</span>
              <select
                value={posicaoId}
                required
                onChange={(e) => {
                  setPosicaoId(e.target.value);
                  const alvo = posicoes.find((item) => String(item.id) === e.target.value);
                  const classeAlvo = esquema.classes.find((item) => item.nome === alvo?.classe);
                  setEvento(classeAlvo?.eventos[0]?.nome ?? "aplicacao");
                }}
              >
                <option value="">selecione</option>
                {posicoes.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.ativo} — {item.classe} {item.status === "encerrada" ? "(encerrada)" : ""}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span>Evento *</span>
              <select value={evento} required onChange={(e) => setEvento(e.target.value)}>
                {(classeDaPosicao?.eventos ?? []).map((item) => (
                  <option key={item.nome} value={item.nome}>
                    {item.rotulo}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span>Data *</span>
              <input
                type="date"
                value={dataEvento}
                required
                onChange={(e) => setDataEvento(e.target.value)}
              />
            </label>
            <label>
              <span>Valor do evento (R$) *</span>
              <input
                type="text"
                inputMode="decimal"
                value={valorEvento}
                required
                onChange={(e) => setValorEvento(e.target.value)}
              />
            </label>
            <label>
              <span>Quantidade</span>
              <input
                type="text"
                inputMode="decimal"
                value={quantidadeEvento}
                onChange={(e) => setQuantidadeEvento(e.target.value)}
              />
            </label>
          </div>

          <h3>Custos e impostos (R$)</h3>
          <div className="form-grid">
            {esquema.custos.map((campo) => (
              <label key={campo.nome}>
                <span>{campo.rotulo}</span>
                <input
                  type="text"
                  inputMode="decimal"
                  value={custos[campo.nome] ?? ""}
                  onChange={(e) => setCustos({ ...custos, [campo.nome]: e.target.value })}
                />
              </label>
            ))}
          </div>

          <button className="primary-btn" type="submit">
            Registrar evento
          </button>
        </form>
      )}

      {resultado && (
        <div className="sucesso">
          Evento <strong>{resultado.evento}</strong> registrado — custo total {moeda(resultado.custo_total)}
          {" · "}efeito no caixa {moeda(resultado.valor_efeito)}.
        </div>
      )}
    </section>
  );
};
