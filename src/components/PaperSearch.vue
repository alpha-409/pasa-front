<template>
  <div class="paper-search">
    <div class="search-input">
      <input 
        v-model="userQuery" 
        @keyup.enter="startSearch"
        placeholder="Enter your search query"
        type="text"
      />
      <button @click="startSearch" :disabled="isLoading">Search</button>
    </div>

    <div v-if="isLoading" class="loading-section">
      <div class="progress-container">
        <div class="progress-bar" :style="{ width: progressPercentage + '%' }"></div>
      </div>
      <div class="progress-text">
        Loading papers... {{ progressPercentage }}%
      </div>
    </div>

    <div v-if="error" class="error">
      {{ error }}
    </div>

    <div v-if="papers.length > 0" class="content-grid">
      <div class="papers-section">
        <div v-for="(paper, index) in papers" :key="index" class="paper">
          <h3>{{ paper.title }}</h3>
          <p><strong>Authors:</strong> {{ paper.authors.join(', ') }}</p>
          <p><strong>Published:</strong> {{ formatDate(paper.publish_time) }}</p>
          <p class="abstract">{{ paper.abstract }}</p>
          <p><strong>Score:</strong> {{ paper.score.toFixed(2) }}</p>
          <a :href="getPaperLink(paper)" target="_blank" rel="noopener">View Paper</a>
        </div>
      </div>
      <div class="stats-section">
        <PaperStats :papers="papers" :showIndividualClouds="false" />
        <div v-if="papers.length > 0" class="json-section">
          <h3>Combined JSON Results</h3>
          <div class="json-container">
            <pre>{{ formattedJson }}</pre>
            <button class="copy-button" @click="copyJson" :class="{ copied: jsonCopied }">
              {{ jsonCopied ? 'Copied!' : 'Copy JSON' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import PaperStats from './PaperStats.vue';

export default {
  name: 'PaperSearch',
  components: {
    PaperStats
  },
  data() {
    return {
      userQuery: '',
      sessionId: '',
      papers: [],
      isLoading: false,
      error: null,
      pollingInterval: null,
      totalPapers: 0,
      currentProgress: 0,
      pollingMode: 'fast', // 'fast' for first 50, 'slow' for remainder
      jsonCopied: false
    }
  },
  computed: {
    progressPercentage() {
      if (!this.totalPapers) return 0;
      return Math.min(Math.round((this.currentProgress / this.totalPapers) * 100), 100);
    },
    formattedJson() {
      if (!this.papers.length) return '';
      // Combine all json_result fields into one object
      const allResults = {};
      this.papers.forEach((paper) => {
        try {
          const result = JSON.parse(paper.json_result);
          if (typeof result === 'object' && result !== null) {
            Object.entries(result).forEach(([key, value]) => {
              // Keep the highest scoring result if the same key appears multiple times
              if (!allResults[key] || (value.score && allResults[key].score && value.score > allResults[key].score)) {
                allResults[key] = value;
              }
            });
          }
        } catch (err) {
          console.error('Failed to parse json_result:', err);
        }
      });
      return JSON.stringify(allResults, null, 2);
    }
  },
  methods: {
    async copyJson() {
      try {
        await navigator.clipboard.writeText(this.formattedJson);
        this.jsonCopied = true;
        setTimeout(() => {
          this.jsonCopied = false;
        }, 2000);
      } catch (err) {
        console.error('Failed to copy:', err);
      }
    },
    async startSearch() {
      if (!this.userQuery.trim()) {
        this.error = 'Please enter a search query';
        return;
      }

      this.isLoading = true;
      this.error = null;
      this.papers = [];
      this.currentProgress = 0;
      this.totalPapers = 0;
      this.pollingMode = 'fast';
      this.sessionId = Date.now().toString();

      try {
        // Initial search request
        await axios.post('/paper-agent/api/v1/single_paper_agent', {
          user_query: this.userQuery,
          session_id: this.sessionId
        });

        // Start polling for results
        this.startPolling();
      } catch (err) {
        this.error = 'Failed to start search. Please try again.';
        this.isLoading = false;
      }
    },
    startPolling() {
      // Clear any existing polling interval
      if (this.pollingInterval) {
        clearInterval(this.pollingInterval);
      }

      // Start new polling interval
      this.pollingInterval = setInterval(async () => {
        try {
          const response = await axios.post('/paper-agent/api/v1/single_get_result', {
            session_id: this.sessionId
          });

          if (response.data && response.data.papers) {
            const papersObj = JSON.parse(response.data.papers);
            const newPapers = Object.values(papersObj);
            
            // Update total papers count if it's the first time
            if (!this.totalPapers && newPapers.length > 0) {
              this.totalPapers = newPapers.length;
            }

            // Sort papers by score in descending order
            this.papers = newPapers.sort((a, b) => b.score - a.score);
            
            // Update progress
            this.currentProgress = this.papers.length;

            // Switch polling speed based on progress
            if (this.pollingMode === 'fast' && this.currentProgress >= 50) {
              this.pollingMode = 'slow';
              clearInterval(this.pollingInterval);
              this.pollingInterval = setInterval(async () => this.startPolling(), 4000); // Slower polling for remaining papers
            }
          }

          // Check if search is complete
          if (response.data.finish) {
            this.isLoading = false;
            clearInterval(this.pollingInterval);
          }
        } catch (err) {
          this.error = 'Error fetching results. Please try again.';
          this.isLoading = false;
          clearInterval(this.pollingInterval);
        }
      }, this.pollingMode === 'fast' ? 2000 : 4000);
    },
    formatDate(dateStr) {
      if (!dateStr) return 'N/A';
      // Format YYYYMMDD to YYYY-MM-DD
      return `${dateStr.slice(0, 4)}-${dateStr.slice(4, 6)}-${dateStr.slice(6, 8)}`;
    },
    getPaperLink(paper) {
      try {
        const jsonResult = JSON.parse(paper.json_result);
        return jsonResult.link || '#';
      } catch (err) {
        return '#';
      }
    }
  },
  beforeUnmount() {
    // Clean up polling interval when component is destroyed
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
    }
  }
}
</script>

<style scoped>
.paper-search {
  margin: 0 auto;
  padding: 20px;
  max-width: 1600px;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 20px;
  margin-top: 20px;
  height: calc(100vh - 150px);
}

.papers-section {
  overflow-y: auto;
  padding-right: 20px;
}

.stats-section {
  overflow-y: auto;
  padding-left: 20px;
  border-left: 1px solid #eee;
}

.search-input {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  max-width: 800px;
  margin-left: auto;
  margin-right: auto;
}

input {
  flex: 1;
  padding: 10px;
  font-size: 16px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

button {
  padding: 10px 20px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.loading-section {
  text-align: center;
  margin: 20px auto;
  max-width: 600px;
}

.progress-container {
  width: 100%;
  height: 6px;
  background-color: #f0f0f0;
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 10px;
}

.progress-bar {
  height: 100%;
  background-color: #4CAF50;
  transition: width 0.3s ease;
}

.progress-text {
  color: #666;
  font-size: 14px;
}

.error {
  color: #ff0000;
  margin: 10px 0;
  text-align: center;
}

.paper {
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 15px;
  margin-bottom: 20px;
  background: white;
}

.paper h3 {
  margin-top: 0;
  color: #333;
}

.abstract {
  color: #666;
  margin: 10px 0;
  line-height: 1.5;
}

a {
  color: #2196F3;
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}

.json-section {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.json-container {
  position: relative;
  margin-top: 10px;
  background: #f8f8f8;
  border-radius: 4px;
  border: 1px solid #eee;
}

pre {
  padding: 15px;
  margin: 0;
  overflow-x: auto;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.4;
  max-height: 400px;
  overflow-y: auto;
}

.copy-button {
  position: absolute;
  top: 10px;
  right: 10px;
  padding: 6px 12px;
  background-color: #fff;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.copy-button:hover {
  background-color: #f0f0f0;
}

.copy-button.copied {
  background-color: #4CAF50;
  color: white;
  border-color: #4CAF50;
}
</style>
