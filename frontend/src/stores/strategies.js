import { defineStore } from "pinia";
import { ref } from "vue";
import { api } from "../lib/api";

export const useStrategiesStore = defineStore("strategies", () => {
  const items = ref([]);
  const loading = ref(false);

  async function load() {
    loading.value = true;
    try {
      items.value = await api.listStrategies();
    } finally {
      loading.value = false;
    }
  }

  async function create(payload) {
    const created = await api.createStrategy(payload);
    items.value.unshift(created);
    return created;
  }

  async function update(id, payload) {
    const updated = await api.updateStrategy(id, payload);
    const i = items.value.findIndex((s) => s.id === id);
    if (i !== -1) items.value[i] = updated;
    return updated;
  }

  async function toggle(strategy) {

    const next = strategy.status === "active" ? "paused" : "active";
    return update(strategy.id, { status: next });
  }

  async function remove(id) {
    await api.deleteStrategy(id);
    items.value = items.value.filter((s) => s.id !== id);
  }

  return { items, loading, load, create, update, toggle, remove };
});
