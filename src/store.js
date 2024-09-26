import { createStore } from 'vuex';

const store = createStore({
  state() {
    return {
      person:'',
      authority: 0,
      StructTree: null,
      selectedChannels: [],
      sampling: 0.3,
      smoothness: 0,
      anomalies: {} // { [channelName]: [ { anomaly data } ] }
    }
  },
  getters: {
    getStructTree(state) {
      return state.StructTree;
    },
    getSelectedChannels(state) {
      return state.selectedChannels;
    },
    getSampling(state) {
      return state.sampling;
    },
    getSmoothness(state) {
      return state.smoothness;
    },
    getAnomaliesByChannel: (state) => (channelName) => {
      return state.anomalies[channelName] || [];
    }
  },
  mutations: {
    setStructTree(state, data) {
      state.StructTree = data;
    },
    updateSelectedChannels(state, channels) {
      state.selectedChannels = channels;
    },
    setSampling(state, value) {
      state.sampling = value;
    },
    setSmoothness(state, value) {
      state.smoothness = value;
    },
    addAnomaly(state, { channelName, anomaly }) {
      if (!state.anomalies[channelName]) {
        state.anomalies[channelName] = [];
      }
      state.anomalies[channelName].push(anomaly);
    },
    updateAnomaly(state, { channelName, anomalyIndex, anomaly }) {
      if (state.anomalies[channelName] && state.anomalies[channelName][anomalyIndex]) {
        state.anomalies[channelName][anomalyIndex] = anomaly;
      }
    },
    deleteAnomaly(state, { channelName, anomalyIndex }) {
      if (state.anomalies[channelName]) {
        state.anomalies[channelName].splice(anomalyIndex, 1);
      }
    }
  },
  actions: {
    async fetchStructTree({ commit, state }) {
      if (!state.StructTree) {
        try {
          const response = await fetch('/Data/StructTree.json');
          const jsonData = await response.json();
          commit('setStructTree', jsonData);
        } catch (error) {
          console.error('Failed to fetch data:', error);
        }
      }
    },
    updateSampling({ commit }, value) {
      commit('setSampling', value);
    },
    updateSmoothness({ commit }, value) {
      commit('setSmoothness', value);
    },
    addAnomaly({ commit }, payload) {
      commit('addAnomaly', payload);
    },
    updateAnomaly({ commit }, payload) {
      commit('updateAnomaly', payload);
    },
    deleteAnomaly({ commit }, payload) {
      commit('deleteAnomaly', payload);
    }
  }
});

export default store;
