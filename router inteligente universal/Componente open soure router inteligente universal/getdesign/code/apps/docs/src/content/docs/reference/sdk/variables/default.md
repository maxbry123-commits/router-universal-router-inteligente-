---
editUrl: false
next: false
prev: false
title: "default"
---

> **default**: `object`

Defined in: [packages/sdk/src/index.ts:287](https://github.com/MohtashamMurshid/getdesign/blob/9a29e986e32c10258a13bc0b87db6f8c31a09f1d/packages/sdk/src/index.ts#L287)

## Type Declaration

### getDesign

> **getDesign**: (`url`, `options`) => `Promise`\<[`GetDesignResult`](/reference/sdk/type-aliases/getdesignresult/)\>

#### Parameters

##### url

`string`

##### options?

[`GetDesignOptions`](/reference/sdk/type-aliases/getdesignoptions/) = `{}`

#### Returns

`Promise`\<[`GetDesignResult`](/reference/sdk/type-aliases/getdesignresult/)\>

### streamDesign

> **streamDesign**: (`url`, `options`) => `AsyncGenerator`\<[`DesignStreamEvent`](/reference/sdk/type-aliases/designstreamevent/), `void`, `void`\>

#### Parameters

##### url

`string`

##### options?

[`GetDesignOptions`](/reference/sdk/type-aliases/getdesignoptions/) = `{}`

#### Returns

`AsyncGenerator`\<[`DesignStreamEvent`](/reference/sdk/type-aliases/designstreamevent/), `void`, `void`\>

### version

> **version**: `string`
