/* eslint-disable */
/**
 * Generated `api` utility.
 *
 * THIS CODE IS AUTOMATICALLY GENERATED.
 *
 * To regenerate, run `npx convex dev`.
 * @module
 */

import type * as cachedSites from "../cachedSites.js";
import type * as designRunArtifacts from "../designRunArtifacts.js";
import type * as designRunPolicy from "../designRunPolicy.js";
import type * as designRuns from "../designRuns.js";
import type * as lib_cachedSiteFields from "../lib/cachedSiteFields.js";
import type * as lib_cachedSiteSchema from "../lib/cachedSiteSchema.js";
import type * as lib_designMdPreview from "../lib/designMdPreview.js";
import type * as lib_runPreviews from "../lib/runPreviews.js";
import type * as publicRuns from "../publicRuns.js";
import type * as userCredentials from "../userCredentials.js";
import type * as waitlist from "../waitlist.js";
import type * as workosAuth from "../workosAuth.js";

import type {
  ApiFromModules,
  FilterApi,
  FunctionReference,
} from "convex/server";

declare const fullApi: ApiFromModules<{
  cachedSites: typeof cachedSites;
  designRunArtifacts: typeof designRunArtifacts;
  designRunPolicy: typeof designRunPolicy;
  designRuns: typeof designRuns;
  "lib/cachedSiteFields": typeof lib_cachedSiteFields;
  "lib/cachedSiteSchema": typeof lib_cachedSiteSchema;
  "lib/designMdPreview": typeof lib_designMdPreview;
  "lib/runPreviews": typeof lib_runPreviews;
  publicRuns: typeof publicRuns;
  userCredentials: typeof userCredentials;
  waitlist: typeof waitlist;
  workosAuth: typeof workosAuth;
}>;

/**
 * A utility for referencing Convex functions in your app's public API.
 *
 * Usage:
 * ```js
 * const myFunctionReference = api.myModule.myFunction;
 * ```
 */
export declare const api: FilterApi<
  typeof fullApi,
  FunctionReference<any, "public">
>;

/**
 * A utility for referencing Convex functions in your app's internal API.
 *
 * Usage:
 * ```js
 * const myFunctionReference = internal.myModule.myFunction;
 * ```
 */
export declare const internal: FilterApi<
  typeof fullApi,
  FunctionReference<any, "internal">
>;

export declare const components: {};
