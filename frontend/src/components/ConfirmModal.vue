<script setup>
import { watch } from "vue";

const props = defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, required: true },
  message: { type: String, default: "" },
  confirmLabel: { type: String, default: "Confirmer" },
  cancelLabel: { type: String, default: "Annuler" },
  danger: { type: Boolean, default: false },
  busy: { type: Boolean, default: false },
});
const emit = defineEmits(["update:open", "confirm"]);

function close() {
  if (!props.busy) emit("update:open", false);
}
function confirm() {
  emit("confirm");
}

watch(
  () => props.open,
  (v) => { document.body.style.overflow = v ? "hidden" : ""; }
);
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-ink/40 backdrop-blur-sm" @click="close"></div>

        <div class="relative w-full max-w-sm rounded-[var(--radius-xl2)] border border-line bg-surface p-6 shadow-xl"
             role="dialog" aria-modal="true">
          <div v-if="danger" class="mb-4 grid h-11 w-11 place-items-center rounded-full bg-danger-soft text-xl">⏸</div>
          <h3 class="h-display text-xl font-semibold">{{ title }}</h3>
          <p v-if="message" class="mt-2 text-sm text-muted">{{ message }}</p>

          <div class="mt-6 flex gap-3">
            <button class="btn-ghost flex-1" :disabled="busy" @click="close">{{ cancelLabel }}</button>
            <button
              class="flex-1"
              :class="danger ? 'btn-danger' : 'btn-primary'"
              :disabled="busy"
              @click="confirm"
            >{{ busy ? "…" : confirmLabel }}</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.15s ease; }  
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
