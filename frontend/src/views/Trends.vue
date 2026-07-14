<script setup>
import { ref, onMounted, computed } from "vue";
import { api } from "../lib/api";
import { useAuthStore } from "../stores/auth";
import Tooltip from "../components/Tooltip.vue";
import Spinner from "../components/Spinner.vue";

const auth = useAuthStore();
const coins = ref([]);
const updatedAt = ref(null);
const loading = ref(false);
const error = ref("");

async function load() {
  loading.value = true;
  error.value = "";
  try {
    const data = await api.trends();
    coins.value = data.coins;
    updatedAt.value = data.updated_at;
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}
onMounted(load);

const gainers = computed(() => coins.value.filter((c) => c.change_24h >= 0));
const losers = computed(() => coins.value.filter((c) => c.change_24h < 0));

function fmtPrice(n) {
  return new Intl.NumberFormat("fr-FR", { maximumFractionDigits: n < 1 ? 6 : 2 }).format(n);
}
function fmtTime(d) {
  return d ? new Date(d).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" }) : "";
}
</script>

<template>
  <div class="mx-auto max-w-5xl px-5 py-10">
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 class="h-display text-3xl font-semibold">Tendances du marché</h1>
        <p class="mt-1 text-muted">
          Variation des prix sur 24h
          <Tooltip text="La crypto est très volatile : les prix montent et descendent fortement et rapidement. Ces chiffres décrivent le passé récent, ils ne prédisent rien." />
          <span v-if="updatedAt" class="text-sm"> · maj {{ fmtTime(updatedAt) }}</span>
        </p>
      </div>
      <button class="btn-secondary flex items-center gap-2" :disabled="loading" @click="load">
        <Spinner v-if="loading" size="1rem" />
        {{ loading ? "Actualisation…" : "Actualiser" }}
      </button>
    </div>


    <div class="mt-5 rounded-xl2 border border-line bg-paper-2/60 px-5 py-4 text-sm text-ink-soft">
      <strong>ℹ️ Information, pas conseil.</strong>
      Cadence te montre ce qui se passe sur le marché, jamais ce que tu devrais
      faire. Ces données ne sont pas une recommandation d'achat ou de vente. Ta
      stratégie d'épargne reste régulière, quel que soit le prix — c'est tout
      l'intérêt du DCA.
    </div>

    <p v-if="error" class="mt-6 text-danger">{{ error }}</p>

    <div v-else-if="loading && !gainers.length && !losers.length" class="mt-10 flex flex-col items-center gap-3 text-muted">
      <Spinner size="2rem" />
      <span class="text-sm">Chargement des tendances…</span>
    </div>

    <div v-else class="mt-6 grid gap-5 md:grid-cols-2">

      <section class="card p-0 overflow-hidden">
        <header class="flex items-center gap-2 border-b border-line px-5 py-3">
          <span class="badge badge-success">En hausse</span>
          <span class="text-sm text-muted">{{ gainers.length }} sur 24h</span>
        </header>
        <ul>
          <li v-for="c in gainers" :key="c.symbol"
              class="flex items-center justify-between border-b border-line px-5 py-3 last:border-0">
            <div class="flex items-center gap-3">
              <span class="grid h-8 w-8 place-items-center rounded-full bg-paper-2 text-xs font-semibold">{{ c.base }}</span>
              <span class="font-medium">{{ c.symbol }}</span>
            </div>
            <div class="text-right">
              <div class="font-medium">{{ fmtPrice(c.last) }} €</div>
              <div class="text-sm font-medium text-brand">▲ {{ c.change_24h }}%</div>
            </div>
          </li>
          <li v-if="!gainers.length && !loading" class="px-5 py-6 text-center text-sm text-muted">
            Aucune crypto en hausse sur 24h.
          </li>
        </ul>
      </section>


      <section class="card p-0 overflow-hidden">
        <header class="flex items-center gap-2 border-b border-line px-5 py-3">
          <span class="badge badge-failed">En baisse</span>
          <span class="text-sm text-muted">{{ losers.length }} sur 24h</span>
        </header>
        <ul>
          <li v-for="c in losers" :key="c.symbol"
              class="flex items-center justify-between border-b border-line px-5 py-3 last:border-0">
            <div class="flex items-center gap-3">
              <span class="grid h-8 w-8 place-items-center rounded-full bg-paper-2 text-xs font-semibold">{{ c.base }}</span>
              <span class="font-medium">{{ c.symbol }}</span>
            </div>
            <div class="text-right">
              <div class="font-medium">{{ fmtPrice(c.last) }} €</div>
              <div class="text-sm font-medium text-danger">▼ {{ c.change_24h }}%</div>
            </div>
          </li>
          <li v-if="!losers.length && !loading" class="px-5 py-6 text-center text-sm text-muted">
            Aucune crypto en baisse sur 24h.
          </li>
        </ul>
      </section>
    </div>
  </div>
</template>
