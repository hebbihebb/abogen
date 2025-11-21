import { create } from 'zustand';

// Dynamically determine API URL based on current host
const API_URL = `http://${window.location.hostname}:8000`;

export const useStore = create((set, get) => ({
  // File state
  file: null,
  fileInfo: null,
  text: '',
  selectedChapters: [],

  // TTS configuration
  config: {
    engine: 'kokoro',
    voice: 'af_heart',
    speed: 1.0,
    voiceFormula: null,
    referenceAudio: null,
    referenceText: '',
    generateSubtitles: 'disabled',
    subtitleFormat: 'srt',
    maxSubtitleWords: 10,
    outputFormat: 'wav',
    replaceSingleNewlines: false,
    use_gpu: true,
    separateChapters: false,
    separateChaptersFormat: 'wav',
    silenceBetweenChapters: 1.0,
  },

  // Available options
  engines: [],
  voices: [],
  voiceProfiles: [],

  // Job state
  currentJob: null,
  jobStatus: null,
  progress: 0,
  logs: [],
  ws: null,

  // UI state
  showSettings: false,
  showVoiceMixer: false,
  showQueueManager: false,
  showChapterSelector: false,
  processing: false,

  // Actions
  setFile: (file) => set({ file }),
  setFileInfo: (fileInfo) => set({ fileInfo }),
  setText: (text) => set({ text }),
  setSelectedChapters: (chapters) => set({ selectedChapters: chapters }),

  updateConfig: (config) => set((state) => ({
    config: { ...state.config, ...config }
  })),

  setEngines: (engines) => set({ engines }),
  setVoices: (voices) => set({ voices }),
  setVoiceProfiles: (profiles) => set({ voiceProfiles: profiles }),

  setCurrentJob: (jobId) => set({ currentJob: jobId }),
  setJobStatus: (status) => set({ jobStatus: status }),
  setProgress: (progress) => set({ progress }),
  addLog: (log) => set((state) => ({ logs: [...state.logs, log] })),
  clearLogs: () => set({ logs: [] }),

  toggleSettings: () => set((state) => ({ showSettings: !state.showSettings })),
  toggleVoiceMixer: () => set((state) => ({ showVoiceMixer: !state.showVoiceMixer })),
  toggleQueueManager: () => set((state) => ({ showQueueManager: !state.showQueueManager })),
  toggleChapterSelector: () => set((state) => ({ showChapterSelector: !state.showChapterSelector })),

  setProcessing: (processing) => set({ processing }),

  // API calls
  fetchEngines: async () => {
    try {
      const response = await fetch(`${API_URL}/api/engines`);
      const data = await response.json();
      set({ engines: data.engines });
    } catch (error) {
      console.error('Failed to fetch engines:', error);
    }
  },

  fetchVoices: async (engine) => {
    try {
      const response = await fetch(`${API_URL}/api/voices/${engine}`);
      const data = await response.json();
      set({ voices: data.voices });
    } catch (error) {
      console.error('Failed to fetch voices:', error);
    }
  },

  fetchVoiceProfiles: async () => {
    try {
      const response = await fetch(`${API_URL}/api/voice-profiles`);
      const data = await response.json();
      set({ voiceProfiles: data.profiles });
    } catch (error) {
      console.error('Failed to fetch voice profiles:', error);
    }
  },

  uploadFile: async (file) => {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_URL}/api/upload`, {
        method: 'POST',
        body: formData,
      });

      const fileInfo = await response.json();
      set({ file, fileInfo });

      // Show chapter selector for books
      if (fileInfo.type === 'epub' || fileInfo.type === 'pdf') {
        set({ showChapterSelector: true });
      }

      return fileInfo;
    } catch (error) {
      console.error('Failed to upload file:', error);
      throw error;
    }
  },

  uploadReferenceAudio: async (file) => {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_URL}/api/upload`, {
        method: 'POST',
        body: formData,
      });

      const fileInfo = await response.json();

      // Update config with the uploaded file path
      set((state) => ({
        config: { ...state.config, referenceAudio: fileInfo.path }
      }));

      return fileInfo;
    } catch (error) {
      console.error('Failed to upload reference audio:', error);
      throw error;
    }
  },

  loadDemo: async () => {
    try {
      const response = await fetch(`${API_URL}/api/demo/load`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error('Failed to load demo files');
      }

      const data = await response.json();

      set((state) => ({
        file: { name: data.file_info.filename }, // Mock file object
        fileInfo: data.file_info,
        showChapterSelector: true,
        config: {
          ...state.config,
          engine: 'f5_tts',
          referenceAudio: data.reference_audio
        }
      }));

      return data;
    } catch (error) {
      console.error('Failed to load demo:', error);
      throw error;
    }
  },

  startConversion: async () => {
    const { fileInfo, config, selectedChapters } = get();

    if (!fileInfo) {
      throw new Error('No file selected');
    }

    try {
      set({ processing: true, logs: [], progress: 0 });

      const formData = new FormData();
      formData.append('file_path', fileInfo.path);

      const configData = {
        ...config,
        selected_chapters: selectedChapters.length > 0 ? selectedChapters : null,
      };

      formData.append('config_json', JSON.stringify(configData));

      const response = await fetch(`${API_URL}/api/convert`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      set({ currentJob: data.job_id });

      // Connect to WebSocket for real-time updates
      get().connectWebSocket(data.job_id);

      return data.job_id;
    } catch (error) {
      set({ processing: false });
      console.error('Failed to start conversion:', error);
      throw error;
    }
  },

  connectWebSocket: (jobId) => {
    // Construct WebSocket URL from API_URL (http://host:port -> ws://host:port)
    const wsUrl = API_URL.replace('http://', 'ws://').replace('https://', 'wss://');
    const ws = new WebSocket(`${wsUrl}/ws/${jobId}`);

    ws.onopen = () => {
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      if (message.type === 'log') {
        get().addLog(message.data);
      } else if (message.type === 'progress') {
        set({ progress: message.data.progress });
      } else if (message.type === 'init') {
        set({ jobStatus: message.data });
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      set({ ws: null, processing: false });
    };

    set({ ws });
  },

  downloadOutput: async (jobId) => {
    try {
      const response = await fetch(`${API_URL}/api/jobs/${jobId}/download`);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `output.${get().config.outputFormat}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Failed to download output:', error);
      throw error;
    }
  },

  cancelJob: () => {
    const { ws } = get();
    if (ws) {
      ws.close();
    }
    set({ processing: false, currentJob: null, ws: null });
  },
}));

export default useStore;
