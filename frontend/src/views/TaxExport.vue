<script setup>
import { ref, onMounted } from "vue";
import { api } from "../lib/api";

const loading = ref(true);
const downloading = ref(false);
const error = ref("");
const data = ref(null);
const year = ref(null);

async function load(y) {
  loading.value = true;
  error.value = "";
  try {
    data.value = await api.taxSummary(y);
    year.value = data.value.year;
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

async function download() {
  if (!year.value) return;
  downloading.value = true;
  error.value = "";
  try {
    await api.taxExport(year.value);
  } catch (e) {
    error.value = e.message;
  } finally {
    downloading.value = false;
  }
}

function fmt(n) {
  if (n == null) return "—";
  return new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 2 }).format(n);
}

onMounted(() => load());
</script>

<template>
  <div class="mx-auto max-w-2xl px-5 py-10">
    <h1 class="h-display text-3xl font-semibold">Relevé fiscal</h1>
    <p class="mt-1 text-muted">
      Un récapitulatif de tes achats et de ton prix de revient, prêt à transmettre à ton comptable.
    </p>

    <div class="mt-5 rounded-xl border border-line bg-brand-soft/30 p-4 text-sm">
      <p class="font-medium text-brand-ink">Information, pas conseil fiscal.</p>
      <p class="mt-1 text-muted">
        Cadence n'effectue que des achats : aucune vente n'est déclenchée, donc aucune plus-value
        imposable n'est générée par l'app. En France, la plus-value n'est imposable qu'à la revente.
        Ce relevé liste tes acquisitions à conserver — il ne calcule pas la plus-value (le calcul
        officiel exige la valeur de tout ton portefeuille crypto au moment de la vente, hors Cadence
        compris).
      </p>
    </div>

    <div v-if="loading" class="mt-8 text-muted">Chargement…</div>

    <div v-else-if="!data?.years?.length" class="card mt-8 text-center">
      <p class="text-muted">Aucun achat exécuté pour l'instant. Ton relevé apparaîtra ici après tes premiers achats DCA.</p>
    </div>

    <template v-else>
      <div class="mt-6 flex items-center gap-3">
        <label class="field-label mb-0">Année</label>
        <select :value="year" class="field max-w-32" @change="load(Number($event.target.value))">
          <option v-for="y in data.years" :key="y" :value="y">{{ y }}</option>
        </select>
      </div>

      <div class="card mt-4">
        <div class="flex items-baseline justify-between">
          <div>
            <p class="field-label">Total investi en {{ year }}</p>
            <p class="h-display text-3xl font-semibold">{{ fmt(data.total_invested) }}</p>
          </div>
          <p class="text-sm text-muted">{{ data.buys }} achat{{ data.buys > 1 ? "s" : "" }}</p>
        </div>

        <div v-if="data.assets.length" class="mt-5 overflow-hidden rounded-xl border border-line">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-line bg-paper-2/50 text-left text-muted">
                <th class="px-4 py-2 font-medium">Actif</th>
                <th class="px-4 py-2 font-medium">Achats</th>
                <th class="px-4 py-2 font-medium">Investi</th>
                <th class="px-4 py-2 font-medium">Prix de revient moyen</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="a in data.assets" :key="a.base" class="border-b border-line last:border-0">
                <td class="px-4 py-2 font-medium">{{ a.base }}</td>
                <td class="px-4 py-2 text-muted">{{ a.buys }}</td>
                <td class="px-4 py-2">{{ fmt(a.invested) }}</td>
                <td class="px-4 py-2">{{ fmt(a.avg_price) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <button class="btn-primary mt-5 w-full" :disabled="downloading" @click="download">
        {{ downloading ? "Génération…" : `Télécharger le relevé ${year} (CSV)` }}
      </button>
      <p class="mt-2 text-center text-xs text-muted">
        Frais de transaction non inclus. Compatible Excel / comptable.
      </p>
    </template>

    <p v-if="error" class="mt-4 text-sm text-danger">{{ error }}</p>
  </div>
</template>
