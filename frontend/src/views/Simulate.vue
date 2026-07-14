<script setup>

import { ref, computed } from "vue";
import { useRouter } from "vue-router";
import { api } from "../lib/api";
import LineChart from "../components/LineChart.vue";
import Spinner from "../components/Spinner.vue";

const router = useRouter();

const COINS = ["BTC", "ETH", "SOL", "ADA", "DOT", "XRP", "LTC"];
const INTERVALS = [
  { value: "daily", label: "chaque jour" },
  { value: "weekly", label: "chaque semaine" },
  { value: "biweekly", label: "toutes les 2 semaines" },
  { value: "monthly", label: "chaque mois" },
];
const PERIODS = [
  { label: "1 an", years: 1 },
  { label: "2 ans", years: 2 },
  { label: "3 ans", years: 3 },
  { label: "5 ans", years: 5 },
];

function startFor(years) {
  const d = new Date();
  d.setFullYear(d.getFullYear() - years);
  return d.toISOString().slice(0, 10);
}


const comparison = [
  { label: "Plusieurs exchanges au même endroit", exchange: "Un seul à la fois", cadence: "Vue unifiée Kraken + Coinbase" },
  { label: "Prix d'achat moyen lissé", exchange: "Rarement affiché", cadence: "Suivi clair, au cœur de l'app" },
  { label: "Objectifs d'épargne", exchange: "Non", cadence: "Cap + progression motivante" },
  { label: "Accompagnement débutant", exchange: "Interface de trader", cadence: "Mode guidé, vocabulaire simple" },
  { label: "Simulation avant de se lancer", exchange: "Non", cadence: "Oui, sans compte" },
  { label: "Export fiscal (plus-values)", exchange: "Non", cadence: "Relevé annuel + prix de revient" },
];

const form = ref({ base: "BTC", amount: 20, interval: "weekly", years: 3 });
const result = ref(null);
const loading = ref(false);
const error = ref("");

const positive = computed(() => (result.value?.pl ?? 0) >= 0);

async function run() {
  error.value = "";
  loading.value = true;
  result.value = null;
  try {
    result.value = await api.simulate({
      base: form.value.base,
      amount: form.value.amount,
      interval: form.value.interval,
      start: startFor(form.value.years),
      quote: "EUR",
    });
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

function fmt(n) {
  if (n == null) return "—";
  return new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(n);
}
</script>

<template>
  <div class="min-h-screen bg-paper">

    <header class="border-b border-line">
      <div class="mx-auto flex max-w-3xl items-center justify-between px-5 py-4">
        <RouterLink to="/login" class="flex items-center gap-2">
          <span class="grid h-7 w-7 place-items-center rounded-lg bg-brand text-sm font-bold text-white">C</span>
          <span class="h-display text-xl font-semibold">Cadence</span>
        </RouterLink>
        <RouterLink to="/login" class="btn-ghost">Se connecter</RouterLink>
      </div>
    </header>

    <div class="mx-auto max-w-3xl px-5 py-10">
      <h1 class="h-display text-4xl font-semibold leading-tight">
        Et si tu avais épargné en crypto&nbsp;?
      </h1>
      <p class="mt-2 text-muted">
        Teste une stratégie DCA sur les vrais prix passés. Sans inscription, sans risque.
      </p>


      <div class="card mt-8">
        <div class="grid gap-4 sm:grid-cols-2">
          <div>
            <label class="field-label">Montant par achat</label>
            <input v-model="form.amount" type="number" min="1" class="field" />
          </div>
          <div>
            <label class="field-label">Crypto</label>
            <select v-model="form.base" class="field">
              <option v-for="c in COINS" :key="c" :value="c">{{ c }}</option>
            </select>
          </div>
          <div>
            <label class="field-label">Fréquence</label>
            <select v-model="form.interval" class="field">
              <option v-for="i in INTERVALS" :key="i.value" :value="i.value">{{ i.label }}</option>
            </select>
          </div>
          <div>
            <label class="field-label">Période</label>
            <select v-model="form.years" class="field">
              <option v-for="p in PERIODS" :key="p.years" :value="p.years">{{ p.label }}</option>
            </select>
          </div>
        </div>
        <button class="btn-primary mt-5 flex w-full items-center justify-center gap-2" :disabled="loading" @click="run">
          <Spinner v-if="loading" size="1rem" />
          {{ loading ? "Calcul en cours…" : "Voir le résultat" }}
        </button>
        <p v-if="error" class="mt-3 text-sm text-danger">{{ error }}</p>
      </div>


      <section v-if="!result" class="mt-12">
        <h2 class="h-display text-2xl font-semibold">Pourquoi pas juste l'achat récurrent de mon exchange&nbsp;?</h2>
        <p class="mt-1 text-muted">Kraken ou Coinbase le proposent. Voici ce que Cadence apporte en plus.</p>

        <div class="mt-5 overflow-hidden rounded-xl2 border border-line">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-line bg-paper-2/50 text-left">
                <th class="px-4 py-3 font-medium"></th>
                <th class="px-4 py-3 font-medium text-muted">Exchange seul</th>
                <th class="px-4 py-3 font-medium text-brand-ink">Cadence</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in comparison" :key="row.label" class="border-b border-line last:border-0">
                <td class="px-4 py-3">{{ row.label }}</td>
                <td class="px-4 py-3 text-muted">{{ row.exchange }}</td>
                <td class="px-4 py-3">
                  <span class="font-medium text-brand-ink">{{ row.cadence }}</span>
                  <span v-if="row.soon" class="ml-1 rounded bg-amber-soft px-1.5 py-0.5 text-[10px] font-medium text-amber">bientôt</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p class="mt-3 text-xs text-muted">
          Cadence reste non-custodial : tes fonds restent sur ton exchange. On orchestre, on ne détient rien.
        </p>
      </section>

      <div v-if="result" class="mt-8">
        <p class="text-muted">
          {{ fmt(result.amount) }} en {{ result.base }} {{ INTERVALS.find(i => i.value === result.interval)?.label }},
          pendant {{ form.years }} an{{ form.years > 1 ? "s" : "" }} ({{ result.buys }} achats) :
        </p>

        <div class="card mt-3 bg-linear-to-br from-surface to-brand-soft/30">
          <div class="grid gap-6 sm:grid-cols-3">
            <div>
              <p class="field-label">Tu aurais investi</p>
              <p class="text-2xl font-medium text-ink-soft">{{ fmt(result.invested) }}</p>
            </div>
            <div>
              <p class="field-label">Ça vaudrait</p>
              <p class="h-display text-3xl font-semibold">{{ fmt(result.current_value) }}</p>
            </div>
            <div>
              <p class="field-label">Résultat</p>
              <p class="text-2xl font-semibold" :class="positive ? 'text-brand' : 'text-danger'">
                {{ positive ? "+" : "" }}{{ fmt(result.pl) }}
                <span class="text-base">({{ positive ? "+" : "" }}{{ result.pl_pct }}%)</span>
              </p>
            </div>
          </div>
          <p class="mt-4 border-t border-line pt-3 text-sm text-muted">
            Prix d'achat moyen : <strong class="text-ink">{{ fmt(result.avg_price) }}</strong>
            · Prix actuel : {{ fmt(result.current_price) }}
          </p>
        </div>

        <div class="card mt-4">
          <LineChart :points="result.points" quote="EUR" />
        </div>


        <div class="mt-6 rounded-xl2 bg-brand p-6 text-center text-white">
          <h3 class="h-display text-2xl font-semibold">Lance ton épargne pour de vrai</h3>
          <p class="mt-1 text-white/80">Automatique, sur ton compte, en quelques minutes.</p>
          <button class="btn mt-4 bg-white text-brand hover:bg-white/90" @click="router.push({ name: 'login' })">
            Créer mon compte
          </button>
        </div>

        <p class="mt-6 text-center text-xs text-muted">
          ⚠️ Simulation sur données passées. Les performances passées ne préjugent pas des
          performances futures. Investir comporte un risque de perte en capital.
        </p>
      </div>
    </div>
  </div>
</template>
