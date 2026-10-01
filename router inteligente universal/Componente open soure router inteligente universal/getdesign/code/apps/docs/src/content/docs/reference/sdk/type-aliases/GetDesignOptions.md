---
editUrl: false
next: false
prev: false
title: "GetDesignOptions"
---

> **GetDesignOptions** = `object`

Defined in: [packages/sdk/src/index.ts:23](https://github.com/MohtashamMurshid/getdesign/blob/9a29e986e32c10258a13bc0b87db6f8c31a09f1d/packages/sdk/src/index.ts#L23)

## Properties

### credentials?

> `optional` **credentials?**: [`GetDesignCredentials`](/reference/sdk/type-aliases/getdesigncredentials/)

Defined in: [packages/sdk/src/index.ts:27](https://github.com/MohtashamMurshid/getdesign/blob/9a29e986e32c10258a13bc0b87db6f8c31a09f1d/packages/sdk/src/index.ts#L27)

Request-scoped credentials for BYOK runs.

***

### installI18nFonts?

> `optional` **installI18nFonts?**: `boolean`

Defined in: [packages/sdk/src/index.ts:31](https://github.com/MohtashamMurshid/getdesign/blob/9a29e986e32c10258a13bc0b87db6f8c31a09f1d/packages/sdk/src/index.ts#L31)

Force or skip i18n font install. Auto-detected from URL TLD when omitted.

***

### measurementMode?

> `optional` **measurementMode?**: `"cdp"` \| `"visual"` \| `"auto"`

Defined in: [packages/sdk/src/index.ts:33](https://github.com/MohtashamMurshid/getdesign/blob/9a29e986e32c10258a13bc0b87db6f8c31a09f1d/packages/sdk/src/index.ts#L33)

Override measurement strategy. `auto` tries CDP first, then visual-stability.

***

### runDesign?

> `optional` **runDesign?**: (`url`, `options?`) => `Promise`\<`RunDesignResult`\>

Defined in: [packages/sdk/src/index.ts:38](https://github.com/MohtashamMurshid/getdesign/blob/9a29e986e32c10258a13bc0b87db6f8c31a09f1d/packages/sdk/src/index.ts#L38)

Internal/testing seam. Defaults to the real local agent pipeline.
Most callers should not pass this.

#### Parameters

##### url

`string`

##### options?

`RunDesignOptions`

#### Returns

`Promise`\<`RunDesignResult`\>

***

### siteName?

> `optional` **siteName?**: `string`

Defined in: [packages/sdk/src/index.ts:25](https://github.com/MohtashamMurshid/getdesign/blob/9a29e986e32c10258a13bc0b87db6f8c31a09f1d/packages/sdk/src/index.ts#L25)

Override the detected site name.

***

### visualRequirement?

> `optional` **visualRequirement?**: [`VisualRequirement`](/reference/sdk/type-aliases/visualrequirement/)

Defined in: [packages/sdk/src/index.ts:29](https://github.com/MohtashamMurshid/getdesign/blob/9a29e986e32c10258a13bc0b87db6f8c31a09f1d/packages/sdk/src/index.ts#L29)

Explicitly select text-only output; the default requires screenshots.
