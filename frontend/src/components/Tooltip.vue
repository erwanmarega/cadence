<script setup>
import { useAuthStore } from "../stores/auth";
const auth = useAuthStore();
defineProps({ text: { type: String, required: true } });
</script>

<template>
  <span v-if="auth.isBeginner" class="group relative inline-flex align-middle">
    <span
      class="ml-1 grid h-4 w-4 place-items-center rounded-full bg-brand-soft
             text-[10px] font-semibold text-brand-ink cursor-help"
    >?</span>
    <span
      class="pointer-events-none absolute bottom-full left-1/2 z-20 mb-2
             w-max max-w-[240px] -translate-x-1/2 rounded-lg border border-line
             bg-ink px-3 py-2 text-xs leading-snug text-white opacity-0 shadow-lg
             transition-opacity duration-150 group-hover:opacity-100"
    >{{ text }}</span>
  </span>
</template>
