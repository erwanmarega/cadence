<script setup>
defineProps({
  size: { type: String, default: "1.25rem" },
});
</script>

<template>
  <span
    class="inline-block animate-spin rounded-full border-2 border-current border-t-transparent align-[-0.15em]"
    :style="{ width: size, height: size }"
    role="status"
    aria-label="Chargement"
  ></span>
</template>
