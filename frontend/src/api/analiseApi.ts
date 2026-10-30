import axios from "axios";
import type { AxiosResponse } from "axios";

const API_BASE = import.meta.env.VITE_API_BASE || "/api/v1";

export interface SimulacaoInput {
  quantidade_atual: number;
  preco_medio_atual: number;
  quantidade_nova: number;
  preco_nova_compra: number;
  proventos_12m_por_acao?: number;
  jcp_anual_por_acao?: number;
  preco_atual_tela?: number;
}

export interface SimulacaoResultado {
  preco_medio_novo: number;
  quantidade_total: number;
  custo_novo_total: number;
  pnl: number;
  pnl_pct: number;
  yield_on_cost_novo: number;
  projecao_renda_passiva: number;
  jcp_anual_por_acao: number;
}

export interface SimulacaoError {
  campo: string;
  mensagem: string;
  sugestao: string;
}

const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
  withCredentials: false,
});

export const analiseApi = {
  async simular(payload: SimulacaoInput): Promise<AxiosResponse<SimulacaoResultado, SimulacaoError>> {
    return api.post("/analise/simular/", payload);
  },

  async listMetricas() {
    return api.get("/analise/metricas/");
  },

  async listCenarios() {
    return api.get("/analise/cenarios/");
  },

  async listDossies() {
    return api.get("/analise/dossies/");
  },

  async comparar(ativos: string, base: string = "liquida", valor?: number) {
    const params = new URLSearchParams({
      ativos,
      base,
    });
    if (valor !== undefined) {
      params.append("valor", String(valor));
    }
    return api.get(`/comparar/?${params.toString()}`);
  },

  async dossieDetail(data: string) {
    return api.get(`/dossies/${data}/`);
  },

  async listSeries() {
    return api.get("/series/");
  },

  async serieObservacoes(id: number) {
    return api.get(`/series/${id}/observacoes/`);
  },

  async dadosStatus() {
    return api.get("/dados/status/");
  },

  async listPosicoes() {
    return api.get("/carteira/");
  },

  async carteiraResumo() {
    return api.get("/carteira/resumo/");
  },

  async carteiraClasses() {
    return api.get("/carteira/classes/");
  },

  async criarPosicao(payload: Record<string, unknown>) {
    return api.post("/carteira/posicoes/", payload);
  },

  async criarOperacao(payload: Record<string, unknown>) {
    return api.post("/carteira/operacoes/", payload);
  },

  async listDocumentos() {
    return api.get("/documentos/");
  },

  async enviarDocumento(payload: Record<string, unknown> | FormData) {
    // OCR de página inteira passa dos 10s do timeout padrão.
    return api.post("/documentos/", payload, { timeout: 180000 });
  },

  async diagnosticarDocumento(payload: Record<string, unknown> | FormData) {
    return api.post("/documentos/diagnostico/", payload, { timeout: 60000 });
  },

  async promoverDocumento(id: number) {
    return api.post(`/documentos/${id}/promover/`);
  },
};
