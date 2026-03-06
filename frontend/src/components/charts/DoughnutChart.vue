<script>
import { Doughnut } from 'vue-chartjs';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend
} from 'chart.js';

ChartJS.register(ArcElement, Tooltip, Legend);

export default {
  name: 'DoughnutChart',
  components: { Doughnut },
  props: {
    chartData: {
      type: Object,
      required: true
    },
    options: {
      type: Object,
      default: () => ({})
    }
  }
};
</script>

<template>
  <Doughnut :data="chartData" :options="options" />
</template>
