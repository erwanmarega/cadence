<script setup>
import { ref, computed, onMounted } from "vue";
import { api } from "../lib/api";
import { useAuthStore } from "../stores/auth";
import { CURATED_BASES } from "../lib/assets";
import CryptoSelect from "../components/CryptoSelect.vue";
import ConfirmModal from "../components/ConfirmModal.vue";

const auth = useAuthStore();
const goals = ref([]);
const loading = ref(false);
const error = ref("");

const showForm = ref(false);
const form = ref({ base: "BTC", target_amount: 1000, quote_currency: "EUR", title: "" });
const saving = ref(false);

const toDelete = ref(null);
const deleting = ref(false);

const allBases = ref([]);
const showAll = ref(false);
const loadingBases = ref(false);
const coins = computed(() => (showAll.value && allBases.value.length ? allBases.value : CURATED_BASES));

async function loadAllBases() {
  showAll.value = true;
  if (allBases.value.length) return;
  loadingBases.value = true;
  try {
    allBases.value = (await api.marketBases()).bases;
  } catch {
    showAll.value = false;
  } finally {
    loadingBases.value = false;
  }
}

async function load() {
  loading.value = true;
  try {
    goals.value = await api.listGoals();
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}
onMounted(load);

async function create() {
  error.value = "";
  saving.value = true;
  try {
    await api.createGoal({
      base: form.value.base,
      target_amount: Number(form.value.target_amount),
      quote_currency: form.value.quote_currency,
      title: form.value.title || null,
    });
    showForm.value = false;
    form.value = { base: "BTC", target_amount: 1000, quote_currency: "EUR", title: "" };
    await load();
  } catch (e) {
    error.value = e.message;
  } finally {
    saving.value = false;
  }
}

async function confirmDelete() {
  if (!toDelete.value) return;
  deleting.value = true;
  try {
    await api.deleteGoal(toDelete.value.id);
    toDelete.value = null;
    await load();
  } finally {
    deleting.value = false;
  }
}

function fmtMoney(n, cur = "EUR") {
  return new Intl.NumberFormat("fr-FR", { style: "currency", currency: cur, maximumFractionDigits: 0 }).format(n);
}
</script>

<template>
  <div class="mx-auto max-w-3xl px-5 py-10">
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 class="h-display text-3xl font-semibold">Tes objectifs</h1>
        <p class="mt-1 text-muted">Fixe un cap, suis ta progression.</p>
      </div>
      <button class="btn-primary" @click="showForm = !showForm">+ Nouvel objectif</button>
    </div>

    <p v-if="auth.isBeginner" class="mt-4 rounded-xl border border-line bg-paper-2/60 px-4 py-3 text-sm text-ink-soft">
      Un objectif, c'est juste un repère motivant : "atteindre 1000€ en Bitcoin".
      Ça ne change rien à tes achats automatiques, ça t'aide à visualiser le chemin parcouru.
    </p>


    <form v-if="showForm" class="card mt-5 space-y-4" @submit.prevent="create">
      <div>
        <label class="field-label">Nom (optionnel)</label>
        <input v-model="form.title" class="field" placeholder="Ex : Mon épargne BTC" />
      </div>
      <div class="grid grid-cols-3 gap-4">
        <div>
          <label class="field-label">Crypto</label>
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
        <div class="col-span-2">
          <label class="field-label">Objectif (montant)</label>
          <input v-model="form.target_amount" type="number" min="1" class="field" />
        </div>
      </div>
      <p v-if="error" class="text-sm text-danger">{{ error }}</p>
      <div class="flex gap-3">
        <button type="submit" class="btn-primary" :disabled="saving">Créer l'objectif</button>
        <button type="button" class="btn-ghost" @click="showForm = false">Annuler</button>
      </div>
    </form>

    <div v-if="!loading && !goals.length && !showForm" class="card mt-6 text-center">
      <div class="mx-auto max-w-md py-6">
        <div class="mx-auto mb-4 grid h-12 w-12 place-items-center rounded-full bg-brand-soft text-xl">🎯</div>
        <h3 class="h-display text-xl font-semibold">Aucun objectif</h3>
        <p class="mt-2 text-sm text-muted">Fixe un premier cap pour rester motivé.</p>
        <button class="btn-primary mt-5" @click="showForm = true">Créer un objectif</button>
      </div>
    </div>

    <div v-else class="mt-6 space-y-4">
      <div v-for="g in goals" :key="g.id" class="card">
        <div class="flex items-start justify-between">
          <div>
            <h3 class="h-display text-lg font-semibold">{{ g.title || `Objectif ${g.base}` }}</h3>
            <p class="text-sm text-muted">
              {{ fmtMoney(g.current_value, g.quote_currency) }} sur {{ fmtMoney(g.target_amount, g.quote_currency) }}
              · {{ g.base }}
            </p>
          </div>
          <button class="btn-ghost !px-2 !py-1 text-xs text-danger hover:bg-danger-soft" @click="toDelete = g">Supprimer</button>
        </div>
        <div class="mt-4">
          <div class="h-3 w-full overflow-hidden rounded-full bg-paper-2">
            <div class="h-full rounded-full bg-brand transition-all duration-500"
                 :style="{ width: g.progress_pct + '%' }"></div>
          </div>
          <div class="mt-1.5 flex justify-between text-xs">
            <span class="font-medium text-brand">{{ g.progress_pct }}%</span>
            <span class="text-muted" v-if="g.progress_pct >= 100">🎉 Objectif atteint !</span>
            <span class="text-muted" v-else>Plus que {{ fmtMoney(Math.max(g.target_amount - g.current_value, 0), g.quote_currency) }}</span>
          </div>
        </div>
      </div>
    </div>

    <ConfirmModal
      :open="!!toDelete"
      danger
      title="Supprimer cet objectif ?"
      :message="toDelete ? `« ${toDelete.title || ('Objectif ' + toDelete.base)} » sera supprimé. Cela n'affecte ni tes plans ni tes achats.` : ''"
      confirm-label="Supprimer"
      :busy="deleting"
      @update:open="(v) => { if (!v) toDelete = null; }"
      @confirm="confirmDelete"
    />
  </div>
</template>
