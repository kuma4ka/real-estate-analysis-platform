import { defineConfig } from 'cypress';

export default defineConfig({
  e2e: {
    baseUrl: 'http://localhost:5173',
    video: false, // Saves time in CI
    screenshotOnRunFailure: true,
    supportFile: false, // Disabling support file until needed to simplify setup
    setupNodeEvents(on, config) {
      // implement node event listeners here
    },
  },
});
