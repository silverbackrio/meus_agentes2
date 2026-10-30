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
};
