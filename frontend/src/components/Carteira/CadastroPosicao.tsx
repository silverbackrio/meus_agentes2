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

interface ErroValidacao {
  campo: string;
  mensagem: string;
  sugestao: string;
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
  const [errosCampo, setErrosCampo] = React.useState<Record<string, string>>({});

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

  const focar = (campo: string) => {
    const elemento = document.getElementById(campo);
    if (elemento) {
      elemento.scrollIntoView({ behavior: "smooth", block: "center" });
      (elemento as HTMLInputElement).focus();
    }
  };

  /** Aplica a resposta 422 do backend: mostra TODOS os campos reclamados, por nome. */
  const aplicarErrosDoServidor = (corpo: any) => {
    const lista: ErroValidacao[] = Array.isArray(corpo?.erros) ? corpo.erros : [];
    if (lista.length === 0) {
      setErro(`${corpo?.erro ?? "Entrada inválida"} ${corpo?.sugestao ? `— ${corpo.sugestao}` : ""}`.trim());
      return;
    }
    const mapa: Record<string, string> = {};
    for (const item of lista) mapa[item.campo] = item.mensagem;
    setErrosCampo(mapa);
    const nomes = lista.map((item) => `${item.campo} (${item.mensagem})`).join(" · ");
    setErro(`Falta preencher ou corrigir: ${nomes}`);
    focar(lista[0].campo);
  };

  const trocarClasse = (nome: string) => {
    setClasseNome(nome);
    setAtributos({});
    setErrosCampo({});
    setMensagem(null);
    setErro(null);
  };

  const obrigatoriosFaltando = () => {
    const faltas: { campo: string; rotulo: string }[] = [];
    if (!ativo.trim()) faltas.push({ campo: "ativo", rotulo: "Ativo" });
    for (const campo of classeAtual?.campos ?? []) {
      if (!campo.obrigatorio || campo.tipo === "booleano") continue;
      const valor = atributos[campo.nome];
      if (valor === undefined || String(valor).trim() === "") {
        faltas.push({ campo: campo.nome, rotulo: campo.rotulo });
      }
    }
    return faltas;
  };

  const cadastrarPosicao = (eventoForm: React.FormEvent) => {
    eventoForm.preventDefault();
    setErro(null);
    setMensagem(null);
    setErrosCampo({});

    // Validação local: diz exatamente qual campo falta, antes de chamar a API.
    const faltas = obrigatoriosFaltando();
    if (faltas.length > 0) {
      setErrosCampo(Object.fromEntries(faltas.map((item) => [item.campo, "Preencha este campo"])));
      setErro(`Faltou preencher: ${faltas.map((item) => item.rotulo).join(", ")}.`);
      focar(faltas[0].campo);
      return;
    }

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
      .catch((e) => aplicarErrosDoServidor(e?.response?.data));
  };

  const registrarEvento = (eventoForm: React.FormEvent) => {
    eventoForm.preventDefault();
    setErro(null);
    setMensagem(null);
    setErrosCampo({});
    setResultado(null);

    const faltas: { campo: string; rotulo: string }[] = [];
    if (!posicaoId) faltas.push({ campo: "posicao", rotulo: "Posição" });
    if (!dataEvento) faltas.push({ campo: "data_evento", rotulo: "Data do evento" });
    if (!valorEvento.trim()) faltas.push({ campo: "valor_evento", rotulo: "Valor do evento" });
    if (faltas.length > 0) {
      setErrosCampo(Object.fromEntries(faltas.map((item) => [item.campo, "Preencha este campo"])));
      setErro(`Faltou preencher: ${faltas.map((item) => item.rotulo).join(", ")}.`);
      focar(faltas[0].campo);
      return;
    }

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
      .catch((e) => aplicarErrosDoServidor(e?.response?.data));
  };

  const invalido = (campo: string) => (errosCampo[campo] ? "invalido" : undefined);

  const mensagemCampo = (campo: string) =>
    errosCampo[campo] ? <small className="erro-campo">{errosCampo[campo]}</small> : null;

  const renderCampo = (campo: CampoSchema) => {
    const valor = atributos[campo.nome];

    if (campo.tipo === "booleano") {
      return (
        <label className="campo-check" key={campo.nome} htmlFor={campo.nome}>
          <input
            id={campo.nome}
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
        <label key={campo.nome} htmlFor={campo.nome}>
          <span>
            {campo.rotulo}
            {campo.obrigatorio ? " *" : ""}
          </span>
          <select
            id={campo.nome}
            className={invalido(campo.nome)}
            value={String(valor ?? "")}
            onChange={(e) => setAtributos({ ...atributos, [campo.nome]: e.target.value })}
          >
            <option value="">selecione</option>
            {campo.opcoes.map((opcao) => (
              <option key={opcao} value={opcao}>
                {opcao}
              </option>
            ))}
          </select>
          {mensagemCampo(campo.nome)}
          {campo.ajuda && <small className="ajuda">{campo.ajuda}</small>}
        </label>
      );
    }

    return (
      <label key={campo.nome} htmlFor={campo.nome}>
        <span>
          {campo.rotulo}
          {campo.obrigatorio ? " *" : ""}
          {campo.unidade ? <em className="unidade"> ({campo.unidade})</em> : null}
        </span>
        <input
          id={campo.nome}
          className={invalido(campo.nome)}
          type={campo.tipo === "data" ? "date" : "text"}
          inputMode={campo.tipo === "texto" ? undefined : "decimal"}
          value={String(valor ?? "")}
          onChange={(e) => setAtributos({ ...atributos, [campo.nome]: e.target.value })}
        />
        {mensagemCampo(campo.nome)}
        {campo.ajuda && <small className="ajuda">{campo.ajuda}</small>}
      </label>
    );
  };

  if (!esquema) return <div className="loading">Carregando classes de investimento...</div>;

  return (
    <section className="cadastro-section">
      <h2>Cadastrar posição</h2>
      <p className="muted">
        Os campos mudam com a classe — é o esquema do backend que define o que cada investimento
        precisa para ser controlado até a baixa. Os campos com <strong>*</strong> são obrigatórios.
      </p>

      {erro && <div className="error">Erro: {erro}</div>}
      {mensagem && <div className="sucesso">{mensagem}</div>}

      <form className="form-cadastro" onSubmit={cadastrarPosicao} noValidate>
        <label htmlFor="classe">
          <span>Classe do investimento *</span>
          <select id="classe" value={classeNome} onChange={(e) => trocarClasse(e.target.value)}>
            {esquema.classes.map((item) => (
              <option key={item.nome} value={item.nome}>
                {item.rotulo}
              </option>
            ))}
          </select>
        </label>

        {classeAtual?.nota && <p className="nota-classe">{classeAtual.nota}</p>}

        <div className="form-grid">
          <label htmlFor="ativo">
            <span>Ativo *</span>
            <input
              id="ativo"
              className={invalido("ativo")}
              type="text"
              value={ativo}
              placeholder="ex: BBAS3, CDB Banco A 2028, Fundo XYZ"
              onChange={(e) => setAtivo(e.target.value)}
            />
            {mensagemCampo("ativo")}
          </label>
          <label htmlFor="instituicao">
            <span>Instituição / corretora</span>
            <input
              id="instituicao"
              type="text"
              value={instituicao}
              onChange={(e) => setInstituicao(e.target.value)}
            />
          </label>
          <label htmlFor="quantidade">
            <span>Quantidade</span>
            <input
              id="quantidade"
              className={invalido("quantidade")}
              type="text"
              inputMode="decimal"
              value={quantidade}
              placeholder="ex: 100 ou 1.000,50"
              onChange={(e) => setQuantidade(e.target.value)}
            />
            {mensagemCampo("quantidade")}
          </label>
          <label htmlFor="preco_medio">
            <span>Preço médio / custo unitário</span>
            <input
              id="preco_medio"
              className={invalido("preco_medio")}
              type="text"
              inputMode="decimal"
              value={precoMedio}
              placeholder="ex: 32,50"
              onChange={(e) => setPrecoMedio(e.target.value)}
            />
            {mensagemCampo("preco_medio")}
          </label>
          <label htmlFor="data_entrada">
            <span>Data de entrada</span>
            <input id="data_entrada" type="date" value={dataEntrada} onChange={(e) => setDataEntrada(e.target.value)} />
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
        <form className="form-cadastro" onSubmit={registrarEvento} noValidate>
          <div className="form-grid">
            <label htmlFor="posicao">
              <span>Posição *</span>
              <select
                id="posicao"
                className={invalido("posicao")}
                value={posicaoId}
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
              {mensagemCampo("posicao")}
            </label>
            <label htmlFor="evento">
              <span>Evento *</span>
              <select id="evento" value={evento} onChange={(e) => setEvento(e.target.value)}>
                {(classeDaPosicao?.eventos ?? []).map((item) => (
                  <option key={item.nome} value={item.nome}>
                    {item.rotulo}
                  </option>
                ))}
              </select>
            </label>
            <label htmlFor="data_evento">
              <span>Data *</span>
              <input
                id="data_evento"
                className={invalido("data_evento")}
                type="date"
                value={dataEvento}
                onChange={(e) => setDataEvento(e.target.value)}
              />
              {mensagemCampo("data_evento")}
            </label>
            <label htmlFor="valor_evento">
              <span>Valor do evento (R$) *</span>
              <input
                id="valor_evento"
                className={invalido("valor_evento")}
                type="text"
                inputMode="decimal"
                value={valorEvento}
                onChange={(e) => setValorEvento(e.target.value)}
              />
              {mensagemCampo("valor_evento")}
            </label>
            <label htmlFor="quantidade_evento">
              <span>Quantidade</span>
              <input
                id="quantidade_evento"
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
              <label key={campo.nome} htmlFor={`custo_${campo.nome}`}>
                <span>{campo.rotulo}</span>
                <input
                  id={`custo_${campo.nome}`}
                  className={invalido(campo.nome)}
                  type="text"
                  inputMode="decimal"
                  value={custos[campo.nome] ?? ""}
                  onChange={(e) => setCustos({ ...custos, [campo.nome]: e.target.value })}
                />
                {mensagemCampo(campo.nome)}
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
