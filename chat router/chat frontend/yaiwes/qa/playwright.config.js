const { defineConfig, devices } = require('@playwright/test');
module.exports = defineConfig({
 testDir:'./tests', timeout:30000, reporter:[['list'],['html',{outputFolder:'playwright-report',open:'never'}]],
 use:{trace:'retain-on-failure',screenshot:'only-on-failure'},
 projects:[
  {name:'desktop-chromium',use:{...devices['Desktop Chrome']}},
  {name:'mobile-chromium',use:{...devices['Pixel 7']}}
 ]
});
