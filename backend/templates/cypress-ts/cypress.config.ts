import { defineConfig } from 'cypress';

export default defineConfig({
  e2e: {
    baseUrl: 'http://localhost:3000',
    video: true,
    screenshotOnRunFailure: true,
    reporter: 'json',
    reporterOptions: {
      output: 'results.json'
    }
  }
});