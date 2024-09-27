import { createStore } from 'vuex';

const store = createStore({
  state() {
    return {
      person:'玛卡巴卡',
      authority: 0,
      StructTree: null,
      selectedChannels: [],
      sampling: 0.1,
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
    updateAnomaly(state, { channelName, anomaly }) {
      if (state.anomalies[channelName]) {
        const index = state.anomalies[channelName].findIndex(a => a.id === anomaly.id);
        if (index !== -1) {
          state.anomalies[channelName][index] = anomaly;
        }
      }
      console.log(state.anomalies)
    },
    deleteAnomaly(state, { channelName, anomalyId }) {
      if (state.anomalies[channelName]) {
        state.anomalies[channelName] = state.anomalies[channelName].filter(
          (a) => a.id !== anomalyId
        );
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
