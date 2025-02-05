<template>
  <div class="word-cloud" ref="container"></div>
</template>

<script>
import * as d3 from 'd3';
import cloud from 'd3-cloud';

export default {
  name: 'WordCloud',
  props: {
    words: {
      type: Array,
      required: true
    },
    width: {
      type: Number,
      default: 500
    },
    height: {
      type: Number,
      default: 300
    }
  },
  mounted() {
    this.drawWordCloud();
  },
  watch: {
    words: {
      handler() {
        this.drawWordCloud();
      },
      deep: true
    }
  },
  methods: {
    drawWordCloud() {
      if (!this.words.length) return;

      const container = this.$refs.container;
      container.innerHTML = '';

      const layout = cloud()
        .size([this.width, this.height])
        .words(this.words.map(d => ({
          text: d.text,
          size: 10 + Math.sqrt(d.value) * 10
        })))
        .padding(5)
        .rotate(() => 0)
        .fontSize(d => d.size)
        .on('end', words => {
          const svg = d3.select(container)
            .append('svg')
            .attr('width', this.width)
            .attr('height', this.height);

          const g = svg.append('g')
            .attr('transform', `translate(${this.width/2},${this.height/2})`);

          g.selectAll('text')
            .data(words)
            .enter()
            .append('text')
            .style('font-size', d => `${d.size}px`)
            .style('fill', () => `hsl(${Math.random() * 360},70%,50%)`)
            .attr('text-anchor', 'middle')
            .attr('transform', d => `translate(${d.x},${d.y}) rotate(${d.rotate})`)
            .text(d => d.text);
        });

      layout.start();
    }
  }
}
</script>

<style scoped>
.word-cloud {
  width: 100%;
  height: 100%;
  min-height: 300px;
}

svg {
  display: block;
  margin: 0 auto;
}
</style>
