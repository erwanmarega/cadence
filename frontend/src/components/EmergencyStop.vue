<script setup>
import { ref, computed } from "vue";
import { useStrategiesStore } from "../stores/strategies";
import ConfirmModal from "./ConfirmModal.vue";

const store = useStrategiesStore();
const busy = ref(false);
const showConfirm = ref(false);

const activeCount = computed(
  () => store.items.filter((s) => s.status === "active").length
);

async function stopAll() {
  busy.value = true;
  try {
    const active = store.items.filter((s) => s.status === "active");
    for (const s of active) {
      await store.update(s.id, { status: "paused" });
    }
    showConfirm.value = false;
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <button
    class="btn border w-32 h-14 border-danger/30 bg-danger-soft text-danger hover:bg-danger hover:text-white"
    :disabled="busy || !activeCount"
    :title="activeCount ? 'Met en pause tous les achats' : 'Aucun bot actif'"
    @click="showConfirm = true"
  >
    <span class=" flex text-base leading-none">⏸</span>
    Tout suspendre<span v-if="activeCount" class="opacity-80"> {{ activeCount }}</span>
  </button>

  <ConfirmModal
    v-model:open="showConfirm"
    danger
    title="Tout suspendre ?"
    :message="`${activeCount} plan${activeCount > 1 ? 's' : ''} actif${activeCount > 1 ? 's' : ''} seront mis en pause. Aucun nouvel achat ne sera effectué jusqu'à réactivation. Tes fonds ne sont pas touchés.`"
    confirm-label="Oui, tout suspendre"
    cancel-label="Annuler"
    :busy="busy"
    @confirm="stopAll"
  />
</template>
