import { test as base, expect } from '@playwright/test';
// Forward through Chromium itself so multipart file bodies remain intact.
// The same API runs on a second loopback address with temporary storage.
export const test = base.extend({
  page: async ({ page }, providePage) => {
    await page.context().grantPermissions(['local-network-access'], { origin: 'http://localhost:3003' });
    await page.route(/^http:\/\/(localhost|127\.0\.0\.1):8003\//,async route=>{
      const url=new URL(route.request().url());
      await route.continue({url:`${process.env.MODELFORGE_TEST_API}${url.pathname}${url.search}`});
    });
    await providePage(page);
  },
});
export { expect };
