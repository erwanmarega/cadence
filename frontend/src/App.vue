<script setup>
import { computed } from "vue";
import { useRoute } from "vue-router";
import { useAuthStore } from "./stores/auth";
import { useIdleTimeout } from "./lib/idleTimeout";
import Navbar from "./components/Navbar.vue";

const route = useRoute();
const auth = useAuthStore();

useIdleTimeout();


const showNav = computed(
  () => auth.isAuthenticated && auth.onboarded && !route.meta.public
);
</script>

<template>
  <div class="min-h-screen bg-paper text-ink">
    <Navbar v-if="showNav" />
    <main>
      <RouterView />
    </main>
  </div>
</template>
