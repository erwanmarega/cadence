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

const connections = ref([]);
const form = ref({
  exchange_connection_id: "",
  base: "BTC",
  quote_currency: "EUR",
  amount: 20,
  interval: "weekly",
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

const symbol = computed(() => `${form.value.base}/${form.value.quote_currency}`);
const intervalLabel = computed(() => INTERVALS.find((i) => i.value === form.value.interval)?.label.toLowerCase());

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
  busy.value = true;
  try {
    await store.create({
      exchange_connection_id: form.value.exchange_connection_id,
      symbol: symbol.value,
      amount: Number(form.value.amount),
      quote_currency: form.value.quote_currency,
      interval: form.value.interval,
    });
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

      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="field-label">Crypto <Tooltip text="La cryptomonnaie que le bot achètera à chaque échéance." /></label>
          <CryptoSelect v-model="form.base" :options="coins" />
          <button v-if="!auth.isBeginner && !showAll" type="button"
                  class="mt-1.5 text-xs text-brand hover:underline"
                  :disabled="loadingBases" @click="loadAllBases">
            {{ loadingBases ? "Chargement…" : "Voir toutes les cryptos" }}
          </button>
          <button v-else-if="!auth.isBeginner && showAll" type="button"
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

      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="field-label">Montant / achat <Tooltip text="La somme dépensée à chaque échéance." /></label>
          <input v-model="form.amount" type="number" min="1" step="1" class="field" />
        </div>
        <div>
          <label class="field-label">Rythme <Tooltip text="À quelle fréquence le bot achète. Plus c'est régulier, mieux le prix est lissé." /></label>
          <select v-model="form.interval" class="field">
            <option v-for="i in INTERVALS" :key="i.value" :value="i.value">{{ i.label }}</option>
          </select>
        </div>
      </div>

      <div class="rounded-xl bg-brand-soft/50 px-4 py-3 text-sm text-brand-ink">
        Résumé · <strong>{{ form.amount }} {{ form.quote_currency }}</strong> en
        <strong>{{ form.base }}</strong>, {{ intervalLabel }}.
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
