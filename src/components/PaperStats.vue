<template>
  <div class="paper-stats">
    <div class="stats-section">
      <h2>Statistics Summary</h2>
      <p class="stat-item"><strong>Total Papers:</strong> {{ papers.length }}</p>
      
      <!-- Year Distribution -->
      <div class="year-distribution">
        <h3>Publication Years</h3>
        <div class="year-bars">
          <div v-for="(count, year) in yearDistribution" :key="year" class="year-bar">
            <div class="bar" :style="{ height: (count / maxYearCount * 100) + '%' }">
              <span class="count">{{ count }}</span>
            </div>
            <span class="year">{{ year }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Word Cloud -->
    <div class="wordcloud-section">
      <h3>Topic Analysis</h3>
      <div class="wordcloud" v-if="globalWordCloud.length > 0">
        <WordCloud :words="globalWordCloud" :width="500" :height="400" />
      </div>
    </div>
  </div>
</template>

<script>
import WordCloud from './WordCloud.vue';

export default {
  name: 'PaperStats',
  components: {
    WordCloud
  },
  props: {
    papers: {
      type: Array,
      required: true
    }
  },
  data() {
    return {
      stopWords: new Set([
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has', 'he',
        'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the', 'to', 'was', 'were',
        'will', 'with', 'the', 'this', 'we', 'our', 'which', 'paper', 'papers',
        'method', 'methods', 'propose', 'proposed', 'using', 'based', 'show', 'shows'
      ])
    };
  },
  computed: {
    yearDistribution() {
      const distribution = {};
      this.papers.forEach(paper => {
        const year = paper.publish_time.slice(0, 4);
        distribution[year] = (distribution[year] || 0) + 1;
      });
      return Object.fromEntries(
        Object.entries(distribution).sort((a, b) => a[0].localeCompare(b[0]))
      );
    },
    maxYearCount() {
      return Math.max(...Object.values(this.yearDistribution));
    },
    globalWordCloud() {
      const wordCount = {};
      this.papers.forEach(paper => {
        const words = this.extractWords(paper.abstract);
        words.forEach(word => {
          wordCount[word] = (wordCount[word] || 0) + 1;
        });
      });
      return Object.entries(wordCount)
        .map(([word, value]) => ({ text: word, value }))
        .sort((a, b) => b.value - a.value)
        .slice(0, 50);
    }
  },
  methods: {
    extractWords(text) {
      return text
        .toLowerCase()
        .replace(/[^\w\s]/g, '')
        .split(/\s+/)
        .filter(word => 
          word.length > 3 && 
          !this.stopWords.has(word) && 
          !word.match(/^\d+$/)
        );
    }
  }
};
</script>

<style scoped>
.paper-stats {
  padding: 20px;
  background: #fff;
  border-radius: 8px;
}

.stats-section {
  margin-bottom: 30px;
}

.stat-item {
  font-size: 1.1em;
  margin: 10px 0;
}

.year-distribution {
  margin-top: 20px;
}

.year-bars {
  display: flex;
  align-items: flex-end;
  height: 150px;
  gap: 8px;
  padding: 20px 0;
}

.year-bar {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.bar {
  width: 30px;
  background-color: #4CAF50;
  border-radius: 4px 4px 0 0;
  position: relative;
  min-height: 20px;
  transition: height 0.3s ease;
}

.count {
  position: absolute;
  top: -20px;
  width: 100%;
  text-align: center;
  font-size: 12px;
}

.year {
  margin-top: 5px;
  font-size: 12px;
  transform: rotate(-45deg);
}

.wordcloud-section {
  margin-top: 30px;
}

.wordcloud {
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 10px;
  margin: 10px 0;
}

h2, h3 {
  color: #333;
  margin-bottom: 15px;
}

h2 {
  font-size: 1.5em;
}

h3 {
  font-size: 1.2em;
  margin-top: 20px;
}
</style>
