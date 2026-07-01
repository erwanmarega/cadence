<script setup>
import { onMounted, ref, computed } from "vue";
import { useRouter } from "vue-router";
import { api } from "../lib/api";
import { useStrategiesStore } from "../stores/strategies";
import { useAuthStore } from "../stores/auth";
import Tooltip from "../components/Tooltip.vue";
import ConfirmModal from "../components/ConfirmModal.vue";
import LineChart from "../components/LineChart.vue";

const store = useStrategiesStore();
const auth = useAuthStore();
const router = useRouter();

const perf = ref(null);
const perfLoading = ref(false);
const history = ref(null);

const toDelete = ref(null);
const deleting = ref(false);

async function confirmDelete() {
  if (!toDelete.value) return;
  deleting.value = true;
  try {
    await store.remove(toDelete.value.id);
    toDelete.value = null;
  } finally {
    deleting.value = false;
  }
}

onMounted(async () => {
  store.load();
  perfLoading.value = true;
  try {
    perf.value = await api.portfolioSummary();
  } catch {
    perf.value = null;
  } finally {
    perfLoading.value = false;
  }
  try {
    history.value = await api.portfolioHistory();
  } catch {
    history.value = null;
  }
});

const hasStrategies = computed(() => store.items.length > 0);
const activeCount = computed(() => store.items.filter((s) => s.status === "active").length);
const hasPositions = computed(() => perf.value && perf.value.positions.length > 0);
const chartPoints = computed(() => history.value?.points || []);
const hasChart = computed(() => chartPoints.value.some((p) => p.value !== null && p.value !== undefined));
const plPositive = computed(() => (perf.value?.pl_total ?? 0) >= 0);

function fmtMoney(n, cur = "EUR") {
  if (n === null || n === undefined) return "—";
  return new Intl.NumberFormat("fr-FR", { style: "currency", currency: cur, maximumFractionDigits: 2 }).format(n);
}
function fmtNum(n) {
  return n === null || n === undefined ? "—" : new Intl.NumberFormat("fr-FR", { maximumFractionDigits: n < 1 ? 6 : 4 }).format(n);
}
function fmtInterval(i) {
  return { daily: "chaque jour", weekly: "chaque semaine", biweekly: "toutes les 2 semaines", monthly: "chaque mois" }[i] || i;
}
function fmtDate(d) {
  return d ? new Date(d).toLocaleDateString("fr-FR", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }) : "—";
}
function planTitle(s) {
  if (s.allocations?.length) return "Panier";
  return s.symbol?.split("/")[0] || s.symbol || "—";
}
function planDetail(s) {
  if (s.allocations?.length) return s.allocations.map((a) => `${a.base} ${a.weight}%`).join(" · ");
  return null;
}
</script>

<template>
  <div class="mx-auto max-w-5xl px-5 py-10">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="h-display text-3xl font-semibold">Ton portefeuille</h1>
        <p class="mt-1 text-muted">
          <span v-if="hasStrategies">{{ activeCount }} plan{{ activeCount > 1 ? "s" : "" }} actif{{ activeCount > 1 ? "s" : "" }} sur {{ store.items.length }}.</span>
          <span v-else>Aucun plan pour l'instant.</span>
        </p>
      </div>
      <button class="btn-primary" @click="router.push({ name: 'strategy-new' })">+ Nouveau plan</button>
    </div>

    <div v-if="hasPositions" class="card mt-6 bg-gradient-to-br from-surface to-brand-soft/30">
      <div class="grid gap-6 sm:grid-cols-3">
        <div>
          <p class="field-label">Valeur actuelle
            <Tooltip text="Ce que valent aujourd'hui toutes tes cryptos, au prix du marché." />
          </p>
          <p class="h-display text-3xl font-semibold">{{ fmtMoney(perf.current_value_total, perf.quote_currency) }}</p>
        </div>
        <div>
          <p class="field-label">Total investi</p>
          <p class="text-2xl font-medium text-ink-soft">{{ fmtMoney(perf.invested_total, perf.quote_currency) }}</p>
        </div>
        <div>
          <p class="field-label">Plus/moins-value
            <Tooltip text="Différence entre la valeur actuelle et ce que tu as investi. Peut être négative : la crypto monte et descend." />
          </p>
          <p class="text-2xl font-semibold" :class="plPositive ? 'text-brand' : 'text-danger'">
            {{ plPositive ? "+" : "" }}{{ fmtMoney(perf.pl_total, perf.quote_currency) }}
            <span v-if="perf.pl_pct_total !== null" class="text-base">
              ({{ plPositive ? "+" : "" }}{{ perf.pl_pct_total }}%)
            </span>
          </p>
        </div>
      </div>
    </div>

    <div v-if="hasChart" class="card mt-6">
      <h2 class="h-display text-xl font-semibold">Évolution
        <Tooltip text="La valeur de ton portefeuille jour après jour, comparée à ce que tu as investi. L'écart entre les deux courbes = ta plus ou moins-value." />
      </h2>
      <div class="mt-4">
        <LineChart :points="chartPoints" :quote="history.quote_currency" />
      </div>
    </div>

    <p v-if="auth.isBeginner && !hasPositions" class="mt-4 rounded-xl border border-line bg-paper-2/60 px-4 py-3 text-sm text-ink-soft">
      Chaque plan met un montant fixe en crypto, au rythme choisi — sans que tu
      aies à t'en occuper. C'est le principe du DCA : lisser le prix d'achat dans le temps.
    </p>

    <div v-if="hasPositions" class="mt-6">
      <h2 class="h-display text-xl font-semibold">Tes positions</h2>
      <div class="card mt-3 !p-0 overflow-hidden">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-line text-left text-xs uppercase tracking-wide text-muted">
              <th class="px-5 py-3 font-medium">Crypto</th>
              <th class="px-5 py-3 font-medium">Quantité</th>
              <th class="px-5 py-3 font-medium">
                Prix moyen
                <Tooltip text="Le prix moyen auquel tu as acheté, lissé sur tous tes achats. C'est le cœur du DCA." />
              </th>
              <th class="px-5 py-3 font-medium">Prix actuel</th>
              <th class="px-5 py-3 font-medium">Valeur</th>
              <th class="px-5 py-3 font-medium">+/-</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in perf.positions" :key="p.symbol" class="border-b border-line last:border-0">
              <td class="px-5 py-3 font-medium">{{ p.base }}</td>
              <td class="px-5 py-3">{{ fmtNum(p.quantity) }}</td>
              <td class="px-5 py-3">{{ fmtMoney(p.avg_price, p.quote_currency) }}</td>
              <td class="px-5 py-3">{{ fmtMoney(p.current_price, p.quote_currency) }}</td>
              <td class="px-5 py-3">{{ fmtMoney(p.current_value, p.quote_currency) }}</td>
              <td class="px-5 py-3 font-medium" :class="(p.pl ?? 0) >= 0 ? 'text-brand' : 'text-danger'">
                <span v-if="p.pl_pct !== null">{{ (p.pl ?? 0) >= 0 ? "+" : "" }}{{ p.pl_pct }}%</span>
                <span v-else class="text-muted">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="!store.loading && !hasStrategies" class="card mt-6 text-center">
      <div class="mx-auto max-w-md py-6">
        <div class="mx-auto mb-4 grid h-12 w-12 place-items-center rounded-full bg-brand-soft text-xl">🌱</div>
        <h3 class="h-display text-xl font-semibold">Lance ta première épargne</h3>
        <p v-if="auth.isBeginner" class="mt-2 text-sm text-muted">
          Connecte d'abord un compte d'échange (Kraken ou Coinbase), puis crée ton plan.
        </p>
        <div class="mt-6 flex justify-center gap-3">
          <button class="btn-secondary" @click="router.push({ name: 'exchanges' })">Connecter un compte</button>
          <button class="btn-primary" @click="router.push({ name: 'strategy-new' })">Créer un plan</button>
        </div>
      </div>
    </div>

    <div v-else-if="hasStrategies" class="mt-8">
      <h2 class="h-display text-xl font-semibold">Tes plans</h2>
      <div class="mt-3 grid gap-4 sm:grid-cols-2">
        <div v-for="s in store.items" :key="s.id" class="card flex flex-col gap-4"
             :class="s.status === 'error' ? 'border-danger/40' : ''">
          <div class="flex items-start justify-between">
            <div>
              <div class="flex items-center gap-2">
                <span class="h-display text-xl font-semibold">{{ planTitle(s) }}</span>
                <span class="badge" :class="{
                  'badge-active': s.status === 'active',
                  'badge-paused': s.status === 'paused',
                  'badge-failed': s.status === 'error',
                }">
                  <span class="h-1.5 w-1.5 rounded-full" :class="{
                    'bg-brand': s.status === 'active',
                    'bg-amber': s.status === 'paused',
                    'bg-danger': s.status === 'error',
                  }"></span>
                  {{ s.status === "active" ? "Actif" : s.status === "paused" ? "En pause" : "Erreur" }}
                </span>
              </div>
              <p class="mt-1 text-2xl font-semibold tracking-tight">
                {{ s.amount }} <span class="text-base font-normal text-muted">{{ s.quote_currency }}</span>
              </p>
              <p v-if="planDetail(s)" class="text-xs text-muted">{{ planDetail(s) }}</p>
              <p class="text-sm text-muted">{{ fmtInterval(s.interval) }}</p>
            </div>
          </div>

          <div v-if="s.status === 'error'" class="rounded-xl bg-danger-soft px-3 py-2 text-xs text-danger">
            <strong>Plan suspendu automatiquement</strong> après plusieurs échecs.
            <span v-if="s.last_error" class="block opacity-80">{{ s.last_error }}</span>
            <span class="block mt-1 text-danger/80">Vérifie ton solde / ta clé API, puis réactive.</span>
          </div>

          <div class="flex items-center justify-between border-t border-line pt-3">
            <p class="text-xs text-muted">
              Prochain achat · {{ fmtDate(s.next_run_at) }}
              <Tooltip text="Date du prochain achat automatique. Le bot achète au prix du marché à ce moment-là." />
            </p>
            <div class="flex gap-2">
              <button class="btn-secondary !px-3 !py-1.5 text-xs" @click="store.toggle(s)">
                {{ s.status === "active" ? "Suspendre" : "Réactiver" }}
              </button>
              <button class="btn-ghost !px-2 !py-1.5 text-xs text-danger hover:bg-danger-soft"
                      title="Supprimer le plan" @click="toDelete = s">Supprimer</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <ConfirmModal
      :open="!!toDelete"
      danger
      title="Supprimer ce plan ?"
      :message="toDelete ? `Le plan ${planTitle(toDelete)} (${toDelete.amount} ${toDelete.quote_currency}) sera supprimé définitivement. Ton historique d'achats reste consultable. Tes fonds ne sont pas touchés.` : ''"
      confirm-label="Supprimer"
      :busy="deleting"
      @update:open="(v) => { if (!v) toDelete = null; }"
      @confirm="confirmDelete"
    />
  </div>
</template>
