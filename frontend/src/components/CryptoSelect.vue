<script setup>
import { ref, computed, watch } from "vue";

const props = defineProps({
  modelValue: { type: String, default: "" },
  options: { type: Array, default: () => [] },
  placeholder: { type: String, default: "Rechercher une crypto…" },
});
const emit = defineEmits(["update:modelValue"]);

const query = ref(props.modelValue);
const open = ref(false);

watch(() => props.modelValue, (v) => { query.value = v; });

const filtered = computed(() => {
  const q = query.value.trim().toUpperCase();
  if (!q) return props.options;
  return props.options.filter((o) => o.toUpperCase().includes(q));
});

function onInput(e) {
  query.value = e.target.value.toUpperCase();
  open.value = true;
}

function select(o) {
  query.value = o;
  emit("update:modelValue", o);
  open.value = false;
}

function onBlur() {
  setTimeout(() => {
    open.value = false;
    if (!props.options.includes(query.value)) query.value = props.modelValue;
  }, 120);
}
</script>

<template>
  <div class="relative" @focusout="onBlur">
    <input
      :value="query"
      class="field uppercase"
      :placeholder="placeholder"
      autocomplete="off"
      @focus="open = true"
      @input="onInput"
    />
    <ul
      v-if="open && filtered.length"
      class="absolute z-20 mt-1 max-h-56 w-full overflow-auto rounded-xl border border-line bg-surface py-1 shadow-lg"
    >
      <li
        v-for="o in filtered"
        :key="o"
        class="cursor-pointer px-3 py-1.5 text-sm hover:bg-brand-soft/60"
        :class="o === modelValue ? 'font-medium text-brand' : ''"
        @mousedown.prevent="select(o)"
      >
        {{ o }}
      </li>
    </ul>
    <p v-else-if="open && query" class="absolute z-20 mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-sm text-muted shadow-lg">
      Aucune crypto trouvée.
    </p>
  </div>
</template>
