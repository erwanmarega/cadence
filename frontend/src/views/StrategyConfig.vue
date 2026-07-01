<script setup>
import { ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import { api } from "../lib/api";
import { useStrategiesStore } from "../stores/strategies";
import { useAuthStore } from "../stores/auth";
import { CURATED_BASES } from "../lib/assets";
import CryptoSelect from "../components/CryptoSelect.vue";
import Tooltip from "../components/Tooltip.vue";

const router = useRouter();
const store = useStrategiesStore();
const auth = useAuthStore();
const advanced = computed(() => !auth.isBeginner);

const connections = ref([]);
const form = ref({
  exchange_connection_id: "",
  base: "BTC",
  quote_currency: "EUR",
  amount: 20,
  interval: "weekly",
  basket: false,
  allocations: [
    { base: "BTC", weight: 60 },
    { base: "ETH", weight: 40 },
  ],
  run_time: "09:00",
  run_weekday: 0,
  run_day_of_month: 1,
});
const error = ref("");
const busy = ref(false);

const allBases = ref([]);
const showAll = ref(false);
const loadingBases = ref(false);
const coins = computed(() => (showAll.value && allBases.value.length ? allBases.value : CURATED_BASES));

const selectedExchange = computed(
  () => connections.value.find((c) => c.id === form.value.exchange_connection_id)?.exchange || "kraken",
);

async function loadAllBases() {
  showAll.value = true;
  loadingBases.value = true;
  try {
    allBases.value = (await api.marketBases(selectedExchange.value)).bases;
  } catch {
    showAll.value = false;
  } finally {
    loadingBases.value = false;
  }
}

const INTERVALS = [
  { value: "daily", label: "Chaque jour" },
  { value: "weekly", label: "Chaque semaine" },
  { value: "biweekly", label: "Toutes les 2 semaines" },
  { value: "monthly", label: "Chaque mois" },
];
const WEEKDAYS = [
  { v: 0, l: "Lundi" }, { v: 1, l: "Mardi" }, { v: 2, l: "Mercredi" },
  { v: 3, l: "Jeudi" }, { v: 4, l: "Vendredi" }, { v: 5, l: "Samedi" }, { v: 6, l: "Dimanche" },
];

const isWeekish = computed(() => ["weekly", "biweekly"].includes(form.value.interval));
const isMonthly = computed(() => form.value.interval === "monthly");
const symbol = computed(() => `${form.value.base}/${form.value.quote_currency}`);
const intervalLabel = computed(() => INTERVALS.find((i) => i.value === form.value.interval)?.label.toLowerCase());
const weightSum = computed(() => form.value.allocations.reduce((s, a) => s + Number(a.weight || 0), 0));

function addAlloc() {
  form.value.allocations.push({ base: "SOL", weight: 0 });
}
function removeAlloc(i) {
  form.value.allocations.splice(i, 1);
}

onMounted(async () => {
  try {
    connections.value = await api.listExchanges();
    if (connections.value.length) form.value.exchange_connection_id = connections.value[0].id;
  } catch (e) {
    error.value = e.message;
  }
});

async function submit() {
  error.value = "";
  if (!form.value.exchange_connection_id) {
    error.value = "Connecte d'abord un compte d'échange.";
    return;
  }
  const useBasket = advanced.value && form.value.basket;
  if (useBasket && Math.round(weightSum.value) !== 100) {
    error.value = `La somme des poids doit faire 100% (actuellement ${weightSum.value}%).`;
    return;
  }

  const [h, m] = form.value.run_time.split(":").map(Number);
  const payload = {
    exchange_connection_id: form.value.exchange_connection_id,
    amount: Number(form.value.amount),
    quote_currency: form.value.quote_currency,
    interval: form.value.interval,
    run_hour: h,
    run_minute: m,
    run_weekday: isWeekish.value ? form.value.run_weekday : null,
    run_day_of_month: isMonthly.value ? form.value.run_day_of_month : null,
  };
  if (useBasket) {
    payload.allocations = form.value.allocations.map((a) => ({ base: a.base, weight: Number(a.weight) }));
  } else {
    payload.symbol = symbol.value;
  }

  busy.value = true;
  try {
    await store.create(payload);
    router.push({ name: "dashboard" });
  } catch (e) {
    error.value = e.message;
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <div class="mx-auto max-w-xl px-5 py-10">
    <button class="btn-ghost mb-4 !px-0 hover:!bg-transparent" @click="router.back()">← Retour</button>
    <h1 class="h-display text-3xl font-semibold">Nouveau plan d'épargne</h1>

    <p v-if="auth.isBeginner" class="mt-3 rounded-xl border border-line bg-paper-2/60 px-4 py-3 text-sm text-ink-soft">
      Tu définis un montant et un rythme. À chaque échéance, on achète
      automatiquement la crypto choisie, peu importe le prix du jour.
    </p>

    <div v-if="!connections.length" class="card mt-6 text-center">
      <p class="text-muted">Aucun compte d'échange connecté.</p>
      <button class="btn-primary mt-4" @click="router.push({ name: 'exchanges' })">Connecter un compte</button>
    </div>

    <form v-else class="card mt-6 space-y-5" @submit.prevent="submit">
      <div>
        <label class="field-label">Compte d'échange</label>
        <select v-model="form.exchange_connection_id" class="field capitalize">
          <option v-for="c in connections" :key="c.id" :value="c.id">
            {{ c.exchange }} ••••{{ c.api_key_hint }}
          </option>
        </select>
      </div>

      <div v-if="advanced">
        <label class="field-label">Type de plan</label>
        <div class="grid grid-cols-2 gap-2">
          <button type="button" class="rounded-xl border px-3 py-2 text-sm transition"
                  :class="!form.basket ? 'border-brand bg-brand-soft/50 ring-1 ring-brand' : 'border-line-strong hover:border-ink/30'"
                  @click="form.basket = false">
            Une crypto
          </button>
          <button type="button" class="rounded-xl border px-3 py-2 text-sm transition"
                  :class="form.basket ? 'border-brand bg-brand-soft/50 ring-1 ring-brand' : 'border-line-strong hover:border-ink/30'"
                  @click="form.basket = true">
            Panier multi-crypto
          </button>
        </div>
      </div>

      <div v-if="!(advanced && form.basket)" class="grid grid-cols-2 gap-4">
        <div>
          <label class="field-label">Crypto <Tooltip text="La cryptomonnaie que le bot achètera à chaque échéance." /></label>
          <CryptoSelect v-model="form.base" :options="coins" />
          <button v-if="advanced && !showAll" type="button"
                  class="mt-1.5 text-xs text-brand hover:underline"
                  :disabled="loadingBases" @click="loadAllBases">
            {{ loadingBases ? "Chargement…" : "Voir toutes les cryptos" }}
          </button>
          <button v-else-if="advanced && showAll" type="button"
                  class="mt-1.5 text-xs text-muted hover:underline" @click="showAll = false">
            Revenir à la sélection principale
          </button>
        </div>
        <div>
          <label class="field-label">Devise</label>
          <select v-model="form.quote_currency" class="field">
            <option value="EUR">EUR</option>
            <option value="USD">USD</option>
          </select>
        </div>
      </div>

      <div v-else>
        <div class="flex items-center justify-between">
          <label class="field-label mb-0">Répartition du panier</label>
          <span class="text-xs" :class="Math.round(weightSum) === 100 ? 'text-brand' : 'text-danger'">
            Total : {{ weightSum }}%
          </span>
        </div>
        <div class="mt-2 space-y-2">
          <div v-for="(a, i) in form.allocations" :key="i" class="flex items-center gap-2">
            <div class="flex-1"><CryptoSelect v-model="a.base" :options="coins" /></div>
            <div class="flex w-24 items-center gap-1">
              <input v-model.number="a.weight" type="number" min="0" max="100" class="field !py-2" />
              <span class="text-sm text-muted">%</span>
            </div>
            <button type="button" class="text-muted hover:text-danger" :disabled="form.allocations.length <= 2"
                    @click="removeAlloc(i)">✕</button>
          </div>
        </div>
        <div class="mt-2 flex items-center justify-between">
          <button type="button" class="text-xs text-brand hover:underline" @click="addAlloc">+ Ajouter une crypto</button>
          <button v-if="advanced && !showAll" type="button" class="text-xs text-muted hover:underline"
                  :disabled="loadingBases" @click="loadAllBases">
            {{ loadingBases ? "Chargement…" : "Voir toutes les cryptos" }}
          </button>
        </div>
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="field-label">Montant / achat <Tooltip text="La somme dépensée à chaque échéance, répartie sur le panier le cas échéant." /></label>
          <input v-model="form.amount" type="number" min="1" step="1" class="field" />
        </div>
        <div>
          <label class="field-label">Rythme <Tooltip text="À quelle fréquence le bot achète. Plus c'est régulier, mieux le prix est lissé." /></label>
          <select v-model="form.interval" class="field">
            <option v-for="i in INTERVALS" :key="i.value" :value="i.value">{{ i.label }}</option>
          </select>
        </div>
      </div>

      <div v-if="advanced" class="grid grid-cols-2 gap-4">
        <div>
          <label class="field-label">Heure d'exécution <Tooltip text="Heure de Paris à laquelle l'achat est déclenché." /></label>
          <input v-model="form.run_time" type="time" class="field" />
        </div>
        <div v-if="isWeekish">
          <label class="field-label">Jour de la semaine</label>
          <select v-model.number="form.run_weekday" class="field">
            <option v-for="d in WEEKDAYS" :key="d.v" :value="d.v">{{ d.l }}</option>
          </select>
        </div>
        <div v-else-if="isMonthly">
          <label class="field-label">Jour du mois</label>
          <select v-model.number="form.run_day_of_month" class="field">
            <option v-for="d in 28" :key="d" :value="d">{{ d }}</option>
          </select>
        </div>
      </div>

      <div class="rounded-xl bg-brand-soft/50 px-4 py-3 text-sm text-brand-ink">
        Résumé · <strong>{{ form.amount }} {{ form.quote_currency }}</strong>
        <template v-if="advanced && form.basket">
          réparti sur
          <strong>{{ form.allocations.map(a => `${a.base} ${a.weight}%`).join(" · ") }}</strong>,
        </template>
        <template v-else>
          en <strong>{{ form.base }}</strong>,
        </template>
        {{ intervalLabel }}<span v-if="advanced"> à {{ form.run_time }}</span>.
      </div>

      <p class="text-xs text-muted">
        ⚠️ Investir comporte un risque de perte en capital. Le DCA lisse le prix
        d'achat mais ne garantit aucun rendement.
      </p>

      <p v-if="error" class="text-sm text-danger">{{ error }}</p>
      <div class="flex gap-3">
        <button type="submit" class="btn-primary flex-1" :disabled="busy">Créer le plan</button>
        <button type="button" class="btn-ghost" @click="router.back()">Annuler</button>
      </div>
    </form>
  </div>
</template>
