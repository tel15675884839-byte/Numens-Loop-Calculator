<template>
  <div class="print-watermark-layer" aria-hidden="true">
    <img class="print-watermark" :src="watermarkLogoSrc" alt="" />
  </div>
</template>

<script setup lang="ts">
import watermarkLogoSrc from "../../../../assets/logo-V-3-2.png";
</script>
