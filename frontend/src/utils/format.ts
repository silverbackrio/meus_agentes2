import { Decimal } from "decimal.js";

export const decimalParaMoeda = (valor: number | string | Decimal, moeda: string = "BRL"): string => {
  const d = typeof valor === "number" ? new Decimal(valor) : new Decimal(valor);
  return d.toFormat(2, { locale: { decimal: ".", group: "," } }) + " " + moeda;
};

export const decimalParaPorcentagem = (valor: number | string | Decimal, casas: number = 2): string => {
  const d = typeof valor === "number" ? new Decimal(valor) : new Decimal(valor);
  return d.times(100).toFormat(casas, { locale: { decimal: ".", group: "," } }) + " %";
};
