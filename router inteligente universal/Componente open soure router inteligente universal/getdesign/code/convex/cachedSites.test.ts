import { describe, expect, mock, test } from "bun:test";
import { list, get, seed } from "./cachedSites";
import snapshots from "./seedData/cached-sites.json";

type Row = (typeof snapshots)[number] & { _id: string; updatedAt: number };
function database() {
  const rows: Row[] = [];
  const db = {
    query: mock((table: string) => {
      expect(table).toBe("cachedSites");
      let slug: string | undefined;
      const query = {
        withIndex: (name: string, filter: (q: unknown) => unknown) => {
          expect(name).toBe("by_slug");
          filter({ eq: (field: string, value: string) => { expect(field).toBe("slug"); slug = value; } });
          return query;
        },
        unique: async () => rows.find(row => row.slug === slug) ?? null,
        collect: async () => [...rows],
      };
      return query;
    }),
    insert: mock(async (table: string, value: Omit<Row, "_id">) => {
      expect(table).toBe("cachedSites");
      const _id = String(rows.length + 1); rows.push({ ...value, _id }); return _id;
    }),
    patch: mock(async (id: string, value: Partial<Row>) => { Object.assign(rows.find(row => row._id === id)!, value); }),
  };
  return { db, rows };
}
function invoke(operation: unknown, ctx: unknown, args = {}) {
  return (operation as { _handler: (ctx: unknown, args: unknown) => Promise<unknown> })._handler(ctx, args);
}
function auth(subject: string | null) {
  return { getUserIdentity: async () => subject ? { subject } : null };
}

describe("Shared database catalog", () => {
  test("seeds all twelve sites once and makes repeated deployment a no-op", async () => {
    const { db, rows } = database();
    expect(await invoke(seed, { db })).toEqual({ inserted: 12, updated: 0, unchanged: 0, total: 12 });
    const saved = JSON.stringify(rows);
    expect(await invoke(seed, { db })).toEqual({ inserted: 0, updated: 0, unchanged: 12, total: 12 });
    expect(JSON.stringify(rows)).toBe(saved);
    expect(db.insert).toHaveBeenCalledTimes(12);
    expect(db.patch).not.toHaveBeenCalled();
  });
  test("two unrelated accounts receive identical sites and downloads without provider credentials", async () => {
    const { db } = database(); await invoke(seed, { db });
    const first = { db, auth: auth("first-user") };
    const second = { db, auth: auth("second-user") };
    const sites = await invoke(list, first) as Row[];
    expect(sites).toHaveLength(12);
    expect(await invoke(list, second)).toEqual(sites);
    for (const site of sites) {
      expect(site).not.toHaveProperty("markdown");
      expect(site).not.toHaveProperty("userId");
      const doc = await invoke(get, first, { slug: site.slug });
      expect(doc).toEqual(await invoke(get, second, { slug: site.slug }));
      expect(doc).toMatchObject({ markdown: snapshots.find(snapshot => snapshot.slug === site.slug)!.markdown });
    }
  });
  test("anonymous reads are rejected before accessing any data", async () => {
    const { db } = database();
    await expect(invoke(list, { db, auth: auth(null) })).rejects.toThrow("Unauthorized");
    await expect(invoke(get, { db, auth: auth(null) }, { slug: "linear" })).rejects.toThrow("Unauthorized");
    expect(db.query).not.toHaveBeenCalled();
  });
  test("seed is internal; users have no public catalog mutation", () => {
    expect(seed).toMatchObject({ isInternal: true });
    expect(list).toMatchObject({ isPublic: true });
    expect(get).toMatchObject({ isPublic: true });
  });
  test("updates older snapshots, preserves newer records, and never deletes extra sites", async () => {
    const { db, rows } = database(); await invoke(seed, { db });
    rows[0]!.capturedAt = "2000-01-01T00:00:00.000Z";
    rows[0]!.markdown = "old document";
    rows[1]!.capturedAt = "2099-01-01T00:00:00.000Z";
    rows[1]!.markdown = "newer document";
    rows.push({ ...rows[2]!, _id: "extra", slug: "extra-site" });
    expect(await invoke(seed, { db })).toEqual({ inserted: 0, updated: 1, unchanged: 11, total: 12 });
    expect(rows[0]!.markdown).toBe(snapshots[0]!.markdown);
    expect(rows[1]!.markdown).toBe("newer document");
    expect(rows).toHaveLength(13);
  });
  test("unknown sites return null rather than another user's private run", async () => {
    const { db } = database();
    expect(await invoke(get, { db, auth: auth("user") }, { slug: "private-run-id" })).toBeNull();
  });
});

test("deployment backfills image metadata on legacy text-and-palette seed rows", async () => {
  const { db, rows } = database();
  await invoke(seed, { db });
  delete (rows[0] as Partial<Row>).images;
  expect(await invoke(seed, { db })).toMatchObject({ updated: 1 });
  expect(rows[0]!.images).toEqual(snapshots[0]!.images);
});


test("legacy rows are withheld until the seed repairs the complete snapshot, even with a newer date", async () => {
  const { db, rows } = database();
  await invoke(seed, { db });
  const damaged = rows[0]!;
  delete (damaged as Partial<Row>).images;
  damaged.capturedAt = "2099-01-01T00:00:00.000Z";
  damaged.markdown = "Legacy document without image references";
  const ctx = { db, auth: auth("user") };
  expect(await invoke(list, ctx)).toHaveLength(11);
  expect(await invoke(get, ctx, { slug: damaged.slug })).toBeNull();
  expect(await invoke(seed, { db })).toMatchObject({ updated: 1 });
  expect(damaged).toMatchObject(snapshots[0]!);
  expect(await invoke(list, ctx)).toHaveLength(12);
  expect(await invoke(get, ctx, { slug: damaged.slug })).toMatchObject(snapshots[0]!);
});
